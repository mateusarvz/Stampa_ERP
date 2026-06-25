from pathlib import Path
import csv, json
from main import DATA_DIR, CLIENTES_FILE, PEDIDOS_FILE, create_sqlite_db_from_csv, run_sql_query
print('DATA_DIR=', DATA_DIR)
# ensure DB up-to-date
create_sqlite_db_from_csv()
db=DATA_DIR / 'stampa_data.db'
print('DB path:', db)
# counts CSV
with CLIENTES_FILE.open(encoding='utf-8') as f:
    c= sum(1 for _ in csv.DictReader(f))
with PEDIDOS_FILE.open(encoding='utf-8') as f:
    p= sum(1 for _ in csv.DictReader(f))
print('CSV counts -> clientes:', c, 'pedidos:', p)
# counts DB
res_c = run_sql_query('SELECT COUNT(*) as c FROM clientes', sqlite_path=db)
res_p = run_sql_query('SELECT COUNT(*) as c FROM pedidos', sqlite_path=db)
print('DB counts -> clientes:', res_c[0]['c'] if res_c else 0, 'pedidos:', res_p[0]['c'] if res_p else 0)
# sample rows
print('\nSample pedidos (5):')
rows = run_sql_query('SELECT * FROM pedidos LIMIT 5', sqlite_path=db)
print(json.dumps(rows, indent=2, ensure_ascii=False))
