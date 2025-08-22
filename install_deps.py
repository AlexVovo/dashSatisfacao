import subprocess
import sys

# Lista de dependências necessárias
packages = [
    "streamlit",
    "gspread",
    "google-auth",   # contém google.oauth2.service_account
    "pandas",
    "plotly",
    "fpdf2",         # versão atualizada do fpdf
    "Pillow",        # PIL
]

def install(package):
    """Instala um pacote via pip"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    print("Instalando dependências necessárias...\n")
    for package in packages:
        try:
            print(f"➡ Instalando {package}...")
            install(package)
        except Exception as e:
            print(f"❌ Erro ao instalar {package}: {e}")
    print("\n✅ Todas as dependências foram processadas!")

if __name__ == "__main__":
    main()
