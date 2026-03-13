"""
RS DataExtractor- Desktop GUI
Refactorización Estética Total (Estilo Dashboard RS)
"""
import customtkinter as ctk
import os
import re
import sqlite3
import pyperclip
import json
import threading
import asyncio
import time
from tkinter import filedialog, messagebox, ttk
from typing import List, Dict, Any, Optional
from src.desktop.config import AppConfig
from src.desktop.logic import ExtractionLogic
from src.desktop.logic.crawler import CrawlerRecursivo

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Window Setup
        self.title(f"{AppConfig.APP_NAME} {AppConfig.VERSION}")
        self.geometry("1300x850")
        self.minsize(1000, 700)
        self.configure(fg_color=AppConfig.BG_MAIN)
        ctk.set_appearance_mode("dark")
        
        # 2. Asyncio Loop Persistence
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.loop_thread.start()
        
        # 3. Initialize Logic
        self.logic = ExtractionLogic()
        self.last_target_id = None

        # 4. Layout Configuration
        # Column 0: Sidebar (Minimalist)
        # Column 1: Main Content Area
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.filter_btns = []
        self.footer_btns = []
        self._setup_styles()
        self._setup_ui()
        self._load_history()
        self._toggle_action_buttons("disabled")

    def _setup_styles(self):
        """Configure ttk styles for Treeview with subtle grid"""
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview",
            background=AppConfig.BG_INPUT,
            foreground=AppConfig.TEXT_LIGHT,
            fieldbackground=AppConfig.BG_INPUT,
            borderwidth=0,
            font=AppConfig.FONT_MAIN,
            rowheight=35
        )
        style.map("Treeview",
            background=[('selected', AppConfig.RS_ORANGE)],
            foreground=[('selected', AppConfig.TEXT_WHITE)]
        )
        
        style.configure("Treeview.Heading",
            background=AppConfig.BG_SIDEBAR,
            foreground=AppConfig.RS_ORANGE,
            font=AppConfig.FONT_HEADER,
            relief="flat"
        )

    def _setup_ui(self):
        # --- SIDEBAR (Minimalist RS Style) ---
        self.sidebar = ctk.CTkFrame(self, width=80, fg_color=AppConfig.BG_SIDEBAR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo / Top Icon
        ctk.CTkLabel(self.sidebar, text="RS", font=("Inter", 24, "bold"), text_color=AppConfig.RS_ORANGE).pack(pady=30)
        
        self.nav_btns = {}
        self.nav_btns["Extracción"] = self._create_nav_btn("🕵️", "Extracción", active=True)
        self.nav_btns["Historial"] = self._create_nav_btn("📜", "Historial")
        self.nav_btns["Configuración"] = self._create_nav_btn("⚙️", "Configuración")

        # --- MAIN CONTAINER ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # View Dictionary
        self.views = {}
        self._setup_extraction_view()
        self._setup_history_view()
        self._setup_config_view()
        
        self.current_view = "Extracción"
        self.views["Extracción"].pack(fill="both", expand=True)

    def _setup_extraction_view(self):
        view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.views["Extracción"] = view
        
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(1, weight=1)

        # --- TOP: KPI DASHBOARD (3 Tarjetas) ---
        self.kpi_container = ctk.CTkFrame(view, fg_color="transparent")
        self.kpi_container.grid(row=0, column=0, sticky="ew", pady=(0, 30))
        self.kpi_container.grid_columnconfigure((0, 1, 2), weight=1)

        self.kpi_reg = self._create_kpi_card(self.kpi_container, AppConfig.ICON_REGISTROS, "REGISTROS", "0", 0)
        self.kpi_pipe = self._create_kpi_card(self.kpi_container, AppConfig.ICON_PIPELINE, "TIPO DETECTADO", "IDLE", 1)
        self.kpi_status = self._create_kpi_card(self.kpi_container, AppConfig.ICON_STATUS, "ESTADO SISTEMA", "READY", 2)

        # --- BODY: PANEL DUAL DE INGENIERÍA ---
        self.body_container = ctk.CTkFrame(view, fg_color="transparent")
        self.body_container.grid(row=1, column=0, sticky="nsew")
        self.body_container.grid_columnconfigure(0, weight=4) # Izquierda (Smart Input)
        self.body_container.grid_columnconfigure(1, weight=6) # Derecha (Smart Table)
        self.body_container.grid_rowconfigure(0, weight=1)

        # LADO IZQUIERDO: Smart Input & Controls
        self.left_panel = ctk.CTkFrame(self.body_container, fg_color=AppConfig.BG_CARD, corner_radius=AppConfig.RADIUS)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Header Smart Input
        left_header = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        left_header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(left_header, text=f"{AppConfig.ICON_INPUT} SMART INPUT", font=AppConfig.FONT_HEADER, text_color=AppConfig.RS_ORANGE).pack(side="left")
        ctk.CTkButton(left_header, text="Cargar Archivo", font=AppConfig.FONT_BOLD, width=100, height=28, fg_color=AppConfig.BG_SIDEBAR, command=self._load_file).pack(side="right")

        # Smart Input Textbox
        self.text_input = ctk.CTkTextbox(self.left_panel, fg_color=AppConfig.BG_INPUT, border_width=1, border_color="#2D3142", font=AppConfig.FONT_MAIN, corner_radius=10)
        self.text_input.pack(fill="both", expand=True, padx=20, pady=10)
        self.text_input.bind("<KeyRelease>", self._on_text_change)

        # Botón Flotante URL (Inicialmente oculto)
        self.url_float_btn = ctk.CTkButton(self.left_panel, text="🌐 URL Detectada. ¿Descargar contenido?", font=AppConfig.FONT_BOLD, fg_color="#3B82F6", hover_color="#2563EB", height=35, command=self._handle_url_detection)
        
        # Filtros Rápidos (Iconos de liderazgo)
        filter_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=10)
        self._create_filter_icon(filter_frame, "@", "Emails")
        self._create_filter_icon(filter_frame, "🔗", "URLs")
        self._create_filter_icon(filter_frame, "📞", "Teléfonos")
        self._create_filter_icon(filter_frame, "🌍", "IPs")
        self._create_filter_icon(filter_frame, "📅", "Fechas")

        # Modo y Recursive
        settings_frame = ctk.CTkFrame(self.left_panel, fg_color=AppConfig.BG_SIDEBAR, corner_radius=10)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        self.extract_type_var = ctk.StringVar(value="Auto")
        self.extract_dropdown = ctk.CTkOptionMenu(
            settings_frame, 
            values=["Auto", "OSINT Full", "SQLi Probe", "Emails", "URLs"], 
            variable=self.extract_type_var, 
            fg_color=AppConfig.BG_INPUT, 
            button_color=AppConfig.RS_ORANGE, 
            button_hover_color=AppConfig.RS_ORANGE_DARK,
            font=AppConfig.FONT_BOLD
        )
        self.extract_dropdown.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.crawler_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(settings_frame, text="Recursive", variable=self.crawler_var, font=AppConfig.FONT_BOLD, fg_color=AppConfig.RS_ORANGE, border_color=AppConfig.RS_ORANGE).pack(side="right", padx=10)

        # Espaciador final para empujar todo hacia arriba
        ctk.CTkLabel(self.left_panel, text="", height=1).pack(fill="y", expand=True)

        # LADO DERECHO: Smart Table
        self.right_panel = ctk.CTkFrame(self.body_container, fg_color=AppConfig.BG_CARD, corner_radius=AppConfig.RADIUS)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        
        # Header Smart Table
        right_header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        right_header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(right_header, text=f"{AppConfig.ICON_TABLE} ANÁLISIS DE DATOS", font=AppConfig.FONT_HEADER, text_color=AppConfig.RS_ORANGE).pack(side="left")

        # Treeview / Smart Table
        self.table_container = ctk.CTkFrame(self.right_panel, fg_color=AppConfig.BG_INPUT, corner_radius=10)
        self.table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.tree = ttk.Treeview(self.table_container, columns=("ID", "Valor"), show="headings", selectmode="browse")
        self.tree.heading("ID", text="#")
        self.tree.heading("Valor", text="Evidencia / Resultados")
        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Valor", width=500, anchor="w")
        
        self.scrollbar = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Footer Actions
        self.footer = ctk.CTkFrame(view, fg_color="transparent")
        self.footer.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        
        # Izquierda: Main Action
        self.main_action_frame = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.main_action_frame.pack(side="left", fill="x", expand=True)
        
        self.btn_analyze = ctk.CTkButton(self.main_action_frame, text=f"{AppConfig.ICON_PLAY} INICIAR PIPELINE", font=("Inter", 16, "bold"), fg_color=AppConfig.RS_ORANGE, hover_color=AppConfig.RS_ORANGE_DARK, height=50, width=250, command=self._start_pipeline)
        self.btn_analyze.pack(anchor="center")

        # Derecha: Secondary Actions
        self.secondary_actions_frame = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.secondary_actions_frame.pack(side="right")

        self.btn_stop = ctk.CTkButton(
              self.secondary_actions_frame, 
              text=f"{AppConfig.ICON_STOP}", 
              font=("Inter", 16, "bold"), 
              fg_color="#374151", 
              hover_color="#EF4444", 
              border_width=2,
              border_color="#EF4444",
              width=50, 
              height=40, 
              command=self._stop_pipeline
          )
        self.btn_stop.pack(side="left", padx=5)

        self.btn_copy = self._create_footer_btn(self.secondary_actions_frame, f"{AppConfig.ICON_COPY} COPIAR", self._copy_results)
        self.btn_export = self._create_footer_btn(self.secondary_actions_frame, f"{AppConfig.ICON_EXPORT} EXPORTAR", self._export_data)
        self.btn_report = self._create_footer_btn(self.secondary_actions_frame, f"{AppConfig.ICON_REPORT} REPORTE TXT", self._generate_report)

    def _setup_history_view(self):
        view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.views["Historial"] = view
        
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(view, text=f"{AppConfig.ICON_REGISTROS} HISTORIAL DE EXTRACCIONES", font=AppConfig.FONT_HEADER, text_color=AppConfig.RS_ORANGE).grid(row=0, column=0, pady=(0, 20), sticky="w")
        
        # Table container
        history_container = ctk.CTkFrame(view, fg_color=AppConfig.BG_INPUT, corner_radius=10)
        history_container.grid(row=1, column=0, sticky="nsew")
        
        self.history_table = ttk.Treeview(history_container, columns=("ID", "Target", "Tipo", "Fecha"), show="headings", selectmode="browse")
        self.history_table.heading("ID", text="#")
        self.history_table.heading("Target", text="Target / Input")
        self.history_table.heading("Tipo", text="Tipo de Datos")
        self.history_table.heading("Fecha", text="Fecha de Extracción")
        
        self.history_table.column("ID", width=50, anchor="center")
        self.history_table.column("Target", width=400, anchor="w")
        self.history_table.column("Tipo", width=150, anchor="center")
        self.history_table.column("Fecha", width=200, anchor="center")
        
        h_scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=self.history_table.yview)
        self.history_table.configure(yscrollcommand=h_scrollbar.set)
        
        self.history_table.pack(side="left", fill="both", expand=True)
        h_scrollbar.pack(side="right", fill="y")
        
        self.history_table.bind("<<TreeviewSelect>>", self._on_history_select)

        # Footer for history actions
        history_footer = ctk.CTkFrame(view, fg_color="transparent")
        history_footer.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        
        ctk.CTkButton(history_footer, text="RESTAURAR SELECCIÓN", font=AppConfig.FONT_BOLD, fg_color=AppConfig.RS_ORANGE, hover_color=AppConfig.RS_ORANGE_DARK, height=40, command=self._restore_history_item).pack(side="left")
        ctk.CTkButton(history_footer, text="LIMPIAR TODO", font=AppConfig.FONT_BOLD, fg_color="#374151", hover_color="#EF4444", height=40, command=self._clear_history).pack(side="right")

    def _setup_config_view(self):
        view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.views["Configuración"] = view
        
        view.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(view, text=f"{AppConfig.ICON_REPORT} CONFIGURACIÓN DEL SISTEMA", font=AppConfig.FONT_HEADER, text_color=AppConfig.RS_ORANGE).grid(row=0, column=0, pady=(0, 20), sticky="w")
        
        # Scrollable container for settings
        scroll_frame = ctk.CTkScrollableFrame(view, fg_color="transparent")
        scroll_frame.grid(row=1, column=0, sticky="nsew")
        view.grid_rowconfigure(1, weight=1)

        # --- SECCIÓN: SCRAPING ---
        self._create_config_section(scroll_frame, "Scraping & Performance", [
            ("Headless Mode", "scraping", "headless", "switch"),
            ("Max Threads", "scraping", "max_threads", "entry"),
            ("Timeout (s)", "scraping", "timeout", "entry"),
        ])

        # --- SECCIÓN: PROXIES ---
        self._create_config_section(scroll_frame, "Proxies & Seguridad", [
            ("Rotar Proxies", "proxies", "rotar", "switch"),
            ("Archivo de Proxies", "proxies", "archivo", "entry"),
        ])

        # --- SECCIÓN: OSINT ---
        self._create_config_section(scroll_frame, "OSINT Settings", [
            ("Breach Check", "osint", "breach_check", "switch"),
            ("Max Subdominios", "osint", "max_subdominios", "entry"),
        ])

    def _create_config_section(self, parent, title, settings):
        frame = ctk.CTkFrame(parent, fg_color=AppConfig.BG_CARD, corner_radius=10)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text=title, font=AppConfig.FONT_BOLD, text_color=AppConfig.RS_ORANGE).pack(anchor="w", padx=20, pady=10)
        
        for label, section, key, widget_type in settings:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(row, text=label, font=AppConfig.FONT_MAIN).pack(side="left")
            
            current_val = self.logic.config.get(section, key)
            
            if widget_type == "switch":
                var = ctk.BooleanVar(value=current_val)
                widget = ctk.CTkSwitch(row, text="", variable=var, command=lambda s=section, k=key, v=var: self.logic.config.set(s, k, v.get()))
                widget.pack(side="right")
            elif widget_type == "entry":
                widget = ctk.CTkEntry(row, width=100, fg_color=AppConfig.BG_INPUT)
                widget.insert(0, str(current_val))
                widget.pack(side="right")
                # Bind focus out to save
                widget.bind("<FocusOut>", lambda e, s=section, k=key, w=widget: self.logic.config.set(s, k, w.get()))

    # --- UI HELPERS ---
    def _create_nav_btn(self, icon, text, active=False):
        color = AppConfig.BG_CARD if active else "transparent"
        btn = ctk.CTkButton(self.sidebar, text=icon, font=("Inter", 20), width=50, height=50, fg_color=color, hover_color=AppConfig.BG_CARD, command=lambda: self._on_nav_click(text))
        btn.pack(pady=10)
        return btn

    def _on_nav_click(self, text):
        for name, btn in self.nav_btns.items():
            btn.configure(fg_color=AppConfig.BG_CARD if name == text else "transparent")
        
        # Hide current view
        if self.current_view in self.views:
            self.views[self.current_view].pack_forget()
        
        # Show new view
        self.current_view = text
        if text in self.views:
            self.views[text].pack(fill="both", expand=True)

    def _create_kpi_card(self, parent, icon, title, value, col):
        card = ctk.CTkFrame(parent, fg_color=AppConfig.BG_CARD, corner_radius=AppConfig.RADIUS)
        card.grid(row=0, column=col, sticky="nsew", padx=10)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True)
        
        val_lbl = ctk.CTkLabel(inner, text=f"{icon} {value}", font=AppConfig.FONT_KPI, text_color=AppConfig.RS_ORANGE)
        val_lbl.pack()
        
        ctk.CTkLabel(inner, text=title, font=AppConfig.FONT_MAIN, text_color=AppConfig.TEXT_MUTED).pack()
        return val_lbl

    def _create_filter_icon(self, parent, icon, label):
        btn = ctk.CTkButton(parent, text=icon, width=40, height=40, corner_radius=20, fg_color=AppConfig.BG_SIDEBAR, hover_color=AppConfig.RS_ORANGE, state="disabled")
        btn.pack(side="left", padx=5)
        self.filter_btns.append(btn)
        return btn

    def _create_footer_btn(self, parent, text, cmd):
        btn = ctk.CTkButton(parent, text=text, font=AppConfig.FONT_BOLD, fg_color=AppConfig.BG_CARD, hover_color=AppConfig.BG_SIDEBAR, width=150, height=40, command=cmd, state="disabled")
        btn.pack(side="right", padx=10)
        self.footer_btns.append(btn)
        return btn

    # --- REACTIVE LOGIC ---
    def _on_text_change(self, event=None):
        text = self.text_input.get("1.0", "end-1c").strip()
        if not text:
            self.url_float_btn.pack_forget()
            self._toggle_action_buttons("disabled")
            self.kpi_pipe.configure(text=f"{AppConfig.ICON_PIPELINE} IDLE")
            return

        input_type = self.logic.detectar_input(text)
        self.kpi_pipe.configure(text=f"{AppConfig.ICON_PIPELINE} {input_type}")
        self._toggle_action_buttons("normal")
        
        if input_type == "URL":
            self.url_float_btn.pack(fill="x", padx=20, pady=10, after=self.text_input)
        else:
            self.url_float_btn.pack_forget()

    def _handle_url_detection(self):
        self.extract_type_var.set("Auto")
        self._start_pipeline()

    def _toggle_action_buttons(self, state):
        for btn in self.filter_btns:
            btn.configure(state=state)
        for btn in self.footer_btns:
            btn.configure(state=state)
        # Ensure btn_analyze is only enabled if there's text
        text = self.text_input.get("1.0", "end-1c").strip()
        if not text and state == "normal":
            self.btn_analyze.configure(state="disabled")
        else:
            self.btn_analyze.configure(state=state)

    def _start_pipeline(self):
        text = self.text_input.get("1.0", "end-1c").strip()
        if not text: return
        
        self.btn_analyze.configure(state="disabled")
        self.btn_stop.configure(state="normal", fg_color="#EF4444")
        self.kpi_status.configure(text=f"{AppConfig.ICON_STATUS} RUNNING", text_color=AppConfig.WARNING)
        start_time = time.time()

        def pipeline_wrapper():
            try:
                extract_type = self.extract_type_var.get()
                input_type = self.logic.detectar_input(text)
                all_results = set()

                if extract_type == "SQLi Probe" and input_type == "URL":
                    future = self._run_async(self.logic.run_sqli_pipeline(text))
                    sqli_results = future.result()
                    formatted = [f"[SQLi] {r['valor']}" for r in sqli_results]
                    all_results.update(formatted)

                elif extract_type == "OSINT Full" and input_type == "URL":
                    future = self._run_async(self.logic.run_osint_pipeline(text))
                    osint_results = future.result()
                    all_results.update([f"[{r['tipo']}] {r['valor']}" for r in osint_results])

                else:
                    processed = text
                    if input_type == "URL":
                        res = self.logic.scrape_with_playwright(text)
                        processed = res.get("text", "")
                    all_results.update(self.logic.extract_from_text(processed, extract_type))

                results = sorted(list(all_results))
                elapsed = round(time.time() - start_time, 1)
                
                if results:
                    tid = self.logic.save_to_sqlite(extract_type, results, text)
                    self.last_target_id = tid
                
                self.after(0, lambda: self._finalize_pipeline(results, elapsed))

            except Exception as e:
                self.after(0, lambda: self._finalize_pipeline([], 0, str(e)))

        self.logic.thread_manager.lanzar("extraction", pipeline_wrapper)

    def _run_async(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def _finalize_pipeline(self, results, elapsed=0, error=None):
        self.btn_analyze.configure(state="normal")
        self.btn_stop.configure(state="normal", fg_color="#374151")
        
        if error:
            self.kpi_status.configure(text=f"{AppConfig.ICON_STATUS} ERROR", text_color=AppConfig.ERROR)
            messagebox.showerror("Error", f"Fallo en el pipeline: {error}")
        else:
            self.kpi_status.configure(text=f"{AppConfig.ICON_STATUS} SUCCESS", text_color=AppConfig.SUCCESS)
            self.kpi_reg.configure(text=f"{AppConfig.ICON_REGISTROS} {len(results)}")
            self._update_table(results)
            self._toggle_action_buttons("normal")
            self._load_history()

    def _stop_pipeline(self):
        self.logic.thread_manager.cancelar_todo()
        self.kpi_status.configure(text=f"{AppConfig.ICON_STATUS} IDLE", text_color=AppConfig.RS_ORANGE)
        self.btn_analyze.configure(state="normal")
        self.btn_stop.configure(state="normal", fg_color="#374151")

    def _update_table(self, results):
        for item in self.tree.get_children(): self.tree.delete(item)
        for idx, val in enumerate(results, 1):
            self.tree.insert("", "end", values=(idx, val))

    def _load_file(self):
        path = filedialog.askopenfilename()
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.text_input.delete("1.0", "end")
                    self.text_input.insert("1.0", f.read())
                    self._on_text_change()
            except Exception as e: messagebox.showerror("Error", str(e))

    def _load_history(self):
        """Carga los últimos 20 registros de la base de datos"""
        for item in self.history_table.get_children():
            self.history_table.delete(item)
            
        try:
            with sqlite3.connect(self.logic.db.db_path) as conn:
                targets = conn.execute("SELECT id, input_raw, tipo, fecha FROM targets ORDER BY fecha DESC LIMIT 20").fetchall()
            
            for t in targets:
                # Truncate input_raw for display
                display_input = (t[1][:50] + '...') if len(t[1]) > 50 else t[1]
                self.history_table.insert("", "end", values=(t[0], display_input, t[2], t[3]))
        except Exception as e:
            print(f"[ERROR] No se pudo cargar el historial: {e}")

    def _on_history_select(self, event):
        """Opcional: previsualizar resultados al seleccionar un item"""
        pass

    def _restore_history_item(self):
        """Restaura los resultados de un item del historial a la tabla principal"""
        selected = self.history_table.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un registro del historial.")
            return
            
        target_id = self.history_table.item(selected[0])['values'][0]
        
        try:
            with sqlite3.connect(self.logic.db.db_path) as conn:
                results = conn.execute("SELECT valor FROM results WHERE target_id = ?", (target_id,)).fetchall()
                target_data = conn.execute("SELECT input_raw, tipo FROM targets WHERE id = ?", (target_id,)).fetchone()
            
            if target_data:
                self.text_input.delete("1.0", "end")
                self.text_input.insert("1.0", target_data[0])
                self.extract_type_var.set(target_data[1])
                self._on_text_change()
                
            res_list = [r[0] for r in results]
            self._update_table(res_list)
            self.kpi_reg.configure(text=f"{AppConfig.ICON_REGISTROS} {len(res_list)}")
            
            # Cambiar a vista de extracción
            self._on_nav_click("Extracción")
            messagebox.showinfo("Éxito", f"Restaurados {len(res_list)} registros.")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar: {e}")

    def _clear_history(self):
        """Limpia el historial de la base de datos"""
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea borrar todo el historial?"):
            try:
                with sqlite3.connect(self.logic.db.db_path) as conn:
                    conn.execute("DELETE FROM results")
                    conn.execute("DELETE FROM targets")
                    conn.commit()
                self._load_history()
                messagebox.showinfo("Éxito", "Historial borrado.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo borrar: {e}")

    def _copy_results(self):
        if self.logic.results:
            pyperclip.copy("\n".join(self.logic.results))
            messagebox.showinfo("Copiado", "Resultados en portapapeles.")

    def _export_data(self):
        if not self.last_target_id: return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("JSON", "*.json"), ("Excel", "*.xlsx")])
        if path:
            try:
                if path.endswith(".csv"): self.logic.exporter.a_csv(self.last_target_id, path)
                elif path.endswith(".json"): self.logic.exporter.a_json(self.last_target_id, path)
                elif path.endswith(".xlsx"): self.logic.exporter.a_excel(self.last_target_id, path)
                messagebox.showinfo("Éxito", f"Exportado a {os.path.basename(path)}")
            except Exception as e: messagebox.showerror("Error", str(e))

    def _generate_report(self):
        if not self.last_target_id: return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Reporte", "*.txt")])
        if path:
            try:
                self.logic.exporter.generar_reporte_texto(self.last_target_id, path)
                os.startfile(path)
            except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = App()
    app.mainloop()
