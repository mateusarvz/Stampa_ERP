"""
Debug wrapper = Captura erros do .exe
Mostra exatamente o que falhou
"""
import sys
import os
import traceback
from pathlib import Path

def debug_main():
    """Roda main com captura de erros completa"""
    try:
        # Debug: mostra paths
        print(f"Executável: {sys.executable}")
        print(f"Diretório trabalho: {os.getcwd()}")
        print(f"Python version: {sys.version}")
        
        # Tenta importar updater
        print("\n[1/3] Carregando updater...")
        try:
            from updater import update_program
            update_program()
            print("✓ Updater OK")
        except Exception as e:
            print(f"⚠ Aviso updater: {e}")
        
        # Tenta setup
        print("\n[2/3] Carregando setup...")
        try:
            from setup_app import setup
            setup()
            print("✓ Setup OK")
        except Exception as e:
            print(f"✗ Erro setup: {e}")
            traceback.print_exc()
            input("Pressione ENTER para continuar mesmo assim...")
        
        # Tenta main
        print("\n[3/3] Carregando programa...")
        try:
            import main
            print("✓ Main OK - programa encerrado")
        except KeyboardInterrupt:
            print("\nPrograma fechado pelo usuário")
        except Exception as e:
            print(f"✗ ERRO CRÍTICO:")
            traceback.print_exc()
            input("Pressione ENTER para fechar...")
            sys.exit(1)
            
    except Exception as e:
        print(f"ERRO FATAL: {e}")
        traceback.print_exc()
        input("Pressione ENTER para fechar...")
        sys.exit(1)

if __name__ == "__main__":
    debug_main()
