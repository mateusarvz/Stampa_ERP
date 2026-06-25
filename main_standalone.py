"""
Ponto entrada = Stampa SaaS Standalone
Roda updater + setup ANTES de tudo
"""
import sys
import os
from pathlib import Path
import traceback

# Log errors to file (console pode estar hidden)
LOG_FILE = Path(os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home() / "AppData" / "Local")) / "Stampa_SaaS" / "error.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_error(msg):
    """Log to file + stdout (alguns users verão console)"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except:
        pass
    print(msg)

try:
    log_error("=== Iniciando Stampa SaaS ===")
    
    # Updater: sobrescreve versão antiga (skip se frozen/exe para evitar auto-kill)
    try:
        log_error("Iniciando updater...")
        if not getattr(sys, 'frozen', False):
            from updater import update_program
            update_program()
        log_error("Updater OK (skipped/completed)")
    except Exception as e:
        log_error(f"Aviso updater: {e}\n{traceback.format_exc()}")

    # Setup ambiente
    try:
        log_error("Iniciando setup...")
        from setup_app import setup
        setup()
        log_error("Setup OK")
    except Exception as e:
        log_error(f"Erro em setup: {e}\n{traceback.format_exc()}")
        input("Pressione ENTER para continuar...")

    # Agora roda main
    try:
        log_error("Importando main...")
        import main
        log_error("Main rodou OK")
    except KeyboardInterrupt:
        log_error("Interrupção do usuário")
    except Exception as e:
        log_error(f"Erro ao executar main: {e}\n{traceback.format_exc()}")
        input("Pressione ENTER para fechar...")

except Exception as e:
    log_error(f"ERRO CRÍTICO: {e}\n{traceback.format_exc()}")
    input("Pressione ENTER para fechar...")
