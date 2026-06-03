"""Pipeline local: baixa o Focus do BCB e extrai o texto em sequência."""

import argparse
import sys
import webbrowser
from pathlib import Path

# Garante que a pasta src/ seja encontrada ao importar os módulos do projeto
sys.path.insert(0, str(Path(__file__).parent / "src"))

from baixar_focus import baixar
from extrair_texto import extrair


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline Focus: baixar + extrair.")
    parser.add_argument(
        "--abrir",
        action="store_true",
        help="Abre o arquivo .txt gerado no navegador padrão ao final.",
    )
    args = parser.parse_args()

    pasta_dados = Path(__file__).parent / "data"

    # Passo 1: baixa o PDF mais recente do BCB
    data_pub, caminho_pdf = baixar(pasta_dados)
    tamanho_kb = caminho_pdf.stat().st_size / 1024
    print(f"[1/2] PDF baixado: {caminho_pdf.name} ({tamanho_kb:.1f} KB)")

    # Passo 2: extrai o texto do PDF para .txt
    caminho_txt = extrair(caminho_pdf)
    print(f"[2/2] Texto extraído: {caminho_txt}")

    # Abre o .txt no navegador padrão, se solicitado
    if args.abrir:
        webbrowser.open(caminho_txt.resolve().as_uri())


if __name__ == "__main__":
    main()
