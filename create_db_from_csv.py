import sqlite3
import csv
import os
from pathlib import Path
appdata_root = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or str(Path.home() / 'AppData' / 'Local')
DATA_DIR = Path(appdata_root) / 'Stampa_SaaS'
CLIENTES_FILE = DATA_DIR / 'CLIENTES.csv'
PEDIDOS_FILE = DATA_DIR / 'PEDIDOS.csv'
DB_PATH = DATA_DIR / 'stampa_data.db'
DATA_DIR.mkdir(parents=True, exist_ok=True)
print('Using DATA_DIR:', DATA_DIR)
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()
cur.execute('PRAGMA foreign_keys = ON;')
cur.execute('''CREATE TABLE IF NOT EXISTS clientes (
    id_clientes TEXT PRIMARY KEY,
    ClienteEmpresa TEXT,
    email TEXT,
    telefone TEXT,
    data_criacao TEXT
)
''')
cur.execute('''CREATE TABLE IF NOT EXISTS pedidos (
    id_pedidos TEXT PRIMARY KEY,
    id_cliente TEXT,
    cliente_empresa TEXT,
    quantidade REAL,
    valor REAL,
    data TEXT,
    descricao TEXT,
    status TEXT,
    FOREIGN KEY(id_cliente) REFERENCES clientes(id_clientes)
)
''')
# load CSVs if exist
if CLIENTES_FILE.exists():
    with CLIENTES_FILE.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            cur.execute('REPLACE INTO clientes (id_clientes, ClienteEmpresa, email, telefone, data_criacao) VALUES (?,?,?,?,?)',
                        (r.get('id_clientes'), r.get('ClienteEmpresa'), r.get('email'), r.get('telefone'), r.get('data_criação') or r.get('data_criacao')))
else:
    print('CLIENTES.csv not found at', CLIENTES_FILE)

if PEDIDOS_FILE.exists():
    with PEDIDOS_FILE.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            cur.execute('REPLACE INTO pedidos (id_pedidos, id_cliente, cliente_empresa, quantidade, valor, data, descricao, status) VALUES (?,?,?,?,?,?,?,?)',
                        (r.get('id_pedidos'), r.get('id_cliente') or r.get('id_clientes'), r.get('cliente_empresa'), r.get('quantidade') or None, r.get('valor') or None, r.get('data'), r.get('descrição') or r.get('descricao'), r.get('status')))
else:
    print('PEDIDOS.csv not found at', PEDIDOS_FILE)

conn.commit()
print('DB created at', DB_PATH)
conn.close()
