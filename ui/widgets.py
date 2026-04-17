"""Componentes de UI reutilizáveis"""
import tkinter as tk
from core.config import TOOLTIP_BG, TOOLTIP_FG

class ToolTip:
    """Classe para exibir tooltips em widgets"""
    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text
        self.tip_window = None

        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x = self.widget.winfo_rootx() + 15
        y = self.widget.winfo_rooty() + 15

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, bg=TOOLTIP_BG, fg=TOOLTIP_FG, padx=5, pady=2)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
