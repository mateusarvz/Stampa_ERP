import os
from pathlib import Path
import sqlite3
# replicate get_app_data_dir
appdata_root = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or str(Path.home() / 'AppData' / 'Local')
DATA_DIR = Path(appdata_root) / 'Stampa_SaaS'
db = DATA_DIR / 'stampa_data.db'
print('DATA_DIR =>', DATA_DIR)
print('DB exists?', db.exists())
if not db.exists():
    exit(0)
conn = sqlite3.connect(str(db))
cur = conn.cursor()
for t in ('clientes','pedidos'):
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(t, cur.fetchone()[0])
    except Exception as e:
        print('Error counting', t, e)
# sample
try:
    cur.execute('SELECT * FROM pedidos LIMIT 5')
    rows = cur.fetchall()
    print('Sample pedidos:', rows)
except Exception as e:
    print('Sample error', e)
conn.close()
