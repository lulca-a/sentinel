import requests
import calendar
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "https://api-redemet.decea.mil.br/produtos/radar/maxcappi"

def get_dias_do_mes(ano, mes):
    agora = datetime.now()
    if agora.year == ano and agora.month == mes:
        return agora.day - 1
    return calendar.monthrange(ano, mes)[1]

def parse_data_datetime(data_str):
    """Retorna datetime a partir do timestamp de API."""
    try:
        return datetime.fromisoformat(data_str)
    except Exception:
        # Formato possível '2026-03-28 19:16:44' e outros
        try:
            return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

def get_radar(url, params, requested_time=None):
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return None

    try:
        data = resp.json()
        radar_list = data.get('data', {}).get('radar', [])
        candidates = []
        for group in radar_list:
            for entry in group:
                if not entry or 'data' not in entry:
                    continue
                dt = parse_data_datetime(entry['data'])
                if dt is None:
                    continue
                candidates.append((dt, entry))

        if not candidates:
            return None

        if requested_time:
            matched = [(abs((dt - requested_time).total_seconds()), dt, entry)
                       for dt, entry in candidates
                       if dt.hour == requested_time.hour]
            if not matched:
                return None
            matched.sort(key=lambda x: x[0])
            return matched[0][2]

        # Não foi fornecida hora pedida, retorna o último disponível
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    except (KeyError, IndexError, ValueError):
        return None

def coletar_dia(dia, ano, mes, area, api_key, max_workers=4):
    """Coleta dados de radar para todas as horas de um dia específico"""
    
    def buscar(hora):
        params = {
            "api_key": api_key,
            "data": f"{ano}{mes:02d}{dia:02d}{hora:02d}",
            "area": area
        }

        try:
            requested = datetime(ano, mes, dia, hora)
            radar = get_radar(API_URL, params, requested_time=requested)
        except Exception as e:
            radar = None
        return {
            "dia": dia,
            "hora": hora,
            "radar": radar if radar and radar.get("path") else None
        }

    resultados = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(buscar, h) for h in range(24)]

        for future in as_completed(futures):
            resultados.append(future.result())

    resultados.sort(key=lambda x: x["hora"])
    return resultados
