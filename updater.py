"""
Updater = Detecta versão antiga + sobrescreve
Roda ANTES do main.py
"""
import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

def get_exe_path():
    """Retorna caminho do executável em execução"""
    return Path(sys.executable)

def kill_old_process():
    """Mata processo antigo se tiver rodando (NÃO mata processo atual)"""
    try:
        # Se roda como .exe, NÃO mata a si mesmo
        if not getattr(sys, 'frozen', False):
            # Se é script Python, pode matar .exe antigo
            os.system('taskkill /f /im StampaSaaS.exe 2>nul')
            time.sleep(1)
    except Exception:
        pass

def get_app_dir():
    """Retorna diretório do aplicativo"""
    if getattr(sys, 'frozen', False):
        # Roda como .exe
        return Path(sys.executable).parent
    else:
        # Roda como script
        return Path(__file__).parent

def backup_user_data():
    """Backup dados do usuário para restaurar depois"""
    app_dir = get_app_dir()
    backup_files = {}
    
    files_backup = [
        "setup_app.py",
        "main.py",
        "main_standalone.py",
        "LOGO.ico",
        "requirements.txt",
        ".env"
    ]
    
    for fname in files_backup:
        fpath = app_dir / fname
        if fpath.exists():
            backup_files[fname] = fpath.read_bytes()
    
    return backup_files, app_dir

def restore_from_backup(backup_files, app_dir):
    """Restaura backups"""
    for fname, content in backup_files.items():
        try:
            (app_dir / fname).write_bytes(content)
        except Exception as e:
            print(f"Erro ao restaurar {fname}: {e}")

def update_program():
    """Verifica + atualiza programa se necessário"""
    try:
        # Mata processo antigo
        kill_old_process()
        
        # Obtém diretórios
        app_dir = get_app_dir()
        exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else app_dir
        
        # Se não for executável, nada a fazer
        if not getattr(sys, 'frozen', False):
            return
        
        # Verifica versão do .exe
        exe_path = Path(sys.executable)
        version_file = app_dir / ".version_exe"
        
        current_time = int(exe_path.stat().st_mtime)
        
        if version_file.exists():
            last_version = int(version_file.read_text())
            if current_time == last_version:
                # Mesmo .exe, sem atualização
                return
        
        # Atualiza marcador
        version_file.write_text(str(current_time))
        
    except Exception as e:
        print(f"Aviso atualização: {e}")

if __name__ == "__main__":
    update_program()
