from logging import root
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from dotenv import load_dotenv
import os
import threading
import sys
from core.services import get_dias_do_mes, get_radar, coletar_dia, API_URL
from core.config import (
    THEME_BG, THEME_FG, BTN_COLOR, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_RESIZABLE,
    COMBOBOX_WIDTH, BUTTON_PAD, FRAME_PAD, YEARS_RANGE, AREAS, DEFAULT_AREA,
    HOURS_IN_DAY, CELL_WIDTH, CELL_HEIGHT
)
from ui.renderer import desenhar_dia


if getattr(sys, 'frozen', False):
    caminho_base = sys._MEIPASS
else:
    caminho_base = os.path.dirname(os.path.abspath(__file__))

dotenv_path = os.path.join(caminho_base, '.env')

load_dotenv(dotenv_path)
API_KEY = os.getenv("API_KEY")

# --- GERAR REPORTE ---
def gerar_reporte():
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    ano = int(combo_ano.get())
    mes = int(combo_mes.get())
    area = combo_area.get()
    area = area[-3:-1]

    # cabeçalho
    for h in range(HOURS_IN_DAY):
        tk.Label(scrollable_frame, text=f"{h:02d}", width=3).grid(row=0, column=h+1)

    timeline = []  # timeline global dentro da função

    def worker():
        dias = get_dias_do_mes(ano, mes)
        resumo_inoperantes = []

        for dia in range(1, dias + 1):
            dias_inoperantes = {'dia': dia, 'horas': []}
            lista = coletar_dia(dia, ano, mes, area, API_KEY)

            # montar timeline
            for item in lista:
                timeline.append({
                    "dia": dia,
                    "hora": item["hora"],
                    "off": item["radar"] is None
                })

            # UI continua igual
            root.after(0, lambda d=dia, lista=lista: desenhar_dia(scrollable_frame, d, lista))

        # ✅ chamar resumo_continuo quando terminar a thread
        root.after(0, resumo_continuo)

    def resumo_continuo():
        periodos = []
        inicio = None
        anterior = None

        for ponto in timeline:
            if ponto["off"]:
                if inicio is None:
                    inicio = ponto
            else:
                if inicio is not None:
                    periodos.append((inicio, anterior))
                    inicio = None
            anterior = ponto

        if inicio is not None:
            periodos.append((inicio, anterior))

        resumo_final = []
        for ini, fim in periodos:
            if ini["hora"] == 0 and fim["hora"] == 23 and ini["dia"] == fim["dia"]:
                resumo_final.append(f"Dia {ini['dia']:02d}: Sem radar o dia todo")
            else:
                resumo_final.append(
                    f"Fora durante dia {ini['dia']:02d} às {ini['hora']:02d}h "
                    f"até dia {fim['dia']:02d} às {fim['hora']:02d}h"
                )

        resumo_window = tk.Toplevel(root)
        resumo_window.title("Resumo de Períodos Contínuos")
        resumo_window.geometry("400x300")
        resumo_window.configure(bg=THEME_BG)

        tk.Label(
            resumo_window,
            text="Períodos Contínuos de Inoperância",
            bg=THEME_BG,
            fg=THEME_FG,
            font=("Arial", 14)
        ).pack(pady=10)

        texto = tk.Text(
            resumo_window,
            bg=THEME_BG,
            fg=THEME_FG,
            state="normal",   # abrir para inserir
            wrap="word",      # quebra de linha automática
            height=15,        # ajusta altura
            width=50          # ajusta largura
        )
        texto.pack(anchor="w", padx=20, pady=10)

        # inserir conteúdo
        texto.insert("1.0", '\n'.join(resumo_final))

        # bloquear edição, mas permitir seleção
        root.after(0, lambda: texto.config(state="disabled"))
    threading.Thread(target=worker, daemon=True).start()

# --- UI ---
root = tk.Tk()
root.title("Sentinel - Reporte de Radar Meteorológico")
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
root.resizable(WINDOW_RESIZABLE, WINDOW_RESIZABLE)
root.configure(bg=THEME_BG)

frame_top = tk.Frame(root, bg=THEME_BG)
frame_top.pack(pady=FRAME_PAD)

combo_mes = ttk.Combobox(frame_top, values=[f"{i:02d}" for i in range(1, 13)], width=5)
combo_mes.set(f"{datetime.now().month:02d}")
combo_mes.pack(side="left", padx=5)

combo_ano = ttk.Combobox(frame_top, values=[str(y) for y in range(YEARS_RANGE[0], YEARS_RANGE[1])], width=7)
combo_ano.set(str(datetime.now().year))
combo_ano.pack(side="left", padx=5)

combo_area = ttk.Combobox(frame_top, values=AREAS, width=COMBOBOX_WIDTH)
combo_area.set(DEFAULT_AREA)

combo_area.pack(side="left", padx=5)

btn = tk.Button(
    frame_top,
    text="Gerar Reporte",
    command=gerar_reporte,
    bg=BTN_COLOR,
    fg=THEME_FG,
    relief="flat",
    padx=BUTTON_PAD
)
btn.pack(side="left", padx=10)

scrollable_frame = tk.Frame(root, bg=THEME_BG)
scrollable_frame.pack(pady=FRAME_PAD)



root.mainloop()