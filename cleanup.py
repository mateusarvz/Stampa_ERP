#!/usr/bin/env python3
"""
Limpeza de builds antigos e cache.
Uso: python cleanup.py
"""

import shutil
import os
from pathlib import Path

dirs_to_remove = [
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
]

files_to_remove = [
    "build_exe.bat",  # VELHO
    "StampaSaaS.spec",  # VELHO
    "main_standalone.py",  # NÃO USADO
    "*.pyc",
]

def cleanup():
    print("[*] Limpando builds antigos...\n")
    
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"[-] Removendo {dir_name}/")
            shutil.rmtree(dir_path)
    
    for pattern in files_to_remove:
        if "*" in pattern:
            for file in Path(".").glob(pattern):
                print(f"[-] Removendo {file}")
                file.unlink()
        else:
            file_path = Path(pattern)
            if file_path.exists():
                print(f"[-] Removendo {pattern}")
                file_path.unlink()
    
    print("\n[+] Limpeza concluída!")

if __name__ == "__main__":
    cleanup()
