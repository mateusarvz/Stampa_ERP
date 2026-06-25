from pathlib import Path
import csv
import json
import math
import os
import re
import shutil
import sys
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

import sqlite3
import textwrap
import traceback

# Load .env if available
if load_dotenv:
    try:
        load_dotenv()
    except Exception:
        pass

# Configure Gemini client if available and API key present
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        pass

APP_NAME = "Stampa_SaaS"


def get_app_data_dir():
    appdata_root = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home() / "AppData" / "Local")
    data_dir = Path(appdata_root) / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_resource_path(filename):
    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base_path = Path(__file__).resolve().parent
    return base_path / filename


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = get_app_data_dir()
CLIENTES_FILE = DATA_DIR / "CLIENTES.csv"
PEDIDOS_FILE = DATA_DIR / "PEDIDOS.csv"
ART_BASE_FOLDER = DATA_DIR / "PEDIDO_ARTES"
LOGO_PATH = get_resource_path("LOGO.ico")
TASKBAR_LOGO_PATH = get_resource_path("LOGO_BARRA DE TAREFAS.png")
CLIENTE_FIELDS = ["id_clientes", "ClienteEmpresa", "email", "telefone", "data_criação"]
PEDIDO_FIELDS = ["id_pedidos", "id_cliente", "cliente_empresa", "quantidade", "valor", "data", "descrição", "status"]
STATUS_OPTIONS = ["Aguardando aprovação", "Em andamento", "Finalizado", "Cancelado"]
# Gemini integration removed — AI features disabled per user request


def ensure_data_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ART_BASE_FOLDER.mkdir(parents=True, exist_ok=True)
    if not CLIENTES_FILE.exists():
        with CLIENTES_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CLIENTE_FIELDS)
            writer.writeheader()
    if not PEDIDOS_FILE.exists():
        with PEDIDOS_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PEDIDO_FIELDS)
            writer.writeheader()


def create_sqlite_db_from_csv(sqlite_path=None):
    sqlite_path = sqlite_path or (DATA_DIR / "stampa_data.db")
    sqlite_path = str(sqlite_path)
    conn = sqlite3.connect(sqlite_path)
    try:
        cur = conn.cursor()
        # create tables
        cur.execute(
            "CREATE TABLE IF NOT EXISTS clientes (id_clientes TEXT PRIMARY KEY, ClienteEmpresa TEXT, email TEXT, telefone TEXT, data_criacao TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS pedidos (id_pedidos TEXT PRIMARY KEY, id_cliente TEXT, cliente_empresa TEXT, quantidade INTEGER, valor REAL, data TEXT, descricao TEXT, status TEXT)"
        )
        conn.commit()
        # load CSVs
        if CLIENTES_FILE.exists():
            with CLIENTES_FILE.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = []
                for r in reader:
                    rows.append((r.get("id_clientes",""), r.get("ClienteEmpresa",""), r.get("email",""), r.get("telefone",""), r.get("data_criação","")))
                cur.execute("DELETE FROM clientes")
                cur.executemany("INSERT OR REPLACE INTO clientes (id_clientes, ClienteEmpresa, email, telefone, data_criacao) VALUES (?,?,?,?,?)", rows)
        if PEDIDOS_FILE.exists():
            with PEDIDOS_FILE.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = []
                for r in reader:
                    try:
                        qtd = int(float(str(r.get("quantidade","0")).replace(",",".")))
                    except Exception:
                        qtd = 0
                    try:
                        val = float(str(r.get("valor","0")).replace(",","."))
                    except Exception:
                        val = 0.0
                    rows.append((r.get("id_pedidos",""), r.get("id_cliente",""), r.get("cliente_empresa",""), qtd, val, r.get("data",""), r.get("descrição", r.get("descricao","")), r.get("status","")))
                cur.execute("DELETE FROM pedidos")
                cur.executemany("INSERT OR REPLACE INTO pedidos (id_pedidos, id_cliente, cliente_empresa, quantidade, valor, data, descricao, status) VALUES (?,?,?,?,?,?,?,?)", rows)
        conn.commit()
    finally:
        conn.close()


def run_sql_query(query, sqlite_path=None):
    sqlite_path = sqlite_path or (DATA_DIR / "stampa_data.db")
    sqlite_path = str(sqlite_path)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(query)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = [dict(row) for row in cur.fetchall()]
        return rows
    finally:
        conn.close()


def sanitize_filename(value):
    clean = re.sub(r"[^A-Za-z0-9 _-]", "", value or "")
    return re.sub(r"[\s]+", "_", clean.strip())


def format_currency(value):
    try:
        float_value = float(str(value).replace(",", "."))
        if float_value.is_integer():
            formatted = f"R$ {int(float_value):,}"
        else:
            formatted = f"R$ {float_value:,.2f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        try:
            return str(value)
        except Exception:
            return ""


def parse_currency(value):
    if value is None:
        return ""
    raw = str(value).strip()
    raw = raw.replace("R$", "").replace("r$", "").replace(" ", "")
    raw = re.sub(r"[^0-9,\.]+", "", raw)

    if "." in raw and "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    elif raw.count(".") > 1:
        parts = raw.split(".")
        raw = "".join(parts[:-1]) + "." + parts[-1]

    return raw


def split_cliente_empresa(cliente_empresa):
    parts = cliente_empresa.split(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return cliente_empresa, ""


def order_asset_folder(order_id):
    folder = ART_BASE_FOLDER / f"pedido_{order_id}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def open_order_folder(order_id):
    folder = ART_BASE_FOLDER / f"pedido_{order_id}"
    folder.mkdir(parents=True, exist_ok=True)
    os.startfile(folder)


def load_clients():
    ensure_data_files()
    clients = []
    with CLIENTES_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("id_clientes"):
                continue
            if not row.get("ClienteEmpresa"):
                nome = row.get("nome", "").strip()
                empresa = row.get("empresa", "").strip()
                row["ClienteEmpresa"] = f"{nome} - {empresa}".strip()
            row.pop("nome", None)
            row.pop("empresa", None)
            clients.append(row)
    return clients


def load_orders():
    ensure_data_files()
    with PEDIDOS_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        orders = [row for row in reader if row.get("id_pedidos")]
    updated = False
    for order in orders:
        if not order.get("data"):
            order["data"] = datetime.now().strftime("%Y-%m-%d")
            updated = True
    if updated:
        save_orders(orders)
    return orders


def save_clients(clients):
    with CLIENTES_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLIENTE_FIELDS)
        writer.writeheader()
        sanitized = [{k: v for k, v in client.items() if k in CLIENTE_FIELDS} for client in clients]
        writer.writerows(sanitized)
    # After saving CSV, update SQLite to keep DB in sync
    try:
        create_sqlite_db_from_csv()
    except Exception:
        # Do not raise to avoid breaking UI save flow; log to console
        import traceback

        traceback.print_exc()


def save_orders(orders):
    with PEDIDOS_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PEDIDO_FIELDS)
        writer.writeheader()
        sanitized = [ {k: v for k, v in order.items() if k in PEDIDO_FIELDS} for order in orders ]
        writer.writerows(sanitized)
    # After saving CSV, update SQLite to keep DB in sync
    try:
        create_sqlite_db_from_csv()
    except Exception:
        import traceback

        traceback.print_exc()


def next_id(items, key):
    # Gera próximo id numérico seguro mesmo se não houver ids válidos
    if not items:
        return "1"
    ids = []
    for item in items:
        val = item.get(key, "")
        if isinstance(val, int):
            ids.append(val)
        elif isinstance(val, str) and val.isdigit():
            try:
                ids.append(int(val))
            except Exception:
                continue
    if not ids:
        return "1"
    return str(max(ids) + 1)


class StampaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stampa SaaS - Gerenciador de Clientes e Pedidos")
        self.root.geometry("980x620")
        self.root.resizable(True, True)

        self.taskbar_icon = None
        if TASKBAR_LOGO_PATH.exists():
            try:
                self.taskbar_icon = tk.PhotoImage(file=str(TASKBAR_LOGO_PATH))
                self.root.iconphoto(True, self.taskbar_icon)
            except Exception:
                pass

        if LOGO_PATH.exists():
            try:
                self.root.iconbitmap(str(LOGO_PATH))
            except Exception:
                pass

        self.clients = []
        self.orders = []
        self.selected_client_id = None
        self.selected_order_id = None
        self.all_client_options = []
        # Default: sort orders by `id_pedidos` descending (latest first)
        self.order_sort_column = "id_pedidos"
        self.order_sort_reverse = True
        self.order_status_filter = tk.StringVar(value="Todos")

        # Gemini AI integration removed
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        self.root.configure(bg="#f7f6f6")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TNotebook", background="#f7f6f6", borderwidth=0)
        style.configure("TFrame", background="#f7f6f6")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabelframe", background="#ffffff", bordercolor="#dfd9d9", borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background="#ffffff", foreground="#222222", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background="#ffffff", foreground="#222222", font=("Segoe UI", 9))
        style.configure("TEntry", fieldbackground="#ffffff", background="#ffffff")
        style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff")
        style.configure("TButton", background="#d25d5d", foreground="#ffffff", borderwidth=0, focusthickness=3, focuscolor="#d25d5d")
        style.configure("Primary.TButton", background="#d25d5d", foreground="#ffffff", borderwidth=0, focusthickness=3, focuscolor="#d25d5d")
        style.map("Primary.TButton", background=[("active", "#b84747"), ("pressed", "#9b3636")])
        style.configure("Secondary.TButton", background="#ffffff", foreground="#2a2a2a", borderwidth=1, relief="solid")
        style.map("Secondary.TButton", background=[("active", "#f2f2f2"), ("pressed", "#e6e6e6")])
        style.configure("Subtle.TButton", background="#f7f6f6", foreground="#4a4a4a", borderwidth=0)
        style.map("Subtle.TButton", background=[("active", "#ececec"), ("pressed", "#e0e0e0")])
        style.configure("DeleteOrder.TButton", background="#d9d9d9", foreground="#2a2a2a", borderwidth=1, relief="solid")
        style.map("DeleteOrder.TButton", background=[("active", "#cfcfcf"), ("pressed", "#bfbfbf")])
        style.map("TButton", background=[("active", "#b84747"), ("pressed", "#9b3636")])
        style.configure("Treeview", rowheight=28, background="#ffffff", fieldbackground="#ffffff", bordercolor="#d4d4d4", borderwidth=1, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#2a2a2a", foreground="#ffffff", relief="flat")
        style.map("Treeview.Heading", background=[("active", "#444444")])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_orders = ttk.Frame(notebook)
        self.tab_clients = ttk.Frame(notebook)
        self.tab_dashboard = ttk.Frame(notebook)
        self.tab_ai_agent = ttk.Frame(notebook)
        self.tab_reports = ttk.Frame(notebook)
        notebook.add(self.tab_orders, text="Pedidos")
        notebook.add(self.tab_clients, text="Clientes")
        notebook.add(self.tab_dashboard, text="Dashboard")
        notebook.add(self.tab_ai_agent, text="Agente de IA")
        notebook.add(self.tab_reports, text="Relatórios com Gemini")

        self.create_orders_tab()
        self.create_clients_tab()
        self.create_dashboard_tab()
        self.create_ai_agent_tab()
        self.create_reports_tab()

    def create_clients_tab(self):
        frame_form = ttk.LabelFrame(self.tab_clients, text="Cadastro de Cliente", style="Card.TFrame")
        frame_form.pack(fill="x", padx=12, pady=10)

        form_inner = ttk.Frame(frame_form, style="Card.TFrame")
        form_inner.grid(row=0, column=0, sticky="ew", padx=20, pady=12)
        form_inner.columnconfigure(0, weight=1)
        form_inner.columnconfigure(1, weight=2)
        form_inner.columnconfigure(2, weight=1)
        form_inner.columnconfigure(3, weight=2)

        label_nome = ttk.Label(form_inner, text="Nome:")
        label_nome.grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.entry_nome = ttk.Entry(form_inner)
        self.entry_nome.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        label_empresa = ttk.Label(form_inner, text="Empresa:")
        label_empresa.grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.entry_empresa = ttk.Entry(form_inner)
        self.entry_empresa.grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        label_email = ttk.Label(form_inner, text="Email:")
        label_email.grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.entry_email = ttk.Entry(form_inner)
        self.entry_email.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        label_telefone = ttk.Label(form_inner, text="Telefone:")
        label_telefone.grid(row=1, column=2, padx=6, pady=6, sticky="e")
        self.entry_telefone = ttk.Entry(form_inner)
        self.entry_telefone.grid(row=1, column=3, padx=6, pady=6, sticky="ew")

        button_add = ttk.Button(form_inner, text="Adicionar cliente", command=self.add_client, style="Primary.TButton")
        button_add.grid(row=2, column=0, columnspan=4, padx=6, pady=(14, 6), sticky="ew")

        button_update = ttk.Button(form_inner, text="Atualizar cliente", command=self.update_client, style="Secondary.TButton")
        button_update.grid(row=3, column=1, padx=6, pady=6, sticky="ew")

        button_clear = ttk.Button(form_inner, text="Limpar campos", command=self.clear_client_form, style="Secondary.TButton")
        button_clear.grid(row=3, column=2, padx=6, pady=6, sticky="ew")

        button_delete = ttk.Button(form_inner, text="Excluir cliente", command=self.delete_client, style="Subtle.TButton")
        button_delete.grid(row=3, column=3, padx=6, pady=6, sticky="ew")

        frame_table = ttk.Frame(self.tab_clients)
        frame_table.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        columns = CLIENTE_FIELDS
        self.tree_clients = ttk.Treeview(frame_table, columns=columns, show="headings", selectmode="browse", height=14)
        for column in columns:
            heading = "Cliente / Empresa" if column == "ClienteEmpresa" else column.replace("_", " ").title()
            self.tree_clients.heading(column, text=heading)
            self.tree_clients.column(column, width=180 if column == "ClienteEmpresa" else 120, anchor="w" if column == "ClienteEmpresa" else "center")
        self.tree_clients.pack(side="left", fill="both", expand=True)

        self.tree_clients.bind("<<TreeviewSelect>>", self.on_client_select)

        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree_clients.yview)
        self.tree_clients.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def create_orders_tab(self):
        frame_form = ttk.LabelFrame(self.tab_orders, text="Cadastro e edição de pedidos")
        frame_form.pack(fill="x", padx=12, pady=10)

        label_cliente = ttk.Label(frame_form, text="Cliente:")
        label_cliente.grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.combo_cliente = ttk.Combobox(frame_form, values=[], state="normal", width=36)
        self.combo_cliente.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        self.combo_cliente.bind("<KeyRelease>", self.filter_client_options)
        self.combo_cliente.bind("<FocusIn>", lambda _: self.update_client_options())

        label_quantidade = ttk.Label(frame_form, text="Quantidade:")
        label_quantidade.grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.entry_quantidade = ttk.Entry(frame_form, width=18)
        self.entry_quantidade.grid(row=0, column=3, padx=6, pady=6, sticky="w")

        label_valor = ttk.Label(frame_form, text="Valor (R$):")
        label_valor.grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.entry_valor = ttk.Entry(frame_form, width=18)
        self.entry_valor.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        label_status = ttk.Label(frame_form, text="Status:")
        label_status.grid(row=1, column=2, padx=6, pady=6, sticky="e")
        self.combo_status = ttk.Combobox(frame_form, values=STATUS_OPTIONS, state="readonly", width=34)
        self.combo_status.grid(row=1, column=3, padx=6, pady=6, sticky="w")
        self.combo_status.set(STATUS_OPTIONS[0])

        label_descricao = ttk.Label(frame_form, text="Descrição:")
        label_descricao.grid(row=2, column=0, padx=6, pady=6, sticky="ne")
        self.text_descricao = tk.Text(frame_form, width=87, height=4)
        self.text_descricao.grid(row=2, column=1, columnspan=3, padx=6, pady=6, sticky="w")

        button_add = ttk.Button(frame_form, text="Adicionar pedido", command=self.add_order, style="Primary.TButton")
        button_add.grid(row=3, column=1, padx=6, pady=8, sticky="w")

        button_update = ttk.Button(frame_form, text="Atualizar pedido", command=self.update_order, style="Secondary.TButton")
        button_update.grid(row=3, column=2, padx=6, pady=8, sticky="w")

        button_clear = ttk.Button(frame_form, text="Limpar campos", command=self.clear_order_form, style="Secondary.TButton")
        button_clear.grid(row=3, column=3, padx=6, pady=8, sticky="w")

        button_open_folder = ttk.Button(frame_form, text="Abrir pasta do pedido", command=self.open_selected_order_folder, style="Secondary.TButton")
        button_open_folder.grid(row=4, column=0, padx=6, pady=8, sticky="w")

        self.order_folder_label = ttk.Label(frame_form, text="Pasta de imagens: -")
        self.order_folder_label.grid(row=5, column=0, columnspan=4, padx=6, pady=(2, 0), sticky="w")

        frame_table = ttk.Frame(self.tab_orders)
        frame_table.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        frame_table.columnconfigure(0, weight=1)
        frame_table.rowconfigure(1, weight=1)

        filter_frame = ttk.Frame(frame_table)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        filter_frame.columnconfigure(1, weight=1)

        label_filter_status = ttk.Label(filter_frame, text="Filtrar status:")
        label_filter_status.grid(row=0, column=0, padx=6, pady=2, sticky="e")
        self.combo_order_status_filter = ttk.Combobox(
            filter_frame,
            values=["Todos"] + STATUS_OPTIONS,
            state="readonly",
            width=24,
            textvariable=self.order_status_filter,
        )
        self.combo_order_status_filter.grid(row=0, column=1, padx=6, pady=2, sticky="w")
        self.combo_order_status_filter.bind("<<ComboboxSelected>>", lambda event: self.refresh_orders_view())

        tree_container = ttk.Frame(frame_table)
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        columns = PEDIDO_FIELDS
        self.tree_orders = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="browse", height=14)
        for column in columns:
            self.tree_orders.heading(
                column,
                text=self.get_order_heading_text(column),
                command=lambda c=column: self.sort_orders(c),
            )
            self.tree_orders.column(column, width=150, anchor="center", minwidth=100)
        self.tree_orders.column("id_cliente", width=100, anchor="center")
        self.tree_orders.column("cliente_empresa", width=260, anchor="w")
        self.tree_orders.column("data", width=170, anchor="center")
        self.tree_orders.column("descrição", width=320, anchor="w")
        self.tree_orders.column("status", width=140, anchor="center")
        self.tree_orders.grid(row=0, column=0, sticky="nsew")

        scrollbar_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree_orders.yview)
        scrollbar_x = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree_orders.xview)
        self.tree_orders.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.tree_orders.tag_configure("Aguardando aprovação", background="#f0f0f0", foreground="#000000")
        self.tree_orders.tag_configure("Em andamento", background="#fff2cc", foreground="#000000")
        self.tree_orders.tag_configure("Finalizado", background="#dff0d8", foreground="#000000")
        self.tree_orders.tag_configure("Cancelado", background="#f8d7da", foreground="#7a0b0f")

        self.tree_orders.bind("<<TreeviewSelect>>", self.on_order_select)

        delete_button_frame = ttk.Frame(frame_table)
        delete_button_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        delete_button_frame.columnconfigure(0, weight=1)

        button_delete = ttk.Button(
            delete_button_frame,
            text="Excluir Pedido",
            command=self.delete_order,
            style="DeleteOrder.TButton",
            width=20,
        )
        button_delete.pack(side="right", padx=12, pady=(0, 4))

    def load_data(self):
        self.clients = load_clients()
        self.orders = load_orders()
        
        self.normalize_orders()
        self.refresh_clients_view()
        self.refresh_orders_view()
        self.update_client_options()
        if hasattr(self, "dashboard_select_all_var"):
            self.refresh_dashboard()
        if hasattr(self, "report_year_frame"):
            self.update_report_year_options()

    def update_report_year_options(self):
        """Atualiza os anos disponíveis no frame de relatórios com base nos dados do banco"""
        available_years = set()
        for client in self.clients:
            dt_str = client.get("data_criação")
            if dt_str:
                try:
                    yr = datetime.strptime(dt_str, "%Y-%m-%d").year
                    available_years.add(yr)
                except Exception:
                    pass
        for order in self.orders:
            dt_str = order.get("data")
            if dt_str:
                try:
                    yr = datetime.strptime(dt_str, "%Y-%m-%d").year
                    available_years.add(yr)
                except Exception:
                    pass
        if not available_years:
            available_years = {datetime.now().year}
        
        sorted_years = sorted(list(available_years))
        
        # Salva seleções existentes para preservar se possível
        existing_selections = {}
        if hasattr(self, "report_year_vars") and self.report_year_vars:
            for y, var in self.report_year_vars.items():
                existing_selections[y] = var.get()
                
        # Limpa o frame
        for child in self.report_year_frame.winfo_children():
            child.destroy()
            
        self.report_year_vars = {}
        for yr in sorted_years:
            default_val = existing_selections.get(yr, 1 if yr == sorted_years[-1] else 0)
            var = tk.IntVar(value=default_val)
            self.report_year_vars[yr] = var
            cb = ttk.Checkbutton(self.report_year_frame, text=str(yr), variable=var)
            cb.pack(side="left", padx=(0, 8), pady=2)

    def create_dashboard_tab(self):
        self.dashboard_canvas = tk.Canvas(self.tab_dashboard, highlightthickness=0)
        self.dashboard_scrollbar = ttk.Scrollbar(self.tab_dashboard, orient="vertical", command=self.dashboard_canvas.yview)
        self.dashboard_canvas.configure(yscrollcommand=self.dashboard_scrollbar.set)
        self.dashboard_scrollbar.pack(side="right", fill="y")
        self.dashboard_canvas.pack(side="left", fill="both", expand=True)

        self.dashboard_inner_frame = ttk.Frame(self.dashboard_canvas)
        self.dashboard_inner_window = self.dashboard_canvas.create_window((0, 0), window=self.dashboard_inner_frame, anchor="nw")
        # Atualiza scrollregion quando o conteúdo interno muda
        self.dashboard_inner_frame.bind(
            "<Configure>",
            lambda event: self.dashboard_canvas.configure(scrollregion=self.dashboard_canvas.bbox("all")),
        )
        # Faz o frame interno expandir horizontalmente junto com o canvas
        self.dashboard_canvas.bind(
            "<Configure>",
            lambda event: self.dashboard_canvas.itemconfig(self.dashboard_inner_window, width=event.width),
        )

        frame_filters = ttk.LabelFrame(self.dashboard_inner_frame, text="Período de análise", style="Card.TFrame")
        frame_filters.pack(fill="x", padx=12, pady=10)
        frame_filters.columnconfigure(0, weight=1)
        frame_filters.columnconfigure(1, weight=1)
        frame_filters.columnconfigure(2, weight=1)
        frame_filters.columnconfigure(3, weight=1)
        frame_filters.columnconfigure(4, weight=1)
        frame_filters.columnconfigure(5, weight=1)

        self.dashboard_select_all_var = tk.BooleanVar(value=False)
        self.dashboard_year_vars = {}
        self.dashboard_year_checkbuttons = {}
        self.dashboard_month_from_var = tk.StringVar(value="Janeiro")
        self.dashboard_month_to_var = tk.StringVar(value="Dezembro")

        label_year_select = ttk.Label(frame_filters, text="Anos:")
        label_year_select.grid(row=0, column=0, padx=6, pady=10, sticky="e")
        self.dashboard_year_frame = ttk.Frame(frame_filters)
        self.dashboard_year_frame.grid(row=0, column=1, columnspan=2, sticky="w", padx=6, pady=10)

        self.dashboard_select_all_check = ttk.Checkbutton(
            frame_filters,
            text="Selecionar todo período",
            variable=self.dashboard_select_all_var,
            command=self.on_dashboard_select_all_changed,
        )
        self.dashboard_select_all_check.grid(row=1, column=0, columnspan=2, padx=6, pady=10, sticky="w")

        label_month_from = ttk.Label(frame_filters, text="De (mês):")
        label_month_from.grid(row=1, column=2, padx=6, pady=10, sticky="e")
        month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        self.dashboard_month_from_combo = ttk.Combobox(frame_filters, textvariable=self.dashboard_month_from_var, values=month_names, state="readonly", width=18)
        self.dashboard_month_from_combo.grid(row=1, column=3, padx=6, pady=10, sticky="w")
        self.dashboard_month_from_combo.bind("<<ComboboxSelected>>", lambda event: (self.update_dashboard_month_to_options(), self.refresh_dashboard()))

        label_month_to = ttk.Label(frame_filters, text="Até (mês):")
        label_month_to.grid(row=1, column=4, padx=6, pady=10, sticky="e")
        self.dashboard_month_to_combo = ttk.Combobox(frame_filters, textvariable=self.dashboard_month_to_var, values=month_names, state="readonly", width=18)
        self.dashboard_month_to_combo.grid(row=1, column=5, padx=6, pady=10, sticky="w")
        self.dashboard_month_to_combo.bind("<<ComboboxSelected>>", lambda event: self.refresh_dashboard())

        frame_summary = ttk.LabelFrame(self.dashboard_inner_frame, text="Visão Geral", style="Card.TFrame")
        frame_summary.pack(fill="x", padx=12, pady=10)
        frame_summary.columnconfigure(0, weight=1)
        frame_summary.columnconfigure(1, weight=1)
        frame_summary.columnconfigure(2, weight=1)
        frame_summary.columnconfigure(3, weight=1)

        self.dashboard_labels = {}
        metrics = [
            ("Receita total", "R$ 0,00"),
            ("Média por mês", "R$ 0,00"),
            ("Pedidos finalizados", "0"),
        ]
        for idx, (title, value) in enumerate(metrics):
            card = tk.Frame(frame_summary, bg="#ffffff", bd=1, relief="solid")
            card.grid(row=0, column=idx, padx=6, pady=10, sticky="nsew")
            card.columnconfigure(0, weight=1)
            title_label = tk.Label(card, text=title, bg="#ffffff", fg="#d25d5d", font=("Segoe UI", 9, "bold"))
            title_label.pack(anchor="w", padx=12, pady=(10, 2))
            value_label = tk.Label(card, text=value, bg="#ffffff", fg="#000000", font=("Segoe UI", 16, "bold"))
            value_label.pack(anchor="w", padx=12, pady=(0, 10))
            self.dashboard_labels[title] = value_label

        self.update_dashboard_month_to_options()

        self.dashboard_charts_row = ttk.Frame(self.dashboard_inner_frame)
        self.dashboard_charts_row.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        # Dar mais espaço para a coluna esquerda onde ficam os gráficos principais
        self.dashboard_charts_row.columnconfigure(0, weight=5)
        self.dashboard_charts_row.columnconfigure(1, weight=2)
        self.dashboard_charts_row.rowconfigure(0, weight=1)

        self.dashboard_charts_left = ttk.Frame(self.dashboard_charts_row)
        self.dashboard_charts_left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.dashboard_charts_right = ttk.Frame(self.dashboard_charts_row)
        self.dashboard_charts_right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.create_dashboard_revenue_chart()
        self.create_dashboard_orders_revenue_chart()
        self.create_dashboard_status_chart()
        self.create_dashboard_quantity_revenue_chart()
        self.refresh_dashboard()
        # Gemini prompt area
        gemini_frame = ttk.LabelFrame(self.dashboard_inner_frame, text="Agente Gemini (Dashboard)", style="Card.TFrame")
        gemini_frame.pack(fill="x", padx=12, pady=10)
        label = ttk.Label(gemini_frame, text="Prompt para análise de dados:")
        label.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.gemini_prompt_entry = tk.Text(gemini_frame, height=4)
        self.gemini_prompt_entry.grid(row=1, column=0, sticky="ew", padx=6, pady=6)
        send_btn = ttk.Button(gemini_frame, text="Executar Gemini", style="Primary.TButton", command=self.execute_gemini_prompt)
        send_btn.grid(row=1, column=1, padx=6, pady=6)
        self.gemini_output = tk.Text(gemini_frame, height=10, bg="#fafafa")
        self.gemini_output.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=6, pady=(6,12))
        gemini_frame.columnconfigure(0, weight=1)

    def create_dashboard_revenue_chart(self):
        frame_revenue = ttk.LabelFrame(self.dashboard_charts_left, text="Receita por ano", style="Card.TFrame")
        frame_revenue.pack(fill="both", expand=True, pady=(0, 10))
        self.dashboard_revenue_canvas = tk.Canvas(frame_revenue, height=220, bg="#ffffff", highlightthickness=0)
        self.dashboard_revenue_canvas.pack(fill="both", expand=True, padx=12, pady=12)
        self.dashboard_revenue_data = {"years": [], "months": [], "values": {}}
        self.dashboard_revenue_canvas.bind(
            "<Configure>",
            lambda event: self.draw_dashboard_revenue_chart(),
        )

    def create_ai_agent_tab(self):
        frame = ttk.LabelFrame(self.tab_ai_agent, text="Agente de IA", style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=12, pady=10)
        frame.columnconfigure(0, weight=1)

        label = ttk.Label(frame, text="Prompt para o Agente:")
        label.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.ai_prompt_text = tk.Text(frame, height=6)
        self.ai_prompt_text.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, sticky="e", padx=6, pady=6)
        send_btn = ttk.Button(btn_frame, text="Enviar", style="Primary.TButton", command=self.on_ai_agent_send)
        send_btn.pack(side="right")

        self.ai_agent_output = tk.Text(frame, height=12, bg="#fafafa")
        self.ai_agent_output.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 12))

    def create_reports_tab(self):
        """Create Reports with Gemini tab"""
        main_frame = ttk.Frame(self.tab_reports)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Gerar Relatório", style="Card.TFrame")
        control_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)
        
        # Descrição
        ttk.Label(control_frame, text="Descrição/Pedido:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.report_description_text = tk.Text(control_frame, height=3, width=40)
        self.report_description_text.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=6, pady=6)
        
        # Ano
        ttk.Label(control_frame, text="Anos:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.report_year_frame = ttk.Frame(control_frame)
        self.report_year_frame.grid(row=2, column=1, columnspan=2, sticky="w", padx=6, pady=6)
        self.report_year_vars = {}
        
        # Meses
        ttk.Label(control_frame, text="Meses:").grid(row=3, column=0, sticky="nw", padx=6, pady=6)
        months_frame = ttk.Frame(control_frame)
        months_frame.grid(row=3, column=1, columnspan=2, sticky="w", padx=6, pady=6)
        
        self.report_month_vars = {}
        months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        current_month = datetime.now().month
        
        for idx, month in enumerate(months):
            col = idx % 6
            row = idx // 6
            var = tk.BooleanVar(value=(idx + 1 == current_month))
            self.report_month_vars[idx + 1] = var
            cb = ttk.Checkbutton(months_frame, text=month, variable=var)
            cb.grid(row=row, column=col, sticky="w", padx=3, pady=2)
        
        # Botão Gerar
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, sticky="e", padx=6, pady=10)
        generate_btn = ttk.Button(
            btn_frame,
            text="Gerar Relatório",
            style="Primary.TButton",
            command=self.on_generate_report
        )
        generate_btn.pack(side="right", padx=5)
        
        # Status label
        self.report_status_label = ttk.Label(control_frame, text="", foreground="green")
        self.report_status_label.grid(row=4, column=0, columnspan=3, sticky="w", padx=6, pady=10)
        
        # Output area
        output_frame = ttk.LabelFrame(main_frame, text="Status", style="Card.TFrame")
        output_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(output_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.report_output = tk.Text(
            output_frame,
            height=15,
            bg="#fafafa",
            yscrollcommand=scrollbar.set
        )
        self.report_output.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.report_output.yview)

    def on_generate_report(self):
        """Handle report generation"""
        description = self.report_description_text.get("1.0", "end").strip()
        selected_years = [y for y, var in self.report_year_vars.items() if var.get()]
        months = [m for m, var in self.report_month_vars.items() if var.get()]
        
        if not description:
            messagebox.showwarning("Relatório", "Descreva o que você deseja no relatório.")
            return
            
        if not selected_years:
            messagebox.showwarning("Relatório", "Selecione pelo menos um ano.")
            return
        
        if not months:
            messagebox.showwarning("Relatório", "Selecione pelo menos um mês.")
            return
        
        self.report_output.delete("1.0", "end")
        self.report_status_label.config(text="Gerando... aguarde.", foreground="blue")
        self.root.update()
        
        try:
            self._generate_report_with_gemini(description, selected_years, months)
            self.report_status_label.config(text="✓ Relatório gerado com sucesso!", foreground="green")
        except Exception as e:
            self.report_status_label.config(text=f"✗ Erro: {str(e)}", foreground="red")
            self.report_output.delete("1.0", "end")
            self.report_output.insert("1.0", f"Erro ao gerar relatório:\n{str(e)}\n")

    def _generate_report_with_gemini(self, description, selected_years, months):
        """Generate report and open in browser"""
        create_sqlite_db_from_csv()
        
        # Build date range SQL
        year_list = ", ".join(str(y) for y in selected_years)
        month_list = ", ".join(str(m) for m in months)
        date_filter = f"CAST(strftime('%Y', data) AS INTEGER) IN ({year_list}) AND CAST(strftime('%m', data) AS INTEGER) IN ({month_list})"
        
        # Check comparison condition: 1 month and > 1 year
        is_comparison_mode = len(months) == 1 and len(selected_years) > 1
        comparison_instruction = ""
        if is_comparison_mode:
            comparison_instruction = f"""
IMPORTANTE: Como apenas um mês ({months}) foi selecionado para múltiplos anos ({selected_years}), o foco absoluto da sua análise e das suas queries SQL deve ser COMPARAR o desempenho deste mesmo mês entre os diferentes anos. Desenhe queries que tragam os dados agrupados ou segmentados por ano para viabilizar essa comparação direta.
"""

        # Step 1: Generate SQL queries via Gemini
        system_prompt = f"""Você é especialista em SQL e análise de negócios. Sua missão é gerar queries SQL para obter os dados necessários para o relatório solicitado pelo usuário.

Dê o máximo de poder de decisão ao Gemini para escolher quais análises e tabelas/gráficos são ideais para o pedido do usuário. A regra principal e guia absoluto do relatório é o PROMPT DO USUÁRIO.

Schema do Banco de Dados SQLite:
- clientes: id_clientes, ClienteEmpresa, email, telefone, data_criacao
- pedidos: id_pedidos, id_cliente, cliente_empresa, quantidade, valor, data, descricao, status

Filtro de data padrão a ser usado nas queries:
{date_filter}

Período Selecionado: Anos: {selected_years}, Meses (números): {months}
{comparison_instruction}

Regras:
1. Gere queries SQL válidas para SQLite.
2. Decida livremente quais e quantas queries são relevantes (até 4 queries) para responder perfeitamente ao prompt do usuário.
3. Para cada query, especifique no JSON retornado:
   - "sql": A query SQL correspondente.
   - "label": Título da análise (ex: "Ranking de Clientes por Faturamento").
   - "type": Tipo de exibição. Escolha "chart" (apenas gráfico), "table" (apenas tabela) ou "both" (gráfico e tabela). Escolha "chart" quando o gráfico sozinho for suficiente e claro, evitando tabelas redundantes com as mesmas informações.
   - "chart_type": O tipo de gráfico adequado para a análise. Escolha "bar" (barra), "line" (linha para evolução temporal), "pie" (pizza para distribuição de parcelas) ou "doughnut" (rosca).
   - "kpis": Uma lista com até 3 indicadores-chave relevantes para essa análise que serão mostrados como cards. Cada KPI deve ter:
     * "column": nome da coluna de resultado no SQL.
     * "label": título do card (ex: "Faturamento Médio").
     * "operation": a operação ("sum" para somar, "avg" para média, "count" para contagem de registros).
     * IMPORTANTE: Não crie KPIs para dados inúteis (como somar índices de meses, IDs de clientes ou contar linhas sem sentido analítico). Apenas inclua se agregar valor direto ao prompt do usuário.
4. Siga rigorosamente a instrução do usuário.

Responda APENAS com um objeto JSON válido, sem markdown ou explicações externas, no formato:
{{
  "queries": [
    {{
      "sql": "SELECT ...",
      "label": "Título da Análise",
      "type": "chart|table|both",
      "chart_type": "bar|line|pie|doughnut",
      "kpis": [
        {{"column": "nome_coluna", "label": "Total Vendas", "operation": "sum"}}
      ]
    }}
  ]
}}"""
        
        user_msg = f"""Gere queries SQL para o relatório estratégico com base no meu seguinte pedido: "{description}" """
        
        try:
            resp = self._call_genai(system_prompt, user_msg)
        except Exception as e:
            self.report_output.insert("1.0", f"Erro Gemini (queries): {str(e)}\n")
            return
        
        queries = []
        try:
            m = re.search(r"\{[\s\S]*\}", resp)
            if m:
                data = json.loads(m.group(0))
                queries = data.get("queries", [])
        except Exception:
            pass
        
        if not queries:
            self.report_output.insert("1.0", f"Erro: Não consegui gerar queries.\n{resp}\n")
            return
        
        # Step 2: Execute queries
        self.report_output.insert("1.0", "Coletando dados...\n")
        self.root.update()
        
        query_results = []
        for idx, q_item in enumerate(queries):
            sql = q_item.get("sql", "")
            label = q_item.get("label", f"Análise {idx+1}")
            display_type = q_item.get("type", "table")
            chart_style = q_item.get("chart_type", "bar")
            kpis = q_item.get("kpis", [])
            
            try:
                rows = run_sql_query(sql)
                query_results.append({
                    "label": label,
                    "data": rows,
                    "type": display_type,
                    "chart_type": chart_style,
                    "kpis": kpis,
                    "success": True
                })
            except Exception as e:
                self.report_output.insert("1.0", f"⚠ Erro em query: {label}\n")
        
        # Step 2.5: Generate Analysis/Insights via Gemini
        self.report_output.insert("end", "Analisando dados com inteligência artificial...\n")
        self.root.update()
        
        # Prepare data for Gemini prompt
        clean_results = []
        for r in query_results:
            if r.get("success") and r.get("data"):
                clean_results.append({
                    "label": r["label"],
                    "data": r["data"][:20]
                })
        
        analysis_data = {
            "resumo_executivo": "Não foi possível gerar a análise automática por inteligência artificial.",
            "principais_insights": ["Sem dados suficientes para análise estratégica."],
            "recomendacoes": ["Revise as vendas e pedidos no período selecionado."]
        }
        
        if clean_results:
            comparison_context = ""
            if is_comparison_mode:
                comparison_context = f"Foco Especial: Comparar o mês selecionado ({months}) entre os anos selecionados ({selected_years})."

            analysis_prompt = f"""Você é um analista de negócios e estrategista sênior. 
Você deve analisar os dados fornecidos abaixo e produzir um relatório estratégico em português.

A regra principal e diretriz absoluta para esta análise é atender ao seguinte pedido do usuário:
"{description}"

Período dos dados: Anos {selected_years}, meses {months}
{comparison_context}

Dados coletados do banco de dados:
{json.dumps(clean_results, ensure_ascii=False, indent=2)}

Regras de formatação:
- Responda em formato JSON contendo os seguintes campos:
  - "resumo_executivo": Um resumo profissional do que os dados revelam em relação ao pedido do usuário.
  - "principais_insights": Uma lista de 3 a 5 pontos com insights estratégicos baseados exclusivamente nos dados.
  - "recomendacoes": Recomendações práticas e acionáveis para o negócio baseadas nos insights.
- Evite jargões técnicos de banco de dados ou SQL.
- Foque em responder ao pedido do usuário usando métricas, tendências, crescimento, comportamento do cliente e saúde financeira.

Responda APENAS com o JSON no formato:
{{
  "resumo_executivo": "...",
  "principais_insights": [
    "...",
    "..."
  ],
  "recomendacoes": [
    "...",
    "..."
  ]
}}"""
            try:
                analysis_resp = self._call_genai("Você é um especialista em análise de negócios e geração de relatórios executivos.", analysis_prompt)
                m = re.search(r"\{[\s\S]*\}", analysis_resp)
                if m:
                    analysis_data = json.loads(m.group(0))
            except Exception as e:
                self.report_output.insert("end", f"⚠ Falha ao gerar análise de IA: {str(e)}\n")
                self.root.update()

        # Step 3: Generate HTML
        self.report_output.delete("1.0", "end")
        self.report_output.insert("1.0", "Gerando HTML profissional...\n")
        self.root.update()
        
        html_file = self._generate_html_report(
            description, selected_years, months, query_results, analysis_data
        )
        
        # Step 4: Open in browser
        self.report_output.insert("1.0", f"Abrindo relatório no navegador...\n")
        self.root.update()
        
        import webbrowser
        webbrowser.open(f"file:///{html_file}")
        
        self.report_output.delete("1.0", "end")
        self.report_output.insert("1.0", f"Relatório aberto em: {html_file}\n")

    def _generate_html_report(self, description, years, months, query_results, analysis_data=None):
        """Generate professional HTML report with charts"""
        from datetime import datetime
        import json
        
        # Mapping of month numbers to Portuguese names
        month_names_pt = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        month_labels_str = ", ".join(month_names_pt.get(m, str(m)) for m in months)
        years_str = ", ".join(str(y) for y in years)

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Inteligente IA</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Outfit', sans-serif;
            background: #f1f5f9;
            padding: 40px 20px;
            color: #1e293b;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }}
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-top: 6px solid #d25d5d;
            color: #ffffff;
            padding: 45px 40px;
            text-align: left;
            position: relative;
        }}
        .header h1 {{
            font-size: 2.25em;
            margin-bottom: 8px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
            margin-bottom: 20px;
            font-weight: 300;
            max-width: 800px;
            line-height: 1.5;
        }}
        .header .meta {{
            font-size: 0.85em;
            opacity: 0.8;
            margin-top: 15px;
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 15px;
        }}
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .content {{
            padding: 40px;
        }}
        
        /* AI Insights Section */
        .ai-analysis {{
            background: #ffffff;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            border-left: 6px solid #d25d5d;
        }}
        .ai-header h2 {{
            color: #0f172a;
            font-size: 1.4em;
            margin-bottom: 20px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .ai-summary {{
            margin-bottom: 25px;
            background: #f8fafc;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #64748b;
        }}
        .ai-summary h3 {{
            color: #475569;
            font-size: 0.95em;
            margin-bottom: 8px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .ai-summary p {{
            line-height: 1.6;
            color: #334155;
            font-size: 1em;
        }}
        .ai-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }}
        @media (max-width: 768px) {{
            .ai-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .ai-card {{
            background: #ffffff;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #f1f5f9;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }}
        .ai-card h3 {{
            font-size: 1.1em;
            margin-bottom: 15px;
            padding-bottom: 8px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .insights-card h3 {{
            color: #3b82f6;
            border-bottom: 2px solid #eff6ff;
        }}
        .recommendations-card h3 {{
            color: #10b981;
            border-bottom: 2px solid #ecfdf5;
        }}
        .ai-card ul {{
            list-style: none;
            padding-left: 0;
        }}
        .ai-card ul li {{
            position: relative;
            padding-left: 20px;
            margin-bottom: 12px;
            line-height: 1.5;
            color: #475569;
            font-size: 0.92em;
        }}
        .insights-card ul li::before {{
            content: "•";
            color: #3b82f6;
            font-size: 1.6em;
            position: absolute;
            left: 2px;
            top: -4px;
        }}
        .recommendations-card ul li::before {{
            content: "✓";
            color: #10b981;
            font-weight: 700;
            position: absolute;
            left: 2px;
            top: 1px;
        }}
        
        .section {{
            margin-bottom: 40px;
            background: #ffffff;
            padding: 30px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        .section h2 {{
            font-size: 1.4em;
            color: #0f172a;
            margin-bottom: 6px;
            font-weight: 700;
            letter-spacing: -0.3px;
        }}
        .section-desc {{
            color: #64748b;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        .chart-container {{
            position: relative;
            height: 350px;
            margin: 20px 0;
            background: #ffffff;
            padding: 12px;
            border-radius: 8px;
        }}
        
        /* Stats cards */
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-box {{
            padding: 20px;
            border-radius: 12px;
            text-align: left;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #d25d5d;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .stat-box:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        }}
        .stat-value {{
            font-size: 1.8em;
            font-weight: 700;
            color: #0f172a;
            margin-top: 4px;
            letter-spacing: -0.5px;
        }}
        .stat-label {{
            font-size: 0.8em;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        
        /* Tables */
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #ffffff;
            text-align: left;
            font-size: 0.9em;
        }}
        table thead {{
            background: #f8fafc;
        }}
        table th {{
            padding: 14px 20px;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid #e2e8f0;
            text-transform: uppercase;
            font-size: 0.75em;
            letter-spacing: 0.5px;
        }}
        table td {{
            padding: 12px 20px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
        }}
        table tbody tr:hover {{
            background: #f8fafc;
        }}
        
        .footer {{
            background: #f8fafc;
            padding: 24px;
            text-align: center;
            color: #94a3b8;
            font-size: 0.8em;
            border-top: 1px solid #edf2f7;
        }}
        .error {{
            background: #fef2f2;
            color: #dc2626;
            padding: 16px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #dc2626;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Relatório Inteligente IA</h1>
            <p>{description}</p>
            <div class="meta">
                <div class="meta-item">📅 <b>Anos:</b> {years_str}</div>
                <div class="meta-item">🗓️ <b>Meses:</b> {month_labels_str}</div>
                <div class="meta-item">⏱️ <b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</div>
            </div>
        </div>
        
        <div class="content">
"""

        # Inserir análise da IA se disponível
        if analysis_data:
            insights_li = "".join(f"<li>{item}</li>" for item in analysis_data.get("principais_insights", []))
            recs_li = "".join(f"<li>{item}</li>" for item in analysis_data.get("recomendacoes", []))
            
            html_content += f"""
            <div class="ai-analysis">
                <div class="ai-header">
                    <h2>💡 Análise Estratégica da IA</h2>
                </div>
                <div class="ai-body">
                    <div class="ai-summary">
                        <h3>Resumo Executivo</h3>
                        <p>{analysis_data.get("resumo_executivo", "")}</p>
                    </div>
                    <div class="ai-grid">
                        <div class="ai-card insights-card">
                            <h3>🔍 Principais Insights</h3>
                            <ul>
                                {insights_li}
                            </ul>
                        </div>
                        <div class="ai-card recommendations-card">
                            <h3>🎯 Recomendações Estratégicas</h3>
                            <ul>
                                {recs_li}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            """

        chart_scripts = []
        
        # Add results
        for idx, result in enumerate(query_results):
            if not result.get("success"):
                html_content += f'<div class="error">Erro ao processar: {result.get("label")}</div>\n'
                continue
            
            label = result.get("label", f"Análise {idx+1}")
            data = result.get("data", [])
            result_type = result.get("type", "table")
            
            html_content += f'''<div class="section">
                <h2>{label}</h2>
                <div class="section-desc">Análise dos dados obtidos para {label.lower()}</div>
'''
            
            if not data:
                html_content += '<div class="error">Sem dados disponíveis para este período</div>\n'
                html_content += '</div>\n'
                continue
            
            # Generate Chart.js dynamic element
            chart_style = result.get("chart_type", "bar")
            if result_type in ("chart", "both") and len(data) > 0:
                cols = list(data[0].keys())
                if len(cols) >= 2:
                    x_col = cols[0]
                    y_col = cols[1]
                    
                    x_vals = [str(row.get(x_col, "")) for row in data]
                    y_vals = []
                    for row in data:
                        try:
                            val_str = str(row.get(y_col, 0))
                            parsed_val = float(parse_currency(val_str) or 0)
                            y_vals.append(parsed_val)
                        except (ValueError, TypeError):
                            y_vals.append(0.0)
                    
                    html_content += f'''
                    <div class="chart-container">
                        <canvas id="chart_{idx}"></canvas>
                    </div>
                    '''
                    
                    chart_json_x = json.dumps(x_vals, ensure_ascii=False)
                    chart_json_y = json.dumps(y_vals, ensure_ascii=False)
                    
                    # Definir cores dinâmicas com base no tipo de gráfico
                    if chart_style in ("pie", "doughnut"):
                        bg_color_js = "['rgba(210, 93, 93, 0.8)', 'rgba(90, 155, 249, 0.8)', 'rgba(245, 158, 11, 0.8)', 'rgba(16, 185, 129, 0.8)', 'rgba(139, 92, 246, 0.8)', 'rgba(236, 72, 153, 0.8)', 'rgba(20, 184, 166, 0.8)', 'rgba(100, 116, 139, 0.8)']"
                        border_color_js = "['#d25d5d', '#5a9bf9', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#14b8a6', '#64748b']"
                        legend_js = "true"
                        scales_js = "{}"
                        extra_dataset_opts = ""
                    else:
                        legend_js = "false"
                        extra_dataset_opts = ""
                        if chart_style == "line":
                            bg_color_js = "'rgba(90, 155, 249, 0.15)'"
                            border_color_js = "'rgba(90, 155, 249, 1)'"
                            extra_dataset_opts = "fill: true, tension: 0.2, borderWidth: 3,"
                        else:  # bar
                            bg_color_js = "'rgba(210, 93, 93, 0.75)'"
                            border_color_js = "'rgba(210, 93, 93, 1)'"
                            
                        scales_js = f"""{{
                                y: {{
                                    beginAtZero: true,
                                    grid: {{
                                        color: '#f3f4f6'
                                    }},
                                    ticks: {{
                                        callback: function(value) {{
                                            let hasDec = value % 1 !== 0;
                                            if (String({json.dumps(y_col)}).toLowerCase().includes('valor') || String({json.dumps(y_col)}).toLowerCase().includes('receita')) {{
                                                return 'R$ ' + value.toLocaleString('pt-BR', hasDec ? {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }} : {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }});
                                            }}
                                            return value.toLocaleString('pt-BR', hasDec ? {{ minimumFractionDigits: 1, maximumFractionDigits: 2 }} : {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }});
                                        }},
                                        font: {{
                                            family: 'Outfit',
                                            size: 11
                                        }}
                                    }}
                                }},
                                x: {{
                                    grid: {{
                                        display: false
                                    }},
                                    ticks: {{
                                        font: {{
                                            family: 'Outfit',
                                            size: 11
                                        }}
                                    }}
                                }}
                            }}"""
                    
                    chart_scripts.append(f"""
                    const ctx_{idx} = document.getElementById('chart_{idx}').getContext('2d');
                    new Chart(ctx_{idx}, {{
                        type: '{chart_style}',
                        data: {{
                            labels: {chart_json_x},
                            datasets: [{{
                                label: {json.dumps(label, ensure_ascii=False)},
                                data: {chart_json_y},
                                backgroundColor: {bg_color_js},
                                borderColor: {border_color_js},
                                borderWidth: 1.5,
                                borderRadius: 6,
                                {extra_dataset_opts}
                                hoverOffset: 4
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{
                                    display: {legend_js},
                                    labels: {{
                                        font: {{ family: 'Outfit', size: 11 }}
                                    }}
                                }},
                                tooltip: {{
                                    backgroundColor: '#1f2937',
                                    titleFont: {{ family: 'Outfit', size: 13, weight: 'bold' }},
                                    bodyFont: {{ family: 'Outfit', size: 12 }},
                                    padding: 12,
                                    cornerRadius: 8,
                                    displayColors: {legend_js},
                                    callbacks: {{
                                        label: function(context) {{
                                            let label = context.label || '';
                                            let val = context.raw;
                                            let hasDec = val % 1 !== 0;
                                            let displayVal = '';
                                            if (String({json.dumps(y_col)}).toLowerCase().includes('valor') || String({json.dumps(y_col)}).toLowerCase().includes('receita')) {{
                                                displayVal = 'R$ ' + val.toLocaleString('pt-BR', hasDec ? {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }} : {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }});
                                            }} else {{
                                                displayVal = val.toLocaleString('pt-BR', hasDec ? {{ minimumFractionDigits: 1, maximumFractionDigits: 2 }} : {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }});
                                            }}
                                            return label ? label + ': ' + displayVal : displayVal;
                                        }}
                                    }}
                                }}
                            }},
                            scales: {scales_js}
                        }}
                    }});
                    """)
            
            # Add stats if numeric and specified in KPI defs
            stats = self._extract_stats(data, result.get("kpis", []))
            if stats:
                html_content += '<div class="stats">\n'
                for stat_label, stat_value in stats.items():
                    html_content += f'<div class="stat-box"><div class="stat-label">{stat_label}</div><div class="stat-value">{stat_value}</div></div>\n'
                html_content += '</div>\n'
            
            # Add table - Only if type is 'table' or 'both'
            if result_type in ("table", "both") and data and len(data) > 0:
                html_content += self._data_to_html_table(data)
            
            html_content += '</div>\n'
        
        html_content += f'''        </div>
        
        <div class="footer">
            <p>Relatório gerado automaticamente pelo Stampa SaaS | © {datetime.now().year}</p>
        </div>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            {"".join(chart_scripts)}
        }});
    </script>
</body>
</html>
'''
        
        # Save to file
        reports_dir = DATA_DIR / "relatórios"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_gemini_{timestamp}.html"
        filepath = reports_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(filepath)

    def _create_chart_base64(self, data, title, plt):
        """Create chart and return as base64"""
        try:
            if len(data) == 0:
                return None
            
            cols = list(data[0].keys())
            if len(cols) < 2:
                return None
            
            x_col = cols[0]
            y_col = cols[1]
            
            x_vals = [str(row.get(x_col, ""))[:20] for row in data]
            y_vals = []
            for row in data:
                try:
                    y_vals.append(float(row.get(y_col, 0)))
                except (ValueError, TypeError):
                    y_vals.append(0)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(x_vals, y_vals, color="#d25d5d", alpha=0.8)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel(x_col, fontsize=11)
            ax.set_ylabel(y_col, fontsize=11)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            
            buffer.seek(0)
            import base64
            return base64.b64encode(buffer.read()).decode()
        except Exception:
            return None

    def _extract_stats(self, data, kpi_defs=None):
        """Extract numeric stats from data using definition from Gemini"""
        stats = {}
        if not data or len(data) == 0:
            return stats
        
        # Se não houver definições de KPIs, não geramos nenhum card (foca na limpeza do relatório)
        if not kpi_defs:
            return stats
            
        for kpi in kpi_defs:
            col = kpi.get("column")
            label = kpi.get("label", col)
            op = kpi.get("operation", "sum").lower()
            
            if not col:
                continue
                
            values = []
            for row in data:
                val = row.get(col)
                if val is not None:
                    try:
                        # Se for formato monetário com R$ ou vírgula, tratar
                        val_clean = str(val).replace("R$", "").replace(" ", "")
                        if "," in val_clean and "." in val_clean:
                            val_clean = val_clean.replace(".", "").replace(",", ".")
                        elif "," in val_clean:
                            val_clean = val_clean.replace(",", ".")
                        values.append(float(val_clean))
                    except (ValueError, TypeError):
                        pass
            
            if op == "count":
                stats[label] = len(data)
            elif values:
                if op == "sum":
                    stats[label] = sum(values)
                elif op == "avg":
                    stats[label] = sum(values) / len(values)
            else:
                # Caso não seja numérico ou operação seja none, pega o valor do primeiro registro
                stats[label] = data[0].get(col, "")
                
        # Formata os valores calculados
        for label, val in list(stats.items()):
            if isinstance(val, (int, float)):
                val_float = float(val)
                if any(x in label.lower() for x in ("valor", "preço", "faturamento", "receita")):
                    stats[label] = format_currency(val_float)
                elif val_float.is_integer():
                    stats[label] = f"{int(val_float):,}".replace(",", ".")
                else:
                    stats[label] = f"{val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    
        return stats

    def _data_to_html_table(self, data):
        """Convert data to HTML table"""
        if not data or len(data) == 0:
            return ""
        
        cols = list(data[0].keys())
        table_html = '<div class="table-container"><table><thead><tr>'
        
        for col in cols:
            table_html += f'<th>{col}</th>'
        table_html += '</tr></thead><tbody>'
        
        for row in data[:50]:  # Max 50 rows
            table_html += '<tr>'
            for col in cols:
                val = row.get(col, "")
                table_html += f'<td>{val}</td>'
            table_html += '</tr>'
        
        if len(data) > 50:
            table_html += f'<tr><td colspan="{len(cols)}" style="text-align: center; color: #999;">... e mais {len(data) - 50} registros</td></tr>'
        
        table_html += '</tbody></table></div>'
        return table_html

    def on_ai_agent_send(self):
        prompt = self.ai_prompt_text.get("1.0", "end").strip()
        if not prompt:
            messagebox.showinfo("Agente de IA", "Digite um prompt.")
            return
        # For now, reuse execute_gemini_prompt flow by seeding the prompt into that handler
        self.gemini_prompt_entry.delete("1.0", "end")
        self.gemini_prompt_entry.insert("1.0", prompt)
        # call existing handler to process
        self.execute_gemini_prompt()
        # copy result to AI Agent output for convenience
        result = self.gemini_output.get("1.0", "end")
        self.ai_agent_output.delete("1.0", "end")
        self.ai_agent_output.insert("1.0", result)

    def _call_genai(self, system, user_text):
        """Helper: call genai and return response text."""
        if not genai:
            raise RuntimeError("google.generativeai not available")
        
        try:
            # Configure API key
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
        except Exception:
            pass
        
        try:
            # Use GenerativeModel with generate_content
            model = genai.GenerativeModel("gemini-2.5-flash")
            combined_prompt = f"{system}\n\n{user_text}"
            resp = model.generate_content(combined_prompt)
            return resp.text if resp else ""
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {str(e)}")

    def execute_gemini_prompt(self):
        prompt = self.gemini_prompt_entry.get("1.0", "end").strip()
        if not prompt:
            messagebox.showinfo("Gemini", "Digite um prompt para o Gemini.")
            return
        try:
            create_sqlite_db_from_csv()
        except Exception:
            traceback.print_exc()

        # Step 1: Generate SQL queries
        system_instructions = """Você é um analista de dados especialista da empresa. Seu trabalho é entender o que o usuário (Darlan) está pedindo e gerar as queries SQL necessárias.

IMPORTANTE:
- Você NÃO deve mencionar código SQL, banco de dados ou termos técnicos na resposta final
- Se não entender a pergunta, peca esclarecimento de forma natural e profissional, como um funcionário experiente
- Sempre responda como se fosse um colega da empresa, conversando naturalmente
- Nunca mostre exemplos de código SQL para o usuário

Gere um JSON com:
- gemini_json_gerado: array de queries SQL para responder a pergunta
- gemini_porque_gerou_json: razão simples das queries (sem termos técnicos)

Responda APENAS JSON."""
        
        user_msg_1 = f"""Schema disponível: clientes (empresa, email, telefone, data_criacao), pedidos (cliente_empresa, quantidade, valor, data, descricao, status)

Pergunta do Darlan: {prompt}"""

        try:
            resp1_text = self._call_genai(system_instructions, user_msg_1)
        except Exception as e:
            self.gemini_output.delete("1.0", "end")
            self.gemini_output.insert("1.0", f"Erro ao processar: {e}\n")
            return

        # Extract JSON
        json_text = {}
        try:
            m = re.search(r"\{[\s\S]*\}", resp1_text)
            if m:
                json_text = json.loads(m.group(0))
        except Exception:
            pass

        if not json_text:
            self.gemini_output.delete("1.0", "end")
            self.gemini_output.insert("1.0", f"{resp1_text}")
            return

        queries = json_text.get("gemini_json_gerado", [])
        rationale = json_text.get("gemini_porque_gerou_json", "")

        if not isinstance(queries, list) or not queries:
            self.gemini_output.delete("1.0", "end")
            self.gemini_output.insert("1.0", "Não consegui gerar a análise. Por favor, reformule sua pergunta.")
            return

        # Step 2: Execute queries
        query_results = {}
        for idx, q in enumerate(queries):
            try:
                query_results[f"query_{idx}"] = {"sql": q, "rows": run_sql_query(q)}
            except Exception as e:
                query_results[f"query_{idx}"] = {"sql": q, "error": str(e)}

        # Step 3: Get final answer
        system_final = """Você é um analista de dados da empresa conversando com Darlan.
Você recebeu os resultados das análises. Agora prepare uma resposta natural, clara e profissional.

REGRAS IMPORTANTES:
- NUNCA mencione SQL, queries ou banco de dados
- Nunca mostre código ou estrutura técnica
- Responda como um colega especialista em dados conversando naturalmente
- Se não houver dados, seja honesto e direto: "Não encontrei dados para isso" ou "Não temos registros disso"
- Sempre use linguagem profissional mas acessível
- Se a pergunta foi mal compreendida, peça esclarecimento de forma natural"""

        user_msg_2 = json.dumps({
            "pergunta_original": prompt,
            "resultados": query_results,
        }, ensure_ascii=False)

        try:
            resp2_text = self._call_genai(system_final, user_msg_2)
        except Exception as e:
            self.gemini_output.delete("1.0", "end")
            self.gemini_output.insert("1.0", f"Erro ao gerar resposta: {e}\n")
            return

        # Display results: final answer only
        self.gemini_output.delete("1.0", "end")
        try:
            self.gemini_output.insert("1.0", resp2_text)
        except Exception:
            self.gemini_output.insert("1.0", str(resp2_text))

    def draw_dashboard_revenue_chart(self):
        if not hasattr(self, "dashboard_revenue_canvas"):
            return
        canvas = self.dashboard_revenue_canvas
        canvas.delete("all")

        data = getattr(self, "dashboard_revenue_data", {})
        years = data.get("years", [])
        months = data.get("months", [])
        values = data.get("values", {})

        if not years or not months:
            canvas.create_text(
                20,
                20,
                anchor="nw",
                text="Sem dados para os anos ou período selecionados.",
                fill="#333333",
                font=("Segoe UI", 10, "bold"),
            )
            return

        width = max(canvas.winfo_width(), 560)
        height = max(canvas.winfo_height(), 220)
        left_margin = 80
        right_margin = 50
        top_margin = 24
        bottom_margin = 80
        chart_width = int(width - left_margin - right_margin)
        chart_height = height - top_margin - bottom_margin

        all_values = [value for year in years for value in values.get(year, [])]
        max_value = max(max(all_values), 1)
        x_count = len(months)
        x_step = chart_width / (x_count - 1) if x_count > 1 else chart_width

        canvas.create_line(left_margin, top_margin, left_margin, top_margin + chart_height, fill="#333333", width=1)
        canvas.create_line(left_margin, top_margin + chart_height, left_margin + chart_width, top_margin + chart_height, fill="#333333", width=1)

        # Desenha marcas no eixo Y com valores arredondados e linhas horizontais sutis
        def nice_step(value):
            if value <= 0:
                return 1
            magnitude = 10 ** int(math.floor(math.log10(value)))
            normalized = value / magnitude
            for candidate in [1, 1.5, 2, 2.5, 3, 5, 6, 7.5, 10]:
                if normalized <= candidate:
                    return max(int(candidate * magnitude), 1)
            return max(int(10 * magnitude), 1)

        tick_count = 4
        target_step = max_value / (tick_count - 1)
        step_value = max(nice_step(target_step), 1)
        max_tick_value = max(step_value * (tick_count - 1), 1)
        if max_value > max_tick_value:
            max_tick_value = max(step_value * tick_count, 1)

        for tick in range(tick_count):
            value = step_value * (tick_count - 1 - tick)
            y = top_margin + chart_height - (value / max_tick_value) * chart_height
            canvas.create_line(left_margin, y, left_margin + chart_width, y, fill="#ebebeb", width=1)
            canvas.create_text(left_margin - 10, y, anchor="e", text=format_currency(f"{value:.2f}"), fill="#666666", font=("Segoe UI", 8))

        month_labels = [month[:3] for month in months]
        for idx, label in enumerate(month_labels):
            x = left_margin + x_step * idx
            canvas.create_text(x, top_margin + chart_height + 18, anchor="n", text=label, fill="#333333", font=("Segoe UI", 8, "bold"))

        line_colors = ["#e25f6a", "#5cb85c", "#5a9bf9", "#f2a33d", "#8d6cb8", "#47b0a3", "#d670d6"]
        legend_x = left_margin
        legend_y = top_margin + chart_height + 30
        legend_dx = 0

        for idx, year in enumerate(years):
            year_values = values.get(year, [0.0] * x_count)
            coords = []
            for i, amount in enumerate(year_values):
                x = left_margin + x_step * i
                y = top_margin + chart_height - (amount / max_value) * chart_height
                coords.append((x, y))
            color = line_colors[idx % len(line_colors)]
            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                canvas.create_line(x1, y1, x2, y2, fill=color, width=2, smooth=True)
            for x, y in coords:
                canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline="")
            legend_label_x = legend_x + legend_dx
            legend_label_y = legend_y
            canvas.create_rectangle(legend_label_x, legend_label_y + 4, legend_label_x + 14, legend_label_y + 18, fill=color, outline="")
            canvas.create_text(legend_label_x + 18, legend_label_y + 11, anchor="w", text=str(year), fill="#333333", font=("Segoe UI", 8, "bold"))
            legend_dx += 90

    def _dashboard_nice_step(self, value):
        if value <= 0:
            return 1
        magnitude = 10 ** int(math.floor(math.log10(value)))
        normalized = value / magnitude
        for candidate in [1, 1.5, 2, 2.5, 3, 5, 6, 7.5, 10]:
            if normalized <= candidate:
                return max(int(candidate * magnitude), 1)
        return max(int(10 * magnitude), 1)

    def create_dashboard_orders_revenue_chart(self):
        frame_combo = ttk.LabelFrame(
            self.dashboard_charts_right,
            text="Pedidos e receita por mês",
            style="Card.TFrame",
        )
        frame_combo.pack(fill="both", expand=True)
        self.dashboard_combo_canvas = tk.Canvas(frame_combo, height=260, bg="#ffffff", highlightthickness=0)
        self.dashboard_combo_canvas.pack(fill="both", expand=True, padx=12, pady=12)
        self.dashboard_combo_data = {"months": [], "order_counts": [], "revenue": []}
        self.dashboard_combo_canvas.bind(
            "<Configure>",
            lambda event: self.draw_dashboard_orders_revenue_chart(),
        )

    def draw_dashboard_orders_revenue_chart(self):
        if not hasattr(self, "dashboard_combo_canvas"):
            return
        canvas = self.dashboard_combo_canvas
        canvas.delete("all")

        data = getattr(self, "dashboard_combo_data", {})
        months = data.get("months", [])
        order_counts = data.get("order_counts", [])
        revenue_values = data.get("revenue", [])

        if not months:
            canvas.create_text(
                20,
                20,
                anchor="nw",
                text="Sem dados para os anos ou período selecionados.",
                fill="#333333",
                font=("Segoe UI", 10, "bold"),
            )
            return

        width = max(canvas.winfo_width(), 560)
        height = max(canvas.winfo_height(), 260)
        left_margin = 58
        right_margin = 78
        top_margin = 28
        bottom_margin = 72
        chart_width = width - left_margin - right_margin
        chart_height = height - top_margin - bottom_margin

        max_count = max(max(order_counts), 1)
        max_revenue = max(max(revenue_values), 1.0)

        count_tick_count = 4
        count_step = max(self._dashboard_nice_step(max_count / (count_tick_count - 1)), 1)
        max_count_axis = max(count_step * (count_tick_count - 1), count_step)

        revenue_tick_count = 4
        revenue_step = max(self._dashboard_nice_step(max_revenue / (revenue_tick_count - 1)), 1)
        max_revenue_axis = max(revenue_step * (revenue_tick_count - 1), revenue_step)
        if max_revenue > max_revenue_axis:
            max_revenue_axis = revenue_step * revenue_tick_count

        x_count = len(months)
        group_width = chart_width / x_count if x_count else chart_width
        bar_width = min(group_width * 0.55, 42)

        canvas.create_line(
            left_margin,
            top_margin,
            left_margin,
            top_margin + chart_height,
            fill="#333333",
            width=1,
        )
        canvas.create_line(
            left_margin + chart_width,
            top_margin,
            left_margin + chart_width,
            top_margin + chart_height,
            fill="#333333",
            width=1,
        )
        canvas.create_line(
            left_margin,
            top_margin + chart_height,
            left_margin + chart_width,
            top_margin + chart_height,
            fill="#333333",
            width=1,
        )

        for tick in range(count_tick_count):
            value = count_step * tick
            y = top_margin + chart_height - (value / max_count_axis) * chart_height
            canvas.create_line(left_margin, y, left_margin + chart_width, y, fill="#f0f0f0", width=1)
            canvas.create_text(
                left_margin - 8,
                y,
                anchor="e",
                text=str(int(value)),
                fill="#5a9bf9",
                font=("Segoe UI", 8),
            )

        for tick in range(revenue_tick_count):
            value = revenue_step * tick
            y = top_margin + chart_height - (value / max_revenue_axis) * chart_height
            canvas.create_text(
                left_margin + chart_width + 8,
                y,
                anchor="w",
                text=format_currency(f"{value:.2f}"),
                fill="#e25f6a",
                font=("Segoe UI", 8),
            )

        canvas.create_text(
            left_margin - 42,
            top_margin + chart_height / 2,
            text="Pedidos",
            fill="#5a9bf9",
            font=("Segoe UI", 8, "bold"),
            angle=90,
        )
        canvas.create_text(
            left_margin + chart_width + 62,
            top_margin + chart_height / 2,
            text="Receita",
            fill="#e25f6a",
            font=("Segoe UI", 8, "bold"),
            angle=270,
        )

        line_coords = []
        for idx, month_label in enumerate(months):
            center_x = left_margin + group_width * idx + group_width / 2
            count = order_counts[idx] if idx < len(order_counts) else 0
            revenue = revenue_values[idx] if idx < len(revenue_values) else 0.0

            bar_height = (count / max_count_axis) * chart_height
            x1 = center_x - bar_width / 2
            x2 = center_x + bar_width / 2
            y1 = top_margin + chart_height - bar_height
            y2 = top_margin + chart_height
            canvas.create_rectangle(x1, y1, x2, y2, fill="#5a9bf9", outline="#4a8be0")

            rev_y = top_margin + chart_height - (revenue / max_revenue_axis) * chart_height
            line_coords.append((center_x, rev_y))
            canvas.create_oval(center_x - 4, rev_y - 4, center_x + 4, rev_y + 4, fill="#e25f6a", outline="#c94f59")

            short_label = month_label[:3]
            canvas.create_text(
                center_x,
                top_margin + chart_height + 16,
                anchor="n",
                text=short_label,
                fill="#333333",
                font=("Segoe UI", 8, "bold"),
            )

        for i in range(len(line_coords) - 1):
            x1, y1 = line_coords[i]
            x2, y2 = line_coords[i + 1]
            canvas.create_line(x1, y1, x2, y2, fill="#e25f6a", width=2, smooth=True)

        legend_y = top_margin + chart_height + 38
        canvas.create_rectangle(left_margin, legend_y + 3, left_margin + 14, legend_y + 17, fill="#5a9bf9", outline="")
        canvas.create_text(
            left_margin + 20,
            legend_y + 10,
            anchor="w",
            text="Quantidade de pedidos",
            fill="#333333",
            font=("Segoe UI", 8, "bold"),
        )
        canvas.create_line(left_margin + 180, legend_y + 10, left_margin + 210, legend_y + 10, fill="#e25f6a", width=2)
        canvas.create_oval(left_margin + 192, legend_y + 6, left_margin + 200, legend_y + 14, fill="#e25f6a", outline="")
        canvas.create_text(
            left_margin + 218,
            legend_y + 10,
            anchor="w",
            text="Receita (pedidos finalizados)",
            fill="#333333",
            font=("Segoe UI", 8, "bold"),
        )

    def create_dashboard_status_chart(self):
        frame_status = ttk.LabelFrame(self.dashboard_charts_left, text="Status dos pedidos", style="Card.TFrame")
        frame_status.pack(fill="both", expand=True)
        self.dashboard_status_canvas = tk.Canvas(frame_status, height=180, bg="#ffffff", highlightthickness=0)
        self.dashboard_status_canvas.pack(fill="both", expand=True, padx=12, pady=12)
        self.dashboard_status_counts = {}
        self.dashboard_status_canvas.bind(
            "<Configure>",
            lambda event: self.draw_dashboard_status_chart(self.dashboard_status_counts),
        )

    def create_dashboard_quantity_revenue_chart(self):
        frame_qr = ttk.LabelFrame(self.dashboard_charts_left, text="Receita (colunas) e Quantidade (linha)", style="Card.TFrame")
        frame_qr.pack(fill="both", expand=True, pady=(0, 10))
        self.dashboard_qr_canvas = tk.Canvas(frame_qr, height=260, bg="#ffffff", highlightthickness=0)
        self.dashboard_qr_canvas.pack(fill="both", expand=True, padx=12, pady=12)
        self.dashboard_qr_data = {"months": [], "revenue": [], "quantity": []}
        self.dashboard_qr_canvas.bind(
            "<Configure>",
            lambda event: self.draw_dashboard_quantity_revenue_chart(),
        )

    def draw_dashboard_quantity_revenue_chart(self):
        if not hasattr(self, "dashboard_qr_canvas"):
            return
        canvas = self.dashboard_qr_canvas
        canvas.delete("all")

        data = getattr(self, "dashboard_qr_data", {})
        months = data.get("months", [])
        revenue = data.get("revenue", [])
        quantity = data.get("quantity", [])

        if not months:
            canvas.create_text(20, 20, anchor="nw", text="Sem dados para o período selecionado.", fill="#333333", font=("Segoe UI", 10, "bold"))
            return

        width = max(canvas.winfo_width(), 560)
        height = max(canvas.winfo_height(), 220)
        left_margin = 58
        right_margin = 78
        top_margin = 28
        bottom_margin = 72
        chart_width = width - left_margin - right_margin
        chart_height = height - top_margin - bottom_margin

        max_revenue = max(max(revenue), 1.0)
        max_qty = max(max(quantity), 1)

        x_count = len(months)
        group_width = chart_width / x_count if x_count else chart_width
        bar_width = min(group_width * 0.6, 48)

        # Eixos
        canvas.create_line(left_margin, top_margin, left_margin, top_margin + chart_height, fill="#333333", width=1)
        canvas.create_line(left_margin, top_margin + chart_height, left_margin + chart_width, top_margin + chart_height, fill="#333333", width=1)

        # Labels eixo Y esquerda (revenue) com passos arredondados
        rev_tick_count = 4
        rev_step = self._dashboard_nice_step(max_revenue / rev_tick_count)
        max_revenue_axis = max(rev_step * rev_tick_count, 1.0)
        for t in range(rev_tick_count + 1):
            v = rev_step * t
            y = top_margin + chart_height - (v / max_revenue_axis) * chart_height
            # Formatar sem centavos e com R$
            try:
                display_rev = f"R$ {float(v):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except Exception:
                display_rev = format_currency(f"{v:.2f}")
            canvas.create_text(left_margin - 10, y, anchor="e", text=display_rev, fill="#e25f6a", font=("Segoe UI", 8))
            canvas.create_line(left_margin, y, left_margin + chart_width, y, fill="#f3f3f3", width=1)

        # Labels eixo Y direita (quantity)
        # Usar passos "nicely rounded" para ticks da quantidade
        qty_tick_count = 4
        qty_step = self._dashboard_nice_step(max_qty / qty_tick_count)
        max_qty_axis = max(qty_step * qty_tick_count, 1)
        for t in range(qty_tick_count + 1):
            v = qty_step * t
            y = top_margin + chart_height - (v / max_qty_axis) * chart_height
            canvas.create_text(left_margin + chart_width + 8, y, anchor="w", text=str(int(v)), fill="#5a9bf9", font=("Segoe UI", 8))

        # Desenha barras de revenue e linha de quantity
        line_coords = []
        for i, m in enumerate(months):
            cx = left_margin + group_width * i + group_width / 2
            rev = revenue[i] if i < len(revenue) else 0.0
            qty = quantity[i] if i < len(quantity) else 0

            bar_h = (rev / max_revenue) * chart_height if max_revenue else 0
            x1 = cx - bar_width / 2
            x2 = cx + bar_width / 2
            y1 = top_margin + chart_height - bar_h
            y2 = top_margin + chart_height
            canvas.create_rectangle(x1, y1, x2, y2, fill="#e25f6a", outline="")

            qty_y = top_margin + chart_height - (qty / max_qty) * chart_height if max_qty else top_margin + chart_height
            line_coords.append((cx, qty_y))
            canvas.create_oval(cx - 3, qty_y - 3, cx + 3, qty_y + 3, fill="#5a9bf9", outline="")

            canvas.create_text(cx, top_margin + chart_height + 14, anchor="n", text=m[:3], fill="#333333", font=("Segoe UI", 8, "bold"))

        for i in range(len(line_coords) - 1):
            x1, y1 = line_coords[i]
            x2, y2 = line_coords[i + 1]
            canvas.create_line(x1, y1, x2, y2, fill="#5a9bf9", width=2, smooth=True)

        # Legenda
        legend_y = top_margin + chart_height + 32
        canvas.create_rectangle(left_margin, legend_y + 3, left_margin + 14, legend_y + 17, fill="#e25f6a", outline="")
        canvas.create_text(left_margin + 20, legend_y + 10, anchor="w", text="Receita (R$)", fill="#333333", font=("Segoe UI", 8, "bold"))
        canvas.create_rectangle(left_margin + 140, legend_y + 6, left_margin + 152, legend_y + 18, fill="#5a9bf9", outline="")
        canvas.create_text(left_margin + 156, legend_y + 10, anchor="w", text="Quantidade (soma)", fill="#333333", font=("Segoe UI", 8, "bold"))

    def draw_dashboard_status_chart(self, status_counts):
        if not hasattr(self, "dashboard_status_canvas"):
            return
        canvas = self.dashboard_status_canvas
        canvas.delete("all")

        statuses = [
            ("Aguardando aprovação", "Agurd. Aprov.", "#e25f6a"),
            ("Em andamento", "Andamento", "#e25f6a"),
            ("Finalizado", "Finalizado", "#e25f6a"),
            ("Cancelado", "Cancelado", "#e25f6a"),
        ]
        counts = [status_counts.get(status, 0) for status, _, _ in statuses]
        max_count = max(max(counts), 1)

        width = max(canvas.winfo_width(), 560)
        height = max(canvas.winfo_height(), 180)
        left_margin = 140
        right_margin = 90
        bar_height = 26
        gap = 14
        total_width = int((width - left_margin - right_margin) * 0.72)
        total_height = len(statuses) * (bar_height + gap) + gap

        for idx, (status, label, color) in enumerate(statuses):
            count = status_counts.get(status, 0)
            bar_length = int(total_width * (count / max_count)) if max_count else 0
            y = gap + idx * (bar_height + gap)
            canvas.create_text(12, y + bar_height / 2, anchor="w", text=f"{label} ({count})", fill="#111111", font=("Segoe UI", 10, "bold"))
            canvas.create_rectangle(left_margin, y, left_margin + bar_length, y + bar_height, fill=color, outline="")
            canvas.create_rectangle(left_margin + bar_length, y, width - right_margin, y + bar_height, fill="#f3f3f3", outline="")

    

    def on_dashboard_select_all_changed(self):
        if self.dashboard_select_all_var.get():
            self.dashboard_month_from_var.set("Janeiro")
            self.dashboard_month_to_var.set("Dezembro")
            for var in self.dashboard_year_vars.values():
                var.set(1)
        self.update_dashboard_year_checkbox_state()
        self.refresh_dashboard()

    def update_dashboard_year_checkbox_state(self):
        enabled = not self.dashboard_select_all_var.get()
        for checkbox in self.dashboard_year_checkbuttons.values():
            checkbox.state(["!disabled"] if enabled else ["disabled"])
        self.dashboard_month_from_combo.configure(state="readonly" if enabled else "disabled")
        self.dashboard_month_to_combo.configure(state="readonly" if enabled else "disabled")

    def update_dashboard_year_checkboxes(self, year_values):
        if set(year_values) == set(self.dashboard_year_vars.keys()) and self.dashboard_year_vars:
            self.update_dashboard_year_checkbox_state()
            return
        existing_values = {year: var.get() for year, var in self.dashboard_year_vars.items()}
        for widget in self.dashboard_year_frame.winfo_children():
            widget.destroy()
        self.dashboard_year_vars = {}
        self.dashboard_year_checkbuttons = {}
        for year in year_values:
            year_state = existing_values.get(year, 1 if not self.dashboard_select_all_var.get() else 1)
            var = tk.IntVar(value=year_state)
            self.dashboard_year_vars[year] = var
            checkbox = ttk.Checkbutton(
                self.dashboard_year_frame,
                text=str(year),
                variable=var,
                command=self.refresh_dashboard,
            )
            checkbox.pack(side="left", padx=(0, 8), pady=2)
            self.dashboard_year_checkbuttons[year] = checkbox
        self.update_dashboard_year_checkbox_state()

    def update_dashboard_month_to_options(self):
        month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        selected_from = self.dashboard_month_from_var.get()
        if selected_from in month_names:
            start_index = month_names.index(selected_from)
        else:
            start_index = 0
        valid_to_values = month_names[start_index:]
        self.dashboard_month_to_combo["values"] = valid_to_values
        if self.dashboard_month_to_var.get() not in valid_to_values:
            self.dashboard_month_to_var.set(valid_to_values[0])

    def refresh_dashboard(self):
        clients_df = pd.DataFrame(self.clients)
        orders_df = pd.DataFrame(self.orders)

        if not hasattr(self, "dashboard_select_all_var"):
            return

        month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        if self.dashboard_month_from_var.get() not in month_names:
            self.dashboard_month_from_var.set("Janeiro")
        if self.dashboard_month_to_var.get() not in month_names:
            self.dashboard_month_to_var.set("Dezembro")

        if not clients_df.empty:
            clients_df["data_criação"] = pd.to_datetime(clients_df["data_criação"], errors="coerce")
        if not orders_df.empty:
            orders_df["data"] = pd.to_datetime(orders_df["data"], errors="coerce")

        available_years = set()
        if not clients_df.empty:
            available_years.update(clients_df["data_criação"].dt.year.dropna().astype(int).tolist())
        if not orders_df.empty:
            available_years.update(orders_df["data"].dt.year.dropna().astype(int).tolist())
        if not available_years:
            available_years = {datetime.now().year}
        year_values = [str(year) for year in sorted(available_years)]
        self.update_dashboard_year_checkboxes(year_values)

        selected_years = [int(year) for year, var in self.dashboard_year_vars.items() if var.get() == 1]
        month_from = month_names.index(self.dashboard_month_from_var.get()) + 1
        month_to = month_names.index(self.dashboard_month_to_var.get()) + 1
        if month_from > month_to:
            month_from, month_to = month_to, month_from

        if not clients_df.empty and selected_years:
            clients_df = clients_df[
                (clients_df["data_criação"].dt.year.isin(selected_years)) &
                (clients_df["data_criação"].dt.month >= month_from) &
                (clients_df["data_criação"].dt.month <= month_to)
            ]
        elif not clients_df.empty:
            clients_df = clients_df.iloc[0:0]

        if not orders_df.empty and selected_years:
            orders_df = orders_df[
                (orders_df["data"].dt.year.isin(selected_years)) &
                (orders_df["data"].dt.month >= month_from) &
                (orders_df["data"].dt.month <= month_to)
            ]
        elif not orders_df.empty:
            orders_df = orders_df.iloc[0:0]

        def parse_val(value):
            try:
                return float(parse_currency(value) or 0)
            except ValueError:
                return 0.0

        finished_orders_df = orders_df[orders_df["status"] == "Finalizado"] if not orders_df.empty else pd.DataFrame()
        total_revenue = finished_orders_df["valor"].apply(parse_val).sum() if not finished_orders_df.empty else 0.0
        finished_orders = int(len(finished_orders_df))
        if selected_years:
            years_count = len(selected_years)
        else:
            years_count = 0
        months_count = (month_to - month_from + 1) * years_count
        average_per_month = total_revenue / months_count if months_count > 0 else 0.0

        revenue_by_year_month = {}
        selected_months = [month_names[m - 1] for m in range(month_from, month_to + 1)]
        if not finished_orders_df.empty:
            finished_orders_df["year"] = finished_orders_df["data"].dt.year
            finished_orders_df["month"] = finished_orders_df["data"].dt.month
            grouped = (
                finished_orders_df.groupby(["year", "month"])["valor"]
                .apply(lambda s: s.apply(parse_val).sum())
                .reset_index()
            )
            revenue_map = {
                (int(row["year"]), int(row["month"])): float(row["valor"])
                for _, row in grouped.iterrows()
            }
        else:
            revenue_map = {}

        for year in selected_years:
            revenue_by_year_month[year] = [
                revenue_map.get((year, month), 0.0)
                for month in range(month_from, month_to + 1)
            ]

        order_count_map = {}
        if not orders_df.empty:
            orders_with_date = orders_df[orders_df["data"].notna()].copy()
            if not orders_with_date.empty:
                grouped_orders = orders_with_date.groupby(
                    [orders_with_date["data"].dt.year, orders_with_date["data"].dt.month]
                ).size()
                for (year, month), count in grouped_orders.items():
                    if pd.isna(year) or pd.isna(month):
                        continue
                    order_count_map[(int(year), int(month))] = int(count)

        combo_order_counts = []
        combo_revenue = []
        for month in range(month_from, month_to + 1):
            month_total_orders = sum(order_count_map.get((year, month), 0) for year in selected_years)
            month_total_revenue = sum(revenue_map.get((year, month), 0.0) for year in selected_years)
            combo_order_counts.append(month_total_orders)
            combo_revenue.append(month_total_revenue)

        self.dashboard_combo_data = {
            "months": selected_months,
            "order_counts": combo_order_counts,
            "revenue": combo_revenue,
        }

        # Preparar dados para novo gráfico: receita total por mês e soma de quantidade por mês
        qty_map = {}
        if not orders_df.empty:
            orders_with_date = orders_df[orders_df["data"].notna()].copy()
            if not orders_with_date.empty:
                orders_with_date["year"] = orders_with_date["data"].dt.year
                orders_with_date["month"] = orders_with_date["data"].dt.month
                # parse quantidade as int
                def parse_int_val(v):
                    try:
                        return int(float(str(v).replace(",", ".")))
                    except Exception:
                        return 0
                grouped_qty = (
                    orders_with_date.groupby([orders_with_date["year"], orders_with_date["month"]])["quantidade"]
                    .apply(lambda s: s.apply(parse_int_val).sum())
                    .reset_index()
                )
                for _, row in grouped_qty.iterrows():
                    qty_map[(int(row["year"]), int(row["month"]))] = int(row["quantidade"])

        qr_revenue = []
        qr_qty = []
        for month in range(month_from, month_to + 1):
            m_rev = sum(revenue_map.get((year, month), 0.0) for year in selected_years)
            m_qty = sum(qty_map.get((year, month), 0) for year in selected_years)
            qr_revenue.append(m_rev)
            qr_qty.append(m_qty)

        self.dashboard_qr_data = {
            "months": selected_months,
            "revenue": qr_revenue,
            "quantity": qr_qty,
        }

        status_counts = {
            "Aguardando aprovação": int((orders_df["status"] == "Aguardando aprovação").sum()) if not orders_df.empty else 0,
            "Em andamento": int((orders_df["status"] == "Em andamento").sum()) if not orders_df.empty else 0,
            "Finalizado": int((orders_df["status"] == "Finalizado").sum()) if not orders_df.empty else 0,
            "Cancelado": int((orders_df["status"] == "Cancelado").sum()) if not orders_df.empty else 0,
        }

        self.dashboard_labels["Receita total"].configure(text=format_currency(f"{total_revenue:.2f}"))
        self.dashboard_labels["Média por mês"].configure(text=format_currency(f"{average_per_month:.2f}"))
        self.dashboard_labels["Pedidos finalizados"].configure(text=str(finished_orders))
        self.dashboard_revenue_data = {
            "years": selected_years,
            "months": selected_months,
            "values": revenue_by_year_month,
        }
        self.dashboard_status_counts = status_counts
        self.draw_dashboard_revenue_chart()
        self.draw_dashboard_orders_revenue_chart()
        self.draw_dashboard_quantity_revenue_chart()
        self.draw_dashboard_status_chart(status_counts)

    def normalize_orders(self):
        updated = False
        for order in self.orders:
            if not order.get("cliente_empresa"):
                cliente_name = order.get("cliente") or order.get("cliente_empresa", "")
                match = next((client for client in self.clients if client["ClienteEmpresa"] == cliente_name), None)
                if match:
                    order["cliente_empresa"] = match["ClienteEmpresa"]
                    updated = True
                else:
                    order["cliente_empresa"] = cliente_name
            if not order.get("id_cliente"):
                match = next((client for client in self.clients if client["ClienteEmpresa"] == order["cliente_empresa"]), None)
                if match:
                    order["id_cliente"] = match["id_clientes"]
                    updated = True
                else:
                    order["id_cliente"] = ""
            if "status" not in order:
                order["status"] = ""
                updated = True
            if "cliente" in order:
                del order["cliente"]
            if "descricao" in order:
                order["descrição"] = order.get("descricao", order.get("descrição", ""))
                del order["descricao"]
        if updated:
            save_orders(self.orders)

    def refresh_clients_view(self):
        for item in self.tree_clients.get_children():
            self.tree_clients.delete(item)
        for client in self.clients:
            self.tree_clients.insert("", "end", iid=client["id_clientes"], values=(
                client["id_clientes"],
                client["ClienteEmpresa"],
                client.get("email", ""),
                client.get("telefone", ""),
                client["data_criação"],
            ))
        if hasattr(self, "dashboard_select_all_var"):
            self.refresh_dashboard()

    def refresh_orders_view(self):
        for item in self.tree_orders.get_children():
            self.tree_orders.delete(item)
        for column in PEDIDO_FIELDS:
            self.tree_orders.heading(column, text=self.get_order_heading_text(column))
        filtered_orders = self.get_filtered_orders()
        for order in filtered_orders:
            tag = order.get("status", "")
            self.tree_orders.insert("", "end", iid=order["id_pedidos"], values=(
                order.get("id_pedidos", ""),
                order.get("id_cliente", ""),
                order.get("cliente_empresa", order.get("cliente", "")),
                order.get("quantidade", ""),
                format_currency(order.get("valor", "")),
                order.get("data", ""),
                order.get("descrição", order.get("descricao", "")),
                order.get("status", ""),
            ), tags=(tag,))
        if hasattr(self, "dashboard_select_all_var"):
            self.refresh_dashboard()

    def update_client_options(self):
        self.all_client_options = [client["ClienteEmpresa"] for client in self.clients]
        current_value = self.combo_cliente.get().strip()
        if current_value:
            filtered = [name for name in self.all_client_options if current_value.lower() in name.lower()]
        else:
            filtered = list(self.all_client_options)
        self.combo_cliente["values"] = filtered
        if current_value and current_value not in filtered:
            self.combo_cliente.set("")

    def get_filtered_orders(self):
        orders = list(self.orders)
        status_filter = self.order_status_filter.get()
        if status_filter and status_filter != "Todos":
            orders = [order for order in orders if order.get("status", "") == status_filter]
        if self.order_sort_column:
            orders.sort(key=self.order_sort_key, reverse=self.order_sort_reverse)
        return orders

    def order_sort_key(self, order):
        column = self.order_sort_column
        if column in ("id_pedidos", "id_cliente", "quantidade"):
            value = order.get(column, "")
            return int(value) if str(value).isdigit() else 0
        if column == "valor":
            try:
                return float(str(order.get("valor", "")).replace(",", "."))
            except ValueError:
                return 0.0
        if column == "data":
            try:
                return datetime.strptime(order.get("data", ""), "%Y-%m-%d")
            except ValueError:
                return order.get("data", "")
        return str(order.get(column, "")).lower()

    def sort_orders(self, column):
        if self.order_sort_column == column:
            self.order_sort_reverse = not self.order_sort_reverse
        else:
            self.order_sort_column = column
            self.order_sort_reverse = False
        self.refresh_orders_view()

    def get_order_heading_text(self, column):
        text = column.replace("_", " ").title()
        if self.order_sort_column == column:
            text += " ▼" if self.order_sort_reverse else " ▲"

        return text

    def filter_client_options(self, event=None):
        typed = self.combo_cliente.get().strip()
        if typed:
            matching = [name for name in self.all_client_options if typed.lower() in name.lower()]
        else:
            matching = list(self.all_client_options)
        self.combo_cliente["values"] = matching
        self.combo_cliente.set(typed)
        if len(matching) == 1:
            self.combo_cliente.set(matching[0])

    def add_client(self):
        nome = self.entry_nome.get().strip()
        empresa = self.entry_empresa.get().strip()
        email = self.entry_email.get().strip()
        telefone = self.entry_telefone.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome do cliente.")
            return
        cliente_empresa = f"{nome} - {empresa}".strip()
        new_client = {
            "id_clientes": next_id(self.clients, "id_clientes"),
            "ClienteEmpresa": cliente_empresa,
            "email": email,
            "telefone": telefone,
            "data_criação": datetime.now().strftime("%Y-%m-%d"),
        }
        self.clients.append(new_client)
        save_clients(self.clients)
        self.refresh_clients_view()
        self.update_client_options()
        self.clear_client_form()
        messagebox.showinfo("Sucesso", "Cliente cadastrado com sucesso.")

    def update_client(self):
        if not self.selected_client_id:
            messagebox.showwarning("Atenção", "Selecione um cliente para atualizar.")
            return
        nome = self.entry_nome.get().strip()
        empresa = self.entry_empresa.get().strip()
        email = self.entry_email.get().strip()
        telefone = self.entry_telefone.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome do cliente.")
            return
        cliente_empresa = f"{nome} - {empresa}".strip()
        old_client = None
        for client in self.clients:
            if client["id_clientes"] == self.selected_client_id:
                old_client = client.copy()
                client["ClienteEmpresa"] = cliente_empresa
                client["email"] = email
                client["telefone"] = telefone
                break
        for order in self.orders:
            if order["id_cliente"] == self.selected_client_id:
                order["cliente_empresa"] = cliente_empresa
        save_clients(self.clients)
        save_orders(self.orders)
        self.refresh_clients_view()
        self.refresh_orders_view()
        self.update_client_options()
        self.tree_clients.selection_set(self.selected_client_id)
        self.tree_clients.focus(self.selected_client_id)
        messagebox.showinfo("Sucesso", "Cliente atualizado com sucesso.")

    def delete_client(self):
        selected = self.tree_clients.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um cliente para remover.")
            return
        client_id = selected[0]
        selected_values = self.tree_clients.item(client_id, "values")
        client_name = selected_values[1]
        client_orders = [order for order in self.orders if order["id_cliente"] == client_id]
        if client_orders:
            response = messagebox.askyesno(
                "Cliente com pedidos",
                f"O cliente '{client_name}' possui {len(client_orders)} pedido(s).\nDeseja remover também os pedidos relacionados?"
            )
            if not response:
                return
            self.orders = [order for order in self.orders if order["id_cliente"] != client_id]
            save_orders(self.orders)
        self.clients = [client for client in self.clients if client["id_clientes"] != client_id]
        save_clients(self.clients)
        self.refresh_clients_view()
        self.refresh_orders_view()
        self.update_client_options()
        self.clear_client_form()
        messagebox.showinfo("Sucesso", "Cliente removido com sucesso.")

    def add_order(self):
        cliente = self.combo_cliente.get().strip()
        quantidade = self.entry_quantidade.get().strip()
        valor = parse_currency(self.entry_valor.get().strip())
        descricao = self.text_descricao.get("1.0", "end").strip()
        status = self.combo_status.get().strip()

        if not cliente:
            messagebox.showwarning("Atenção", "Selecione um cliente para o pedido.")
            return
        client_obj = next((c for c in self.clients if c["ClienteEmpresa"] == cliente), None)
        if not client_obj:
            messagebox.showwarning("Atenção", "Cliente selecionado não foi encontrado.")
            return
        if not quantidade.isdigit() or int(quantidade) <= 0:
            messagebox.showwarning("Atenção", "Informe uma quantidade válida.")
            return
        try:
            float_valor = float(valor.replace(",", "."))
            if float_valor < 0:
                raise ValueError
            valor = f"{float_valor:.2f}"
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um valor válido para o pedido.")
            return
        if not descricao:
            messagebox.showwarning("Atenção", "Informe a descrição do pedido.")
            return

        new_order = {
            "id_pedidos": next_id(self.orders, "id_pedidos"),
            "id_cliente": client_obj["id_clientes"],
            "cliente_empresa": client_obj["ClienteEmpresa"],
            "quantidade": quantidade,
            "valor": valor,
            "data": datetime.now().strftime("%Y-%m-%d"),
            "descrição": descricao,
            "status": status or STATUS_OPTIONS[0],
        }
        self.orders.append(new_order)
        save_orders(self.orders)
        order_asset_folder(new_order["id_pedidos"])
        self.refresh_orders_view()
        self.clear_order_form()
        messagebox.showinfo("Sucesso", "Pedido cadastrado com sucesso.")

    def update_order(self):
        if not self.selected_order_id:
            messagebox.showwarning("Atenção", "Selecione um pedido para atualizar.")
            return
        cliente = self.combo_cliente.get().strip()
        quantidade = self.entry_quantidade.get().strip()
        valor = parse_currency(self.entry_valor.get().strip())
        descricao = self.text_descricao.get("1.0", "end").strip()
        status = self.combo_status.get().strip()

        if not cliente:
            messagebox.showwarning("Atenção", "Selecione um cliente para o pedido.")
            return
        client_obj = next((c for c in self.clients if c["ClienteEmpresa"] == cliente), None)
        if not client_obj:
            messagebox.showwarning("Atenção", "Cliente selecionado não foi encontrado.")
            return
        if not quantidade.isdigit() or int(quantidade) <= 0:
            messagebox.showwarning("Atenção", "Informe uma quantidade válida.")
            return
        try:
            float_valor = float(valor.replace(",", "."))
            if float_valor < 0:
                raise ValueError
            valor = f"{float_valor:.2f}"
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um valor válido para o pedido.")
            return
        if not descricao:
            messagebox.showwarning("Atenção", "Informe a descrição do pedido.")
            return

        for order in self.orders:
            if order["id_pedidos"] == self.selected_order_id:
                order["id_cliente"] = client_obj["id_clientes"]
                order["cliente_empresa"] = client_obj["ClienteEmpresa"]
                order["quantidade"] = quantidade
                order["valor"] = valor
                order["descrição"] = descricao
                order["status"] = status or STATUS_OPTIONS[0]
                break

        save_orders(self.orders)
        self.refresh_orders_view()
        self.clear_order_form()
        messagebox.showinfo("Sucesso", "Pedido atualizado com sucesso.")

    def delete_order(self):
        selected = self.tree_orders.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um pedido para remover.")
            return
        order_id = selected[0]
        order_values = self.tree_orders.item(order_id, "values")
        response = messagebox.askyesno(
            "Remover pedido",
            f"Tem certeza de que deseja remover o pedido {order_values[0]} do cliente '{order_values[2]}'?"
        )
        if not response:
            return
        pedido_folder = ART_BASE_FOLDER / f"pedido_{order_id}"
        if pedido_folder.exists() and pedido_folder.is_dir():
            try:
                shutil.rmtree(pedido_folder)
            except Exception as e:
                messagebox.showwarning(
                    "Atenção",
                    f"O pedido foi removido, mas não foi possível excluir a pasta de artes:\n{e}"
                )
        self.orders = [order for order in self.orders if order["id_pedidos"] != order_id]
        save_orders(self.orders)
        self.refresh_orders_view()
        self.clear_order_form()
        messagebox.showinfo("Sucesso", "Pedido removido com sucesso.")

    def on_client_select(self, event):
        selected = self.tree_clients.selection()
        if not selected:
            return
        client_id = selected[0]
        values = self.tree_clients.item(client_id, "values")
        self.selected_client_id = client_id
        cliente_empresa = values[1]
        nome, empresa = split_cliente_empresa(cliente_empresa)
        self.entry_nome.delete(0, tk.END)
        self.entry_nome.insert(0, nome)
        self.entry_empresa.delete(0, tk.END)
        self.entry_empresa.insert(0, empresa)
        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, values[2])
        self.entry_telefone.delete(0, tk.END)
        self.entry_telefone.insert(0, values[3])

    def on_order_select(self, event):
        selected = self.tree_orders.selection()
        if not selected:
            return
        order_id = selected[0]
        values = self.tree_orders.item(order_id, "values")
        self.selected_order_id = order_id
        self.combo_cliente.set(values[2])
        self.entry_quantidade.delete(0, tk.END)
        self.entry_quantidade.insert(0, values[3])
        self.entry_valor.delete(0, tk.END)
        self.entry_valor.insert(0, parse_currency(values[4]))
        self.text_descricao.delete("1.0", tk.END)
        self.text_descricao.insert("1.0", values[6])
        self.combo_status.set(values[7])
        self.order_folder_label.configure(text=f"Pasta do pedido: {ART_BASE_FOLDER / ('pedido_' + order_id)}")

    def open_selected_order_folder(self):
        if not self.selected_order_id:
            messagebox.showwarning("Atenção", "Selecione um pedido para abrir a pasta.")
            return
        open_order_folder(self.selected_order_id)

    def clear_client_form(self):
        self.selected_client_id = None
        self.entry_nome.delete(0, tk.END)
        self.entry_empresa.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_telefone.delete(0, tk.END)
        self.tree_clients.selection_remove(self.tree_clients.selection())

    def clear_order_form(self):
        
        self.selected_order_id = None
        self.combo_cliente.set("")
        self.entry_quantidade.delete(0, tk.END)
        self.entry_valor.delete(0, tk.END)
        self.text_descricao.delete("1.0", tk.END)
        self.combo_status.set(STATUS_OPTIONS[0])
        self.tree_orders.selection_remove(self.tree_orders.selection())


if __name__ == "__main__":
    root = tk.Tk()
    app = StampaApp(root)
    root.mainloop()
