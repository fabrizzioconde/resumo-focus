"""Baixa o PDF mais recente do Boletim Focus do Banco Central do Brasil."""

import urllib3
import requests
from datetime import date, timedelta
from pathlib import Path

URL_BASE = "https://www.bcb.gov.br/content/focus/focus/R{data}.pdf"
CABECALHO = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MAX_TENTATIVAS = 7

# O BCB usa certificado com cadeia intermediária ausente no bundle padrão do
# Python no Windows; verify=False contorna isso para este domínio conhecido.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def baixar(dest: str | Path, hoje: date | None = None) -> tuple[date, Path]:
    """Baixa o PDF do Focus mais recente e salva em `dest`.

    O arquivo no site do BCB tem como data a SEXTA-FEIRA de referência da pesquisa
    (embora o relatório seja disponibilizado na segunda seguinte). Por isso a busca
    parte de hoje e RECUA um dia por tentativa (até MAX_TENTATIVAS), encontrando a
    sexta mais recente com PDF publicado — o recuo também cobre feriados que adiam a
    data de referência. Valida que o arquivo é um PDF real (%PDF) antes de salvar.

    `hoje` permite fixar a data de partida em testes; em produção usa date.today().

    Retorna (data_publicacao, caminho_arquivo) ou levanta RuntimeError.
    """
    pasta = Path(dest)
    pasta.mkdir(parents=True, exist_ok=True)

    inicio = hoje or date.today()
    data_tentativa = inicio

    for _ in range(MAX_TENTATIVAS):
        url = URL_BASE.format(data=data_tentativa.strftime("%Y%m%d"))

        resposta = requests.get(url, headers=CABECALHO, timeout=30, verify=False)

        if resposta.status_code == 200 and resposta.content[:4] == b"%PDF":
            nome = f"focus_{data_tentativa.strftime('%Y-%m-%d')}.pdf"
            caminho = pasta / nome
            caminho.write_bytes(resposta.content)
            return data_tentativa, caminho

        # PDF não encontrado nesta data; recua um dia até achar a sexta de referência
        # mais recente (cobre fim de semana e feriados que adiam a publicação)
        data_tentativa -= timedelta(days=1)

    raise RuntimeError(
        f"Nenhum PDF encontrado nas {MAX_TENTATIVAS} tentativas a partir de "
        f"{inicio.strftime('%Y-%m-%d')}."
    )


def main() -> None:
    pasta_dados = Path(__file__).parent.parent / "data"
    data_pub, caminho = baixar(pasta_dados)
    tamanho_kb = caminho.stat().st_size / 1024
    print(f"Focus de {data_pub.strftime('%d/%m/%Y')} salvo em: {caminho}")
    print(f"Tamanho: {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
