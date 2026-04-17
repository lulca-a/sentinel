"""Renderização de grid de radar"""
import tkinter as tk
from PIL import Image, ImageTk
from io import BytesIO
import requests
import threading
import sys
import os

# Importar com fallback para path absoluto
try:
    from ..core.config import THEME_BG, RADAR_COLOR, NO_RADAR_COLOR, CELL_WIDTH, CELL_HEIGHT
    from ..ui.widgets import ToolTip
except (ImportError, ValueError):
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.config import THEME_BG, RADAR_COLOR, NO_RADAR_COLOR, CELL_WIDTH, CELL_HEIGHT
    from ui.widgets import ToolTip

def resumo_do_dia(lista):
    """Gera resumo do dia baseado nos dados coletados"""
    total = len(lista)
    com_radar = sum(1 for item in lista if item["radar"])
    return f"{com_radar}/{total} horas com radar"

def desenhar_dia(scrollable_frame, d, lista):
    dias_inperantes = []
    """Renderiza uma linha de dia com suas 24 horas"""
    resumo = resumo_do_dia(lista)

    lbl_dia = tk.Label(
        scrollable_frame,
        text=f"{d:02d}",
        fg="white",
        bg=THEME_BG
    )
    lbl_dia.grid(row=d, column=0)
    ToolTip(lbl_dia, text=resumo)

    def create_preview_window(cell, event):
        """Cria uma janela de preview posicionada"""
        preview = tk.Toplevel(cell)
        preview.wm_overrideredirect(True)
        preview.attributes("-topmost", True)
        preview.geometry(f"+{event.x_root+10}+{event.y_root+10}")
        return preview

    def destroy_preview(cell):
        """Destrói a janela de preview se existir"""
        if getattr(cell, "preview_window", None):
            cell.preview_window.destroy()
            cell.preview_window = None
            cell.preview_image = None

    for item in lista:
        h = item["hora"]
        radar = item["radar"]

        cor = RADAR_COLOR if radar else NO_RADAR_COLOR

        cell = tk.Label(
            scrollable_frame,
            bg=cor,
            width=CELL_WIDTH,
            height=CELL_HEIGHT,
            relief="solid"
        )
        cell.grid(row=d, column=h+1, padx=1, pady=1)

        if radar:
            def show_radar_preview(event, c=cell, r=radar):
                destroy_preview(c)
                c.preview_window = create_preview_window(c, event)
                waiting = tk.Label(c.preview_window, text="Carregando...", bg="#111", fg="#fff", padx=6, pady=2)
                waiting.pack()

                def load_image():
                    try:
                        resp = requests.get(r["path"], timeout=8)
                        resp.raise_for_status()
                        img = Image.open(BytesIO(resp.content))
                        img.thumbnail((160, 120), Image.Resampling.LANCZOS)
                        c.preview_image = ImageTk.PhotoImage(img)
                        def update():
                            if not getattr(c, "preview_window", None):
                                return
                            for w in c.preview_window.winfo_children():
                                w.destroy()
                            tk.Label(c.preview_window, text=f"{r.get('data', 'N/A')}", bg="#111", fg="#0f0", font=("Arial", 8), anchor="center").pack(fill="x")
                            img_lbl = tk.Label(c.preview_window, image=c.preview_image, bg="black")
                            img_lbl.image = c.preview_image
                            img_lbl.pack()
                        c.after(0, update)
                    except Exception:
                        def show_error():
                            if not getattr(c, "preview_window", None):
                                return
                            for w in c.preview_window.winfo_children():
                                w.destroy()
                            tk.Label(c.preview_window, text=f"Data API: {r.get('data', 'N/A')}\n❌ Erro ao carregar", bg="#111", fg="#f00", font=("Arial", 8), anchor="center").pack(fill="x")
                        c.after(0, show_error)
                threading.Thread(target=load_image, daemon=True).start()

            cell.bind("<Enter>", show_radar_preview)
            cell.bind("<Leave>", lambda e, c=cell: destroy_preview(c))
        else:
            def show_no_radar_preview(event, c=cell, r=item, hora=h):
                destroy_preview(c)
                c.preview_window = create_preview_window(c, event)
                api_data = r.get('data', 'N/A')
                txt = f"Hora {hora:02d}\nData API: {api_data}\nSem radar"
                tk.Label(c.preview_window, text=txt, bg="#111", fg="#888", font=("Arial", 8), anchor="center").pack(fill="x")
                
            cell.bind("<Enter>", show_no_radar_preview)
            cell.bind("<Leave>", lambda e, c=cell: destroy_preview(c))
