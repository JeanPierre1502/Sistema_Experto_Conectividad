# ui/gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os

# Importaciones del sistema
from sistema_experto_conectividad.motor_inferencia import engine
from sistema_experto_conectividad.storage import historial

# =========================wh============================
# CONSTANTES Y CONFIGURACIÓN DE TEMA OSCURO
# =====================================================
APP_TITLE = "Sistema Experto - Diagnóstico de Conectividad"

# Paleta de colores modo oscuro
COLORS = {
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#0f3460',
    'accent': '#00d9ff',
    'accent_hover': '#00b8d4',
    'success': '#00ff88',
    'warning': '#ffaa00',
    'error': '#ff4444',
    'text': '#e0e0e0',
    'text_secondary': '#a0a0a0',
    'border': '#2a2a4e'
}

class ModernApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title(APP_TITLE)
        self.geometry("1400x900")
        self.resizable(True, True)
        
        # Variables de estado
        self._last_diagnosis = None
        self._animation_running = False
        self._search_var = tk.StringVar()
        self._search_var.trace('w', self._filter_history)
        
        # Configurar tema oscuro
        self._setup_dark_theme()
        
        # Construir interfaz
        self._build_ui()
        
    # =====================================================
    # CONFIGURACIÓN DE TEMA OSCURO
    # =====================================================
    def _setup_dark_theme(self):
        """Configura el tema oscuro para toda la aplicación"""
        self.configure(bg=COLORS['bg_dark'])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configuración general
        style.configure('.',
            background=COLORS['bg_dark'],
            foreground=COLORS['text'],
            bordercolor=COLORS['border'],
            darkcolor=COLORS['bg_medium'],
            lightcolor=COLORS['bg_light'],
            troughcolor=COLORS['bg_medium'],
            focuscolor=COLORS['accent'],
            selectbackground=COLORS['accent'],
            selectforeground=COLORS['bg_dark'],
            fieldbackground=COLORS['bg_medium'],
            font=('Segoe UI', 10)
        )
        
        # Frames
        style.configure('TFrame', background=COLORS['bg_dark'])
        style.configure('Card.TFrame', background=COLORS['bg_medium'], relief='flat')
        
        # Labels
        style.configure('TLabel', background=COLORS['bg_dark'], foreground=COLORS['text'])
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=COLORS['accent'])
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11), foreground=COLORS['text_secondary'])
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'), foreground=COLORS['text'])
        
        # Botones
        style.configure('TButton',
            background=COLORS['accent'],
            foreground=COLORS['bg_dark'],
            borderwidth=0,
            focuscolor='none',
            font=('Segoe UI', 10, 'bold'),
            padding=(20, 10)
        )
        style.map('TButton',
            background=[('active', COLORS['accent_hover']), ('disabled', COLORS['bg_light'])],
            foreground=[('disabled', COLORS['text_secondary'])]
        )
        
        # Entry
        style.configure('TEntry',
            fieldbackground=COLORS['bg_medium'],
            foreground=COLORS['text'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['border'],
            darkcolor=COLORS['border'],
            insertcolor=COLORS['text']
        )
        
        # Checkbutton
        style.configure('TCheckbutton',
            background=COLORS['bg_dark'],
            foreground=COLORS['text']
        )
        
        # Treeview
        style.configure('Treeview',
            background=COLORS['bg_medium'],
            foreground=COLORS['text'],
            fieldbackground=COLORS['bg_medium'],
            borderwidth=0
        )
        style.configure('Treeview.Heading',
            background=COLORS['bg_light'],
            foreground=COLORS['text'],
            borderwidth=1,
            font=('Segoe UI', 10, 'bold')
        )
        style.map('Treeview',
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', COLORS['bg_dark'])]
        )
        
    # =====================================================
    # CONSTRUCCIÓN DE INTERFAZ
    # =====================================================
    def _build_ui(self):
        """Construye toda la interfaz de usuario"""
        
        # Contenedor principal con scroll
        main_container = tk.Frame(self, bg=COLORS['bg_dark'])
        main_container.pack(fill='both', expand=True)
        
        # ===== HEADER =====
        self._build_header(main_container)
        
        # ===== PANEL DE CONTROL =====
        self._build_control_panel(main_container)
        
        # ===== LOADING ANIMATION =====
        self._build_loading_animation(main_container)
        
        # ===== CONTENIDO PRINCIPAL (3 COLUMNAS) =====
        content = tk.Frame(main_container, bg=COLORS['bg_dark'])
        content.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Columna izquierda: Diagnóstico y parámetros
        left_frame = self._build_left_column(content)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Columna central: Visualizaciones gráficas
        center_frame = self._build_center_column(content)
        center_frame.pack(side='left', fill='both', expand=True, padx=10)
        
        # Columna derecha: Pasos y acciones
        right_frame = self._build_right_column(content)
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # ===== HISTORIAL INFERIOR =====
        self._build_history_panel(main_container)
        
    def _build_header(self, parent):
        """Construye el header de la aplicación"""
        header = tk.Frame(parent, bg=COLORS['bg_medium'], height=100)
        header.pack(fill='x', padx=20, pady=(20, 0))
        header.pack_propagate(False)
        
        # Contenedor interno con padding
        header_content = tk.Frame(header, bg=COLORS['bg_medium'])
        header_content.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Título
        ttk.Label(
            header_content,
            text="🔧 Sistema Experto de Conectividad",
            style='Title.TLabel'
        ).pack(anchor='w')
        
        # Subtítulo
        ttk.Label(
            header_content,
            text="Diagnóstico automático · Análisis inteligente · Soluciones basadas en IA",
            style='Subtitle.TLabel'
        ).pack(anchor='w', pady=(5, 0))
        
    def _build_control_panel(self, parent):
        """Construye el panel de control superior"""
        control = tk.Frame(parent, bg=COLORS['bg_dark'])
        control.pack(fill='x', padx=20, pady=20)
        
        # Contenedor de controles
        controls_frame = tk.Frame(control, bg=COLORS['bg_medium'])
        controls_frame.pack(fill='x', padx=2, pady=2)
        
        inner = tk.Frame(controls_frame, bg=COLORS['bg_medium'])
        inner.pack(fill='x', padx=20, pady=15)
        
        # Gateway input
        gateway_frame = tk.Frame(inner, bg=COLORS['bg_medium'])
        gateway_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(
            gateway_frame,
            text="Gateway (opcional):",
            style='Header.TLabel'
        ).pack(side='left', padx=(0, 10))
        
        self.entry_gateway = ttk.Entry(gateway_frame, width=25)
        self.entry_gateway.pack(side='left', padx=5)
        
        self.detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            gateway_frame,
            text="Detectar automáticamente",
            variable=self.detect_var
        ).pack(side='left', padx=10)
        
        # Botones de acción
        buttons_frame = tk.Frame(inner, bg=COLORS['bg_medium'])
        buttons_frame.pack(side='right')
        
        self.btn_run = ttk.Button(
            buttons_frame,
            text="▶ Ejecutar Diagnóstico",
            command=self._on_run
        )
        self.btn_run.pack(side='left', padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🔄 Actualizar Historial",
            command=self._refresh_history
        ).pack(side='left', padx=5)
        
        ttk.Button(
            buttons_frame,
            text="📊 Exportar Reporte",
            command=self._export_report
        ).pack(side='left', padx=5)
        
    def _build_loading_animation(self, parent):
        """Construye el panel de animación de carga"""
        self.loading_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        
        # Canvas para animación
        self.loading_canvas = tk.Canvas(
            self.loading_frame,
            width=400,
            height=100,
            bg=COLORS['bg_dark'],
            highlightthickness=0
        )
        self.loading_canvas.pack(pady=20)
        
        # Texto de carga
        self.loading_label = tk.Label(
            self.loading_frame,
            text="Analizando conectividad...",
            font=('Segoe UI', 12, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['bg_dark']
        )
        self.loading_label.pack()
        
        # Inicializar elementos de animación
        self._loading_bars = []
        for i in range(5):
            bar = self.loading_canvas.create_rectangle(
                80 + i * 50, 80, 110 + i * 50, 90,
                fill=COLORS['accent'],
                outline=''
            )
            self._loading_bars.append(bar)
            
    def _build_left_column(self, parent):
        """Construye la columna izquierda: diagnóstico y parámetros"""
        frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        
        # === RESUMEN DEL DIAGNÓSTICO ===
        card1 = self._create_card(frame)
        card1.pack(fill='x', pady=(0, 15))
        
        ttk.Label(
            card1,
            text="📋 Resumen del Diagnóstico",
            style='Header.TLabel'
        ).pack(anchor='w', pady=(0, 10))
        
        # Frame para indicadores de estado
        self.status_frame = tk.Frame(card1, bg=COLORS['bg_medium'])
        self.status_frame.pack(fill='x', pady=(0, 10))
        
        # Texto de resumen
        self.txt_resumen = scrolledtext.ScrolledText(
            card1,
            height=4,
            wrap='word',
            font=('Segoe UI', 10),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            insertbackground=COLORS['text'],
            relief='flat',
            borderwidth=5
        )
        self.txt_resumen.pack(fill='x')
        
        # === PARÁMETROS DETECTADOS ===
        card2 = self._create_card(frame)
        card2.pack(fill='both', expand=True)
        
        ttk.Label(
            card2,
            text="🔍 Parámetros Detectados",
            style='Header.TLabel'
        ).pack(anchor='w', pady=(0, 10))
        
        # Treeview para parámetros
        tree_frame = tk.Frame(card2, bg=COLORS['bg_medium'])
        tree_frame.pack(fill='both', expand=True)
        
        self.tree_params = ttk.Treeview(
            tree_frame,
            columns=('parametro', 'valor', 'estado'),
            show='headings',
            height=12
        )
        
        self.tree_params.heading('parametro', text='Parámetro')
        self.tree_params.heading('valor', text='Valor')
        self.tree_params.heading('estado', text='Estado')
        
        self.tree_params.column('parametro', width=180)
        self.tree_params.column('valor', width=120, anchor='center')
        self.tree_params.column('estado', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree_params.yview)
        self.tree_params.configure(yscrollcommand=scrollbar.set)
        
        self.tree_params.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        return frame
        
    def _build_center_column(self, parent):
        """Construye la columna central: visualizaciones gráficas"""
        frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        
        # === GRÁFICO DE MÉTRICAS ===
        card = self._create_card(frame)
        card.pack(fill='both', expand=True)
        
        ttk.Label(
            card,
            text="📊 Visualización de Métricas",
            style='Header.TLabel'
        ).pack(anchor='w', pady=(0, 10))
        
        # Canvas para gráficos
        self.graph_canvas = tk.Canvas(
            card,
            bg=COLORS['bg_light'],
            highlightthickness=0,
            height=400
        )
        self.graph_canvas.pack(fill='both', expand=True)
        
        # Leyenda
        legend_frame = tk.Frame(card, bg=COLORS['bg_medium'])
        legend_frame.pack(fill='x', pady=(10, 0))
        
        self._create_legend_item(legend_frame, COLORS['success'], "Óptimo").pack(side='left', padx=10)
        self._create_legend_item(legend_frame, COLORS['warning'], "Moderado").pack(side='left', padx=10)
        self._create_legend_item(legend_frame, COLORS['error'], "Crítico").pack(side='left', padx=10)
        
        return frame
        
    def _build_right_column(self, parent):
        """Construye la columna derecha: pasos y acciones"""
        frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        
        # === PASOS SUGERIDOS ===
        card1 = self._create_card(frame)
        card1.pack(fill='both', expand=True, pady=(0, 15))
        
        header_frame = tk.Frame(card1, bg=COLORS['bg_medium'])
        header_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text="✅ Pasos Sugeridos",
            style='Header.TLabel'
        ).pack(side='left')
        
        # Contador de pasos
        self.steps_counter = tk.Label(
            header_frame,
            text="0 pasos",
            font=('Segoe UI', 9),
            fg=COLORS['text_secondary'],
            bg=COLORS['bg_medium']
        )
        self.steps_counter.pack(side='right')
        
        # Listbox de pasos
        list_frame = tk.Frame(card1, bg=COLORS['bg_medium'])
        list_frame.pack(fill='both', expand=True)
        
        self.list_pasos = tk.Listbox(
            list_frame,
            font=('Segoe UI', 10),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            selectbackground=COLORS['accent'],
            selectforeground=COLORS['bg_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            height=8
        )
        self.list_pasos.pack(side='left', fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, command=self.list_pasos.yview)
        self.list_pasos.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        
        self.list_pasos.bind('<<ListboxSelect>>', self._on_paso_select)
        
        # === DETALLE DEL PASO ===
        card2 = self._create_card(frame)
        card2.pack(fill='both', expand=True)
        
        ttk.Label(
            card2,
            text="📝 Detalle del Paso",
            style='Header.TLabel'
        ).pack(anchor='w', pady=(0, 10))
        
        self.txt_paso = scrolledtext.ScrolledText(
            card2,
            wrap='word',
            font=('Segoe UI', 10),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            insertbackground=COLORS['text'],
            relief='flat',
            borderwidth=5,
            height=12
        )
        self.txt_paso.pack(fill='both', expand=True, pady=(0, 10))
        
        # Botones de acción
        actions = tk.Frame(card2, bg=COLORS['bg_medium'])
        actions.pack(fill='x')
        
        ttk.Button(
            actions,
            text="✓ Marcar como Aplicado",
            command=self._on_apply_solution
        ).pack(side='left', padx=(0, 10))
        
        ttk.Button(
            actions,
            text="📄 Ver JSON Completo",
            command=self._on_view_report
        ).pack(side='left')
        
        return frame
        
    def _build_history_panel(self, parent):
        """Construye el panel de historial"""
        card = self._create_card(parent)
        card.pack(fill='both', padx=20, pady=(0, 20))
        
        # Header con búsqueda
        header = tk.Frame(card, bg=COLORS['bg_medium'])
        header.pack(fill='x', pady=(0, 10))
        
        ttk.Label(
            header,
            text="📚 Historial de Diagnósticos",
            style='Header.TLabel'
        ).pack(side='left')
        
        # Búsqueda
        search_frame = tk.Frame(header, bg=COLORS['bg_medium'])
        search_frame.pack(side='right')
        
        tk.Label(
            search_frame,
            text="🔍",
            font=('Segoe UI', 12),
            fg=COLORS['text'],
            bg=COLORS['bg_medium']
        ).pack(side='left', padx=(0, 5))
        
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self._search_var,
            width=30
        )
        search_entry.pack(side='left')
        
        # Listbox de historial
        list_frame = tk.Frame(card, bg=COLORS['bg_medium'])
        list_frame.pack(fill='both', expand=True)
        
        self.list_hist = tk.Listbox(
            list_frame,
            font=('Segoe UI', 10),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            selectbackground=COLORS['accent'],
            selectforeground=COLORS['bg_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            height=6
        )
        self.list_hist.pack(side='left', fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, command=self.list_hist.yview)
        self.list_hist.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        
        self.list_hist.bind('<<ListboxSelect>>', self._on_hist_select)
        
        self._refresh_history()
        
    # =====================================================
    # MÉTODOS AUXILIARES DE UI
    # =====================================================
    def _create_card(self, parent):
        """Crea una tarjeta con estilo"""
        card = tk.Frame(parent, bg=COLORS['bg_medium'])
        inner = tk.Frame(card, bg=COLORS['bg_medium'])
        inner.pack(fill='both', expand=True, padx=20, pady=15)
        return inner
        
    def _create_legend_item(self, parent, color, text):
        """Crea un elemento de leyenda"""
        frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        
        canvas = tk.Canvas(frame, width=16, height=16, bg=COLORS['bg_medium'], highlightthickness=0)
        canvas.create_oval(2, 2, 14, 14, fill=color, outline='')
        canvas.pack(side='left', padx=(0, 5))
        
        tk.Label(
            frame,
            text=text,
            font=('Segoe UI', 9),
            fg=COLORS['text'],
            bg=COLORS['bg_medium']
        ).pack(side='left')
        
        return frame
        
    def _create_status_indicator(self, parent, label, status):
        """Crea un indicador de estado visual"""
        frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        
        # Determinar color según estado
        if status in [True, 'OK', 'Conectado']:
            color = COLORS['success']
            symbol = '●'
        elif status in [False, 'FAIL', 'Desconectado']:
            color = COLORS['error']
            symbol = '●'
        else:
            color = COLORS['warning']
            symbol = '●'
            
        # Indicador
        tk.Label(
            frame,
            text=symbol,
            font=('Segoe UI', 16),
            fg=color,
            bg=COLORS['bg_medium']
        ).pack(side='left', padx=(0, 8))
        
        # Texto
        tk.Label(
            frame,
            text=label,
            font=('Segoe UI', 10, 'bold'),
            fg=COLORS['text'],
            bg=COLORS['bg_medium']
        ).pack(side='left')
        
        return frame
        
    # =====================================================
    # ANIMACIÓN DE CARGA
    # =====================================================
    def _show_loading(self):
        """Muestra la animación de carga"""
        self._animation_running = True
        self.loading_frame.pack(fill='x', padx=20, pady=20)
        self._animate_loading()
        
    def _hide_loading(self):
        """Oculta la animación de carga"""
        self._animation_running = False
        self.loading_frame.pack_forget()
        
    def _animate_loading(self, step=0):
        """Animación de barras de carga"""
        if not self._animation_running:
            return
            
        # Actualizar alturas de las barras
        for i, bar in enumerate(self._loading_bars):
            offset = (step + i * 2) % 10
            height = 10 + offset * 3
            self.loading_canvas.coords(
                bar,
                80 + i * 50, 90 - height,
                110 + i * 50, 90
            )
            
        # Actualizar texto
        dots = '.' * ((step // 3) % 4)
        self.loading_label.config(text=f"Analizando conectividad{dots}")
        
        # Continuar animación
        self.after(100, lambda: self._animate_loading(step + 1))
        
    # =====================================================
    # VISUALIZACIÓN DE GRÁFICOS
    # =====================================================
    def _draw_metrics_graph(self, datos):
        """Dibuja gráficos de métricas en el canvas"""
        self.graph_canvas.delete('all')
        
        width = self.graph_canvas.winfo_width()
        height = self.graph_canvas.winfo_height()
        
        if width <= 1:
            width = 400
        if height <= 1:
            height = 400
            
        # Márgenes
        margin = 40
        graph_width = width - 2 * margin
        graph_height = height - 2 * margin
        
        # Obtener valores
        latencia = datos.get('latencia_ms', 0)
        perdida = datos.get('perdida_pct', 0)
        
        # Dibujar título
        self.graph_canvas.create_text(
            width // 2, 20,
            text="Análisis de Rendimiento de Red",
            font=('Segoe UI', 12, 'bold'),
            fill=COLORS['text']
        )
        
        # === GRÁFICO DE LATENCIA ===
        lat_x = margin
        lat_y = margin + 40
        lat_width = graph_width // 2 - 20
        lat_height = graph_height - 60
        
        self._draw_bar_chart(
            lat_x, lat_y, lat_width, lat_height,
            latencia, 200, "Latencia (ms)",
            [50, 100, 150]
        )
        
        # === GRÁFICO DE PÉRDIDA ===
        per_x = margin + graph_width // 2 + 20
        per_y = lat_y
        per_width = lat_width
        per_height = lat_height
        
        self._draw_bar_chart(
            per_x, per_y, per_width, per_height,
            perdida, 100, "Pérdida (%)",
            [5, 15, 30]
        )
        
    def _draw_bar_chart(self, x, y, width, height, value, max_val, title, thresholds):
        """Dibuja un gráfico de barra vertical"""
        # Título
        self.graph_canvas.create_text(
            x + width // 2, y - 10,
            text=title,
            font=('Segoe UI', 10, 'bold'),
            fill=COLORS['text']
        )
        
        # Borde del contenedor
        self.graph_canvas.create_rectangle(
            x, y, x + width, y + height,
            outline=COLORS['border'],
            width=2
        )
        
        # Determinar color según umbrales
        if value < thresholds[0]:
            color = COLORS['success']
            status = "Óptimo"
        elif value < thresholds[1]:
            color = COLORS['warning']
            status = "Moderado"
        else:
            color = COLORS['error']
            status = "Crítico"
            
        # Calcular altura de barra
        bar_height = min((value / max_val) * height, height)
        
        # Dibujar barra
        self.graph_canvas.create_rectangle(
            x + 20, y + height - bar_height,
            x + width - 20, y + height,
            fill=color,
            outline=''
        )
        
        # Valor
        self.graph_canvas.create_text(
            x + width // 2, y + height - bar_height - 15,
            text=f"{value:.1f}",
            font=('Segoe UI', 14, 'bold'),
            fill=color
        )
        
        # Estado
        self.graph_canvas.create_text(
            x + width // 2, y + height + 20,
            text=status,
            font=('Segoe UI', 10),
            fill=color
        )
        
        # Líneas de referencia
        for threshold in thresholds:
            line_y = y + height - (threshold / max_val) * height
            self.graph_canvas.create_line(
                x, line_y, x + width, line_y,
                fill=COLORS['border'],
                dash=(2, 4)
            )
            
    # =====================================================
    # LÓGICA DE DIAGNÓSTICO
    # =====================================================
    def _on_run(self):
        """Ejecuta el diagnóstico en un hilo separado"""
        gw = self.entry_gateway.get().strip() or None
        auto = self.detect_var.get()
        
        # Deshabilitar botón
        self.btn_run.config(state='disabled')
        
        # Mostrar animación
        self._show_loading()
        
        # Ejecutar en hilo
        t = threading.Thread(
            target=self._run_diagnosis_thread,
            args=(gw, auto),
            daemon=True
        )
        t.start()
        
    def _run_diagnosis_thread(self, gw: Optional[str], auto: bool):
        """Hilo de diagnóstico"""
        try:
            datos = engine.diagnosticar_y_registrar(
                gateway_ip=gw,
                auto_detect_gateway=auto
            )
            self._last_diagnosis = datos
            self.after(0, lambda: self._show_diagnosis(datos))
        except Exception as e:
            self.after(0, lambda: self._show_error(e))
        finally:
            self.after(0, self._hide_loading)
            self.after(0, lambda: self.btn_run.config(state='normal'))
            
    def _show_diagnosis(self, datos):
        """Muestra los resultados del diagnóstico"""
        # === RESUMEN ===
        resumen = (
            f"🔍 Diagnóstico: {datos.get('diagnostico', 'N/A')}\n"
            f"⚠️  Severidad: {datos.get('severidad', 'N/A')}\n"
            f"🌐 Gateway: {datos.get('gateway_ip', 'No detectado')}"
        )
        self.txt_resumen.delete('1.0', 'end')
        self.txt_resumen.insert('1.0', resumen)
        
        # === INDICADORES DE ESTADO ===
        # Limpiar indicadores anteriores
        for widget in self.status_frame.winfo_children():
            widget.destroy()
            
        # Crear indicadores
        indicators = [
            ("Internet", datos.get('conexion', False)),
            ("DNS", datos.get('dns', False)),
            ("Gateway", datos.get('gateway', False)),
            ("HTTP", datos.get('puertos_http', False)),
            ("HTTPS", datos.get('puertos_https', False))
        ]
        
        for label, status in indicators:
            indicator = self._create_status_indicator(self.status_frame, label, status)
            indicator.pack(side='left', padx=10, pady=5)
        
        # === PARÁMETROS EN TABLA ===
        # Limpiar tabla
        for item in self.tree_params.get_children():
            self.tree_params.delete(item)
            
        # Insertar datos
        params = [
            ("Conexión a Internet", datos.get('conexion', 'N/A'), '✓' if datos.get('conexion') else '✗'),
            ("DNS Operativo", datos.get('dns', 'N/A'), '✓' if datos.get('dns') else '✗'),
            ("Gateway Accesible", datos.get('gateway', 'N/A'), '✓' if datos.get('gateway') else '✗'),
            ("Latencia (ms)", f"{datos.get('latencia_ms', 0):.1f}", self._get_latency_status(datos.get('latencia_ms', 0))),
            ("Pérdida de Paquetes (%)", f"{datos.get('perdida_pct', 0):.1f}", self._get_loss_status(datos.get('perdida_pct', 0))),
            ("Puerto 80 (HTTP)", datos.get('puertos_http', 'N/A'), '✓' if datos.get('puertos_http') else '✗'),
            ("Puerto 443 (HTTPS)", datos.get('puertos_https', 'N/A'), '✓' if datos.get('puertos_https') else '✗'),
        ]
        
        for param, valor, estado in params:
            # Colores según estado
            if estado == '✓':
                self.tree_params.insert('', 'end', values=(param, valor, estado), tags=('ok',))
            elif estado == '✗':
                self.tree_params.insert('', 'end', values=(param, valor, estado), tags=('error',))
            else:
                self.tree_params.insert('', 'end', values=(param, valor, estado), tags=('warning',))
                
        # Configurar tags de color
        self.tree_params.tag_configure('ok', foreground=COLORS['success'])
        self.tree_params.tag_configure('error', foreground=COLORS['error'])
        self.tree_params.tag_configure('warning', foreground=COLORS['warning'])
        
        # Agregar adaptadores de red
        adaptadores = datos.get('estado_adaptadores', {})
        for nombre, estado in adaptadores.items():
            estado_text = 'UP' if estado else 'DOWN'
            estado_symbol = '✓' if estado else '✗'
            self.tree_params.insert('', 'end', 
                values=(f"Adaptador: {nombre}", estado_text, estado_symbol),
                tags=('ok' if estado else 'error',)
            )
        
        # === PASOS SUGERIDOS ===
        self.list_pasos.delete(0, 'end')
        pasos = datos.get('pasos', [])
        
        for i, paso in enumerate(pasos, 1):
            # Agregar número y título
            self.list_pasos.insert('end', f"{i}. {paso.get('title', 'Sin título')}")
            
        # Actualizar contador
        self.steps_counter.config(text=f"{len(pasos)} pasos")
        
        # Limpiar detalle
        self.txt_paso.delete('1.0', 'end')
        self.txt_paso.insert('1.0', "Selecciona un paso de la lista para ver los detalles...")
        
        # === GRÁFICOS ===
        # Esperar a que el canvas esté listo
        self.after(100, lambda: self._draw_metrics_graph(datos))
        
        # === ACTUALIZAR HISTORIAL ===
        self._refresh_history()
        
        # Notificación
        self._show_notification("✓ Diagnóstico completado con éxito")
        
    def _show_error(self, error):
        """Muestra un error"""
        messagebox.showerror(
            "Error en el Diagnóstico",
            f"Ocurrió un error durante el diagnóstico:\n\n{str(error)}"
        )
        
    def _get_latency_status(self, latencia):
        """Determina el estado según la latencia"""
        if latencia < 50:
            return "Excelente"
        elif latencia < 100:
            return "Bueno"
        elif latencia < 150:
            return "Moderado"
        else:
            return "Crítico"
            
    def _get_loss_status(self, perdida):
        """Determina el estado según la pérdida"""
        if perdida < 5:
            return "Excelente"
        elif perdida < 15:
            return "Moderado"
        else:
            return "Crítico"
    
    # =====================================================
    # MANEJO DE PASOS
    # =====================================================
    def _on_paso_select(self, evt):
        """Maneja la selección de un paso"""
        sel = self.list_pasos.curselection()
        if not sel or not self._last_diagnosis:
            return
            
        paso = self._last_diagnosis['pasos'][sel[0]]
        
        # Construir texto detallado
        texto = f"📌 {paso.get('title', 'Sin título')}\n\n"
        texto += f"📝 Descripción:\n{paso.get('detalle', 'Sin descripción')}\n\n"
        texto += f"🔧 Pasos a seguir:\n\n"
        
        for linea in paso.get('paso_a_paso', []):
            texto += f"{linea}\n"
            
        texto += f"\n⚡ Prioridad: {paso.get('prioridad', 0)}"
        
        # Mostrar en el área de texto
        self.txt_paso.delete('1.0', 'end')
        self.txt_paso.insert('1.0', texto)
        
    def _on_apply_solution(self):
        """Marca una solución como aplicada"""
        sel = self.list_pasos.curselection()
        if not sel or not self._last_diagnosis:
            messagebox.showwarning(
                "Advertencia",
                "Por favor, selecciona un paso primero"
            )
            return
            
        paso = self._last_diagnosis['pasos'][sel[0]]
        
        # Solicitar confirmación
        result = messagebox.askyesno(
            "Confirmar Solución",
            f"¿Aplicaste la solución:\n\n{paso.get('title')}?\n\n"
            "Esto se registrará en el historial."
        )
        
        if result:
            # Intentar actualizar en el historial
            # Nota: Necesitarías implementar un método en historial.py
            # Por ahora, solo mostramos confirmación
            try:
                # historial.actualizar_solucion(caso_id, paso.get('title'))
                self._show_notification(f"✓ Solución registrada: {paso.get('title')}")
                
                # Marcar visualmente en la lista
                current_text = self.list_pasos.get(sel[0])
                self.list_pasos.delete(sel[0])
                self.list_pasos.insert(sel[0], f"✓ {current_text}")
                self.list_pasos.itemconfig(sel[0], fg=COLORS['success'])
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar la solución:\n{e}")
    
    # =====================================================
    # HISTORIAL
    # =====================================================
    def _refresh_history(self):
        """Actualiza la lista de historial"""
        self.list_hist.delete(0, 'end')
        
        try:
            items = historial.leer_historial(50)
            self._history_items = list(reversed(items))
            
            for item in self._history_items:
                timestamp = item.get('timestamp', 'N/A')[:19]
                diagnostico = item.get('diagnostico', 'Sin diagnóstico')
                severidad = item.get('severidad', 'N/A')
                
                # Formatear entrada
                entry = f"[{timestamp}] {severidad} | {diagnostico[:60]}..."
                self.list_hist.insert('end', entry)
                
                # Color según severidad
                if 'crítico' in severidad.lower():
                    self.list_hist.itemconfig('end', fg=COLORS['error'])
                elif 'moderado' in severidad.lower():
                    self.list_hist.itemconfig('end', fg=COLORS['warning'])
                else:
                    self.list_hist.itemconfig('end', fg=COLORS['success'])
                    
        except Exception as e:
            print(f"Error cargando historial: {e}")
            
    def _filter_history(self, *args):
        """Filtra el historial según la búsqueda"""
        search_text = self._search_var.get().lower()
        
        if not search_text:
            self._refresh_history()
            return
            
        self.list_hist.delete(0, 'end')
        
        try:
            if not hasattr(self, '_history_items'):
                items = historial.leer_historial(50)
                self._history_items = list(reversed(items))
                
            for item in self._history_items:
                timestamp = item.get('timestamp', '')
                diagnostico = item.get('diagnostico', '')
                severidad = item.get('severidad', '')
                
                # Buscar en todos los campos
                if (search_text in timestamp.lower() or 
                    search_text in diagnostico.lower() or 
                    search_text in severidad.lower()):
                    
                    entry = f"[{timestamp[:19]}] {severidad} | {diagnostico[:60]}..."
                    self.list_hist.insert('end', entry)
                    
                    if 'crítico' in severidad.lower():
                        self.list_hist.itemconfig('end', fg=COLORS['error'])
                    elif 'moderado' in severidad.lower():
                        self.list_hist.itemconfig('end', fg=COLORS['warning'])
                    else:
                        self.list_hist.itemconfig('end', fg=COLORS['success'])
                        
        except Exception as e:
            print(f"Error filtrando historial: {e}")
            
    def _on_hist_select(self, evt):
        """Maneja la selección de un elemento del historial"""
        sel = self.list_hist.curselection()
        if not sel:
            return
            
        try:
            if not hasattr(self, '_history_items'):
                return
                
            caso = self._history_items[sel[0]]
            
            # Crear ventana de detalle
            self._show_history_detail(caso)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el caso:\n{e}")
            
    def _show_history_detail(self, caso):
        """Muestra el detalle de un caso histórico"""
        win = tk.Toplevel(self)
        win.title("Detalle del Caso Histórico")
        win.geometry("800x600")
        win.configure(bg=COLORS['bg_dark'])
        
        # Header
        header = tk.Frame(win, bg=COLORS['bg_medium'])
        header.pack(fill='x', padx=20, pady=20)
        
        tk.Label(
            header,
            text="📋 Detalle Completo del Diagnóstico",
            font=('Segoe UI', 14, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['bg_medium']
        ).pack(anchor='w')
        
        # Contenido JSON
        text_frame = tk.Frame(win, bg=COLORS['bg_dark'])
        text_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        st = scrolledtext.ScrolledText(
            text_frame,
            wrap='word',
            font=('Consolas', 10),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            insertbackground=COLORS['text'],
            relief='flat',
            borderwidth=5
        )
        st.pack(fill='both', expand=True)
        
        # Formatear JSON
        json_text = json.dumps(caso, indent=2, ensure_ascii=False)
        st.insert('1.0', json_text)
        st.config(state='disabled')
        
        # Botón cerrar
        tk.Button(
            win,
            text="Cerrar",
            command=win.destroy,
            bg=COLORS['accent'],
            fg=COLORS['bg_dark'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(pady=(0, 20))
    
    # =====================================================
    # EXPORTACIÓN Y REPORTES
    # =====================================================
    def _on_view_report(self):
        """Muestra el reporte JSON del diagnóstico actual"""
        if not self._last_diagnosis:
            messagebox.showwarning(
                "Advertencia",
                "No hay ningún diagnóstico para mostrar.\n\n"
                "Ejecuta un diagnóstico primero."
            )
            return
            
        win = tk.Toplevel(self)
        win.title("Reporte JSON Completo")
        win.geometry("900x700")
        win.configure(bg=COLORS['bg_dark'])
        
        # Header
        header = tk.Frame(win, bg=COLORS['bg_medium'])
        header.pack(fill='x', padx=20, pady=20)
        
        tk.Label(
            header,
            text="📊 Reporte Técnico Completo",
            font=('Segoe UI', 14, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['bg_medium']
        ).pack(anchor='w')
        
        tk.Label(
            header,
            text="Todos los detalles técnicos del diagnóstico actual",
            font=('Segoe UI', 10),
            fg=COLORS['text_secondary'],
            bg=COLORS['bg_medium']
        ).pack(anchor='w', pady=(5, 0))
        
        # Contenido JSON
        text_frame = tk.Frame(win, bg=COLORS['bg_dark'])
        text_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        st = scrolledtext.ScrolledText(
            text_frame,
            wrap='word',
            font=('Consolas', 10),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            insertbackground=COLORS['text'],
            relief='flat',
            borderwidth=5
        )
        st.pack(fill='both', expand=True)
        
        # Formatear JSON
        json_text = json.dumps(self._last_diagnosis, indent=2, ensure_ascii=False)
        st.insert('1.0', json_text)
        st.config(state='disabled')
        
        # Botones
        btn_frame = tk.Frame(win, bg=COLORS['bg_dark'])
        btn_frame.pack(pady=(0, 20))
        
        tk.Button(
            btn_frame,
            text="💾 Guardar como JSON",
            command=lambda: self._export_json(self._last_diagnosis),
            bg=COLORS['accent'],
            fg=COLORS['bg_dark'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="Cerrar",
            command=win.destroy,
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
    def _export_report(self):
        """Exporta el diagnóstico actual a un archivo"""
        if not self._last_diagnosis:
            messagebox.showwarning(
                "Advertencia",
                "No hay ningún diagnóstico para exportar.\n\n"
                "Ejecuta un diagnóstico primero."
            )
            return
            
        # Preguntar formato
        win = tk.Toplevel(self)
        win.title("Exportar Reporte")
        win.geometry("400x250")
        win.configure(bg=COLORS['bg_dark'])
        win.transient(self)
        win.grab_set()
        
        # Centrar ventana
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (400 // 2)
        y = (win.winfo_screenheight() // 2) - (250 // 2)
        win.geometry(f"+{x}+{y}")
        
        # Contenido
        tk.Label(
            win,
            text="Selecciona el formato de exportación",
            font=('Segoe UI', 12, 'bold'),
            fg=COLORS['text'],
            bg=COLORS['bg_dark']
        ).pack(pady=20)
        
        btn_frame = tk.Frame(win, bg=COLORS['bg_dark'])
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="📄 JSON (Completo)",
            command=lambda: [win.destroy(), self._export_json(self._last_diagnosis)],
            bg=COLORS['accent'],
            fg=COLORS['bg_dark'],
            font=('Segoe UI', 11, 'bold'),
            relief='flat',
            padx=30,
            pady=15,
            cursor='hand2',
            width=20
        ).pack(pady=5)
        
        tk.Button(
            btn_frame,
            text="📝 TXT (Resumen)",
            command=lambda: [win.destroy(), self._export_txt(self._last_diagnosis)],
            bg=COLORS['accent'],
            fg=COLORS['bg_dark'],
            font=('Segoe UI', 11, 'bold'),
            relief='flat',
            padx=30,
            pady=15,
            cursor='hand2',
            width=20
        ).pack(pady=5)
        
    def _export_json(self, datos):
        """Exporta el diagnóstico a JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"diagnostico_{timestamp}.json"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=2, ensure_ascii=False)
                self._show_notification(f"✓ Reporte exportado: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
                
    def _export_txt(self, datos):
        """Exporta el diagnóstico a TXT"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"diagnostico_{timestamp}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 70 + "\n")
                    f.write("REPORTE DE DIAGNÓSTICO DE CONECTIVIDAD\n")
                    f.write("=" * 70 + "\n\n")
                    
                    f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Diagnóstico: {datos.get('diagnostico', 'N/A')}\n")
                    f.write(f"Severidad: {datos.get('severidad', 'N/A')}\n")
                    f.write(f"Gateway: {datos.get('gateway_ip', 'N/A')}\n\n")
                    
                    f.write("-" * 70 + "\n")
                    f.write("PARÁMETROS DE RED\n")
                    f.write("-" * 70 + "\n")
                    f.write(f"Conexión a Internet: {'✓' if datos.get('conexion') else '✗'}\n")
                    f.write(f"DNS Operativo: {'✓' if datos.get('dns') else '✗'}\n")
                    f.write(f"Gateway Accesible: {'✓' if datos.get('gateway') else '✗'}\n")
                    f.write(f"Latencia: {datos.get('latencia_ms', 0):.1f} ms\n")
                    f.write(f"Pérdida de Paquetes: {datos.get('perdida_pct', 0):.1f}%\n")
                    f.write(f"Puerto HTTP (80): {'✓' if datos.get('puertos_http') else '✗'}\n")
                    f.write(f"Puerto HTTPS (443): {'✓' if datos.get('puertos_https') else '✗'}\n\n")
                    
                    f.write("-" * 70 + "\n")
                    f.write("PASOS RECOMENDADOS\n")
                    f.write("-" * 70 + "\n\n")
                    
                    for i, paso in enumerate(datos.get('pasos', []), 1):
                        f.write(f"{i}. {paso.get('title', 'Sin título')}\n")
                        f.write(f"   {paso.get('detalle', '')}\n\n")
                        
                        for linea in paso.get('paso_a_paso', []):
                            f.write(f"   {linea}\n")
                        f.write("\n")
                        
                    f.write("=" * 70 + "\n")
                    
                self._show_notification(f"✓ Reporte exportado: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
    
    # =====================================================
    # NOTIFICACIONES
    # =====================================================
    def _show_notification(self, message):
        """Muestra una notificación temporal"""
        notification = tk.Toplevel(self)
        notification.overrideredirect(True)
        notification.configure(bg=COLORS['accent'])
        
        # Contenido
        frame = tk.Frame(notification, bg=COLORS['accent'])
        frame.pack(padx=2, pady=2)
        
        inner = tk.Frame(frame, bg=COLORS['bg_medium'])
        inner.pack(padx=15, pady=10)
        
        tk.Label(
            inner,
            text=message,
            font=('Segoe UI', 10, 'bold'),
            fg=COLORS['text'],
            bg=COLORS['bg_medium']
        ).pack()
        
        # Posicionar en la esquina superior derecha
        notification.update_idletasks()
        width = notification.winfo_width()
        height = notification.winfo_height()
        x = self.winfo_x() + self.winfo_width() - width - 20
        y = self.winfo_y() + 80
        notification.geometry(f"+{x}+{y}")
        
        # Auto-destruir después de 3 segundos
        notification.after(3000, notification.destroy)


# =====================================================
# FUNCIÓN PRINCIPAL
# =====================================================
def main():
    """Función principal de la aplicación"""
    app = ModernApp()
    app.mainloop()


if __name__ == "__main__":
    main()
