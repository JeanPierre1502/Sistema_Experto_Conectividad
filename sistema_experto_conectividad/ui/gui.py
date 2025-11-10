# ui/gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Optional
from sistema_experto_conectividad.motor_inferencia import engine
from sistema_experto_conectividad.storage import historial

APP_TITLE = "Sistema Experto - Diagnóstico de Conectividad"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x620")
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        # Top frame: controls
        frm_top = ttk.Frame(self, padding=8)
        frm_top.pack(fill="x")

        ttk.Label(frm_top, text="Gateway (opcional):").pack(side="left", padx=(0,6))
        self.entry_gateway = ttk.Entry(frm_top, width=18)
        self.entry_gateway.pack(side="left")
        self.detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_top, text="Detectar automáticamente si está vacío", variable=self.detect_var).pack(side="left", padx=10)

        self.btn_run = ttk.Button(frm_top, text="Ejecutar diagnóstico", command=self._on_run)
        self.btn_run.pack(side="left", padx=6)

        self.btn_refresh_hist = ttk.Button(frm_top, text="Actualizar historial", command=self._refresh_history)
        self.btn_refresh_hist.pack(side="right")

        # Main frames
        main = ttk.Frame(self, padding=8)
        main.pack(fill="both", expand=True)

        # Left pane: resumen y parámetros
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0,6))

        ttk.Label(left, text="Resumen del diagnóstico", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.txt_resumen = scrolledtext.ScrolledText(left, height=6, wrap="word", state="disabled")
        self.txt_resumen.pack(fill="x", pady=(4,8))

        ttk.Label(left, text="Parámetros detectados", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.tree_params = ttk.Treeview(left, columns=("valor", "explicacion"), show="headings", height=10)
        self.tree_params.heading("valor", text="Valor")
        self.tree_params.heading("explicacion", text="Explicación")
        self.tree_params.column("valor", width=120, anchor="center")
        self.tree_params.column("explicacion", width=400, anchor="w")
        self.tree_params.pack(fill="both", expand=True)

        # Right pane: pasos sugeridos y acciones
        right = ttk.Frame(main, width=360)
        right.pack(side="right", fill="y")

        ttk.Label(right, text="Pasos sugeridos", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.list_pasos = tk.Listbox(right, height=12)
        self.list_pasos.pack(fill="both", expand=False)

        ttk.Label(right, text="Detalle del paso", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6,0))
        self.txt_paso = scrolledtext.ScrolledText(right, height=8, wrap="word", state="disabled")
        self.txt_paso.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill="x", pady=(6,0))
        self.btn_apply = ttk.Button(btn_frame, text="Marcar solución aplicada", command=self._on_apply_solution)
        self.btn_apply.pack(side="left")
        self.btn_view_report = ttk.Button(btn_frame, text="Ver reporte JSON", command=self._on_view_report)
        self.btn_view_report.pack(side="right")

        # Bottom: historial
        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill="both")
        ttk.Label(bottom, text="Historial (casos previos)", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.list_hist = tk.Listbox(bottom, height=6)
        self.list_hist.pack(fill="both", expand=True)
        self._refresh_history()

        # Bind selection events
        self.list_pasos.bind("<<ListboxSelect>>", self._on_paso_select)
        self.list_hist.bind("<<ListboxSelect>>", self._on_hist_select)

        # state
        self._last_diagnosis = None

    def _set_ui_busy(self, busy=True):
        state = "disabled" if busy else "normal"
        self.btn_run.config(state=state)
        self.btn_apply.config(state=state)
        self.btn_view_report.config(state=state)

    def _on_run(self):
        gw = self.entry_gateway.get().strip() or None
        auto = self.detect_var.get()
        # run in background thread
        t = threading.Thread(target=self._run_diagnosis_thread, args=(gw, auto), daemon=True)
        t.start()
        self._set_ui_busy(True)

    def _run_diagnosis_thread(self, gw: Optional[str], auto: bool):
        try:
            datos = engine.diagnosticar_y_registrar(gateway_ip=gw, auto_detect_gateway=auto)
            self._last_diagnosis = datos
            self.after(0, lambda: self._show_diagnosis(datos))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error ejecutando diagnóstico:\n{e}"))
        finally:
            self.after(0, lambda: self._set_ui_busy(False))
            self.after(0, self._refresh_history)

    def _show_diagnosis(self, datos):
        # Resumen
        resumen = f"Diagnóstico: {datos.get('diagnostico')}\nSeveridad: {datos.get('severidad')}\nGateway usado: {datos.get('gateway_ip')}"
        self.txt_resumen.config(state="normal")
        self.txt_resumen.delete("1.0", "end")
        self.txt_resumen.insert("1.0", resumen)
        self.txt_resumen.config(state="disabled")

        # Params
        for i in self.tree_params.get_children():
            self.tree_params.delete(i)
        param_map = {
            "Conexión a Internet": (datos.get("conexion"), "True si hubo respuesta de ping a host externo"),
            "DNS operativo": (datos.get("dns"), "True si se resolvió al menos un dominio"),
            "Gateway accesible": (datos.get("gateway"), "True si el gateway responde al ping"),
            "Latencia (ms)": (datos.get("latencia_ms"), "Promedio de tiempo de respuesta en ms"),
            "Pérdida (%)": (datos.get("perdida_pct"), "Porcentaje de paquetes perdidos en pings"),
            "Puerto 80 (HTTP)": (datos.get("puertos_http"), "Si se puede conectar al puerto 80 de google"),
            "Puerto 443 (HTTPS)": (datos.get("puertos_https"), "Si se puede conectar al puerto 443 de google"),
            "Adaptadores (up)": (', '.join([f"{k}:{'up' if v else 'down'}" for k,v in datos.get("estado_adaptadores", {}).items()]), "Estado de adaptadores detectados"),
        }
        for k, (val, explanation) in param_map.items():
            self.tree_params.insert("", "end", values=(str(val), explanation))

        # Pasos
        self.list_pasos.delete(0, "end")
        for p in datos.get("pasos", []):
            title = p.get("title")
            self.list_pasos.insert("end", title)
        # Clear detalle
        self.txt_paso.config(state="normal")
        self.txt_paso.delete("1.0", "end")
        self.txt_paso.config(state="disabled")

    def _on_paso_select(self, evt):
        sel = self.list_pasos.curselection()
        if not sel or self._last_diagnosis is None:
            return
        idx = sel[0]
        paso = self._last_diagnosis.get("pasos", [])[idx]
        detalle = paso.get("detalle", "") + "\n\nPasos:\n" + "\n".join([f"- {s}" for s in paso.get("paso_a_paso", [])])
        self.txt_paso.config(state="normal")
        self.txt_paso.delete("1.0", "end")
        self.txt_paso.insert("1.0", detalle)
        self.txt_paso.config(state="disabled")

    def _on_apply_solution(self):
        if not self._last_diagnosis:
            messagebox.showinfo("Info", "No hay diagnóstico reciente para aplicar.")
            return
        # Si un paso está seleccionado, proponemos esa solución
        sel = self.list_pasos.curselection()
        propuesta = ""
        if sel:
            idx = sel[0]
            paso = self._last_diagnosis.get("pasos", [])[idx]
            propuesta = paso.get("title") + ": " + (paso.get("paso_a_paso")[0] if paso.get("paso_a_paso") else "")
        # Pedir confirmación / editar
        solucion = tk.simpledialog.askstring("Solución aplicada", "Describa la solución aplicada (edite si quiere):", initialvalue=propuesta)
        if solucion:
            # Guardamos la solución en el último caso del historial (asumimos que fue registrado al diagnosticar)
            hist = historial._leer_raw()  # uso interno - es OK aquí
            if hist:
                last = hist[-1]
                historial.aplicar_solucion_a_caso(last, solucion)
                messagebox.showinfo("Registrado", "Solución aplicada y guardada en historial.")
                self._refresh_history()
            else:
                messagebox.showwarning("No hay historial", "No se encontró el caso en historial para actualizar.")

    def _on_view_report(self):
        if not self._last_diagnosis:
            messagebox.showinfo("Info", "No hay diagnóstico reciente.")
            return
        import json
        txt = json.dumps(self._last_diagnosis, indent=2, ensure_ascii=False)
        # mostrar en ventana
        win = tk.Toplevel(self)
        win.title("Reporte JSON")
        st = scrolledtext.ScrolledText(win, width=100, height=40)
        st.pack(fill="both", expand=True)
        st.insert("1.0", txt)
        st.config(state="disabled")

    def _refresh_history(self):
        self.list_hist.delete(0, "end")
        items = historial.leer_historial(30)
        for it in reversed(items):
            ts = it.get("timestamp", "")[:19]
            diag = it.get("diagnostico", "")
            sol = it.get("solucion_aplicada", "")
            display = f"{ts} | {diag}" + (f" | Sol: {sol}" if sol else "")
            self.list_hist.insert("end", display)

    def _on_hist_select(self, evt):
        sel = self.list_hist.curselection()
        if not sel:
            return
        idx = sel[0]
        # Obtener items en el mismo orden que mostramos (reversed)
        items = historial.leer_historial(30)
        if not items:
            return
        item = list(reversed(items))[idx]
        # abrir ventana con detalles
        win = tk.Toplevel(self)
        win.title("Detalle histórico")
        st = scrolledtext.ScrolledText(win, width=100, height=30)
        st.pack(fill="both", expand=True)
        import json
        st.insert("1.0", json.dumps(item, indent=2, ensure_ascii=False))
        st.config(state="disabled")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
