"""Extrai o texto de um PDF do Boletim Focus e salva como .txt."""

import argparse
import sys
import pdfplumber
from pathlib import Path


def extrair(pdf_path: str | Path) -> Path:
    """Abre o PDF com pdfplumber, concatena o texto de todas as páginas
    e salva num arquivo .txt de mesmo nome (mesma pasta, extensão trocada).

    Retorna o caminho do arquivo .txt gerado.
    """
    caminho_pdf = Path(pdf_path)

    with pdfplumber.open(caminho_pdf) as pdf:
        # Extrai o texto de cada página; páginas sem texto retornam None
        paginas = [pagina.extract_text() or "" for pagina in pdf.pages]

    texto_completo = "\n\n".join(paginas)

    caminho_txt = caminho_pdf.with_suffix(".txt")
    caminho_txt.write_text(texto_completo, encoding="utf-8")

    return caminho_txt


def _pdf_mais_recente(pasta: Path) -> Path | None:
    """Retorna o focus_*.pdf mais recente da pasta, ou None se não houver nenhum."""
    candidatos = sorted(pasta.glob("focus_*.pdf"))
    return candidatos[-1] if candidatos else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai texto de um PDF do Focus.")
    parser.add_argument(
        "--pdf",
        metavar="CAMINHO",
        help="Caminho explícito para o PDF. Se omitido, usa o mais recente de data/.",
    )
    args = parser.parse_args()

    if args.pdf:
        pdf_alvo = Path(args.pdf)
    else:
        # Busca automaticamente na pasta data/ relativa à raiz do projeto
        pasta_dados = Path(__file__).parent.parent / "data"
        pdf_alvo = _pdf_mais_recente(pasta_dados)

        if pdf_alvo is None:
            print(
                "Nenhum PDF encontrado em data/. "
                "Execute primeiro: python src/baixar_focus.py",
                file=sys.stderr,
            )
            sys.exit(1)

    caminho_txt = extrair(pdf_alvo)
    tamanho_kb = caminho_txt.stat().st_size / 1024
    print(f"Texto extraído de: {pdf_alvo.name}")
    print(f"Salvo em:          {caminho_txt}")
    print(f"Tamanho:           {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
