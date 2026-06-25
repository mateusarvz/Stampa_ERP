# BUILD EXECUTAVEL - STAMPA SAAS

Lógica NOVA e SIMPLES para criar executável standalone.

## Como usar

### Windows (Recomendado)
```batch
build.bat
```

Pronto. Gera `dist\StampaSaaS.exe` automaticamente.

### Linux/Mac
```bash
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --onefile --windowed \
  --icon="LOGO.ico" \
  --name="StampaSaaS" \
  --add-data="LOGO.ico:." \
  --add-data="LOGO_BARRA DE TAREFAS.png:." \
  --hidden-import=tkinter \
  --hidden-import=sqlite3 \
  --hidden-import=pandas \
  --hidden-import=google.generativeai \
  --hidden-import=dotenv \
  main.py
```

## O que foi removido

- build_exe.bat (velho)
- StampaSaaS.spec (velho)
- build/ (pasta antiga)
- dist/ (pasta antiga)
- main_standalone.py (não usado)

## O que inclui

✓ Todas as dependências (requirements.txt)
✓ Abas: Pedidos, Clientes, Dashboard, Agente de IA, Relatorio Gemini
✓ Ícone e imagens
✓ Banco de dados SQLite
✓ API Gemini integrada
✓ Variáveis de ambiente (.env)

## Arquivos novos

- `build.bat` → Executa tudo automaticamente
- `build.spec` → Config PyInstaller

Pronto!
