"""
Setup + initialization para Stampa SaaS
Roda ANTES do main.py para garantir ambiente correto
"""
import os
import sys
import csv
from pathlib import Path

def get_app_data_dir():
    """Cria pasta de dados AppData"""
    appdata_root = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home() / "AppData" / "Local")
    data_dir = Path(appdata_root) / "Stampa_SaaS"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def init_csv_files(data_dir):
    """Cria CSVs vazios se não existem"""
    clientes_file = data_dir / "CLIENTES.csv"
    pedidos_file = data_dir / "PEDIDOS.csv"
    
    if not clientes_file.exists():
        with clientes_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id_clientes", "ClienteEmpresa", "email", "telefone", "data_criação"])
            writer.writeheader()
    
    if not pedidos_file.exists():
        with pedidos_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id_pedidos", "id_cliente", "cliente_empresa", "quantidade", "valor", "data", "descrição", "status"])
            writer.writeheader()

def init_db(data_dir):
    """Cria banco de dados SQLite"""
    try:
        import sqlite3
        db_path = data_dir / "stampa_data.db"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id_clientes TEXT PRIMARY KEY,
                ClienteEmpresa TEXT,
                email TEXT,
                telefone TEXT,
                data_criacao TEXT
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id_pedidos TEXT PRIMARY KEY,
                id_cliente TEXT,
                cliente_empresa TEXT,
                quantidade INTEGER,
                valor REAL,
                data TEXT,
                descricao TEXT,
                status TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar BD: {e}")

def check_dependencies():
    """Verifica dependências críticas"""
    deps = ["tkinter", "pandas", "google.generativeai", "dotenv"]
    missing = []
    
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"Aviso: Dependências faltando: {missing}")
        return False
    return True

def setup():
    """Executa setup completo"""
    data_dir = get_app_data_dir()
    init_csv_files(data_dir)
    init_db(data_dir)
    check_dependencies()
    return data_dir

if __name__ == "__main__":
    setup()
