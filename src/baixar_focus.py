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


def ultima_segunda(hoje: date) -> date:
    """Retorna a segunda-feira mais recente ESTRITAMENTE anterior a `hoje`.

    Se hoje já for segunda-feira, retrocede para a segunda da semana passada.
    """
    # weekday(): segunda=0 … domingo=6
    # Segunda (0) → recua 7 dias; qualquer outro dia → recua weekday() dias
    dias_ate_segunda_passada = 7 if hoje.weekday() == 0 else hoje.weekday()
    return hoje - timedelta(days=dias_ate_segunda_passada)


def baixar(dest: str | Path) -> tuple[date, Path]:
    """Baixa o PDF do Focus mais recente e salva em `dest`.

    Parte da última segunda-feira e recua um dia por tentativa (até MAX_TENTATIVAS),
    o que cobre feriados prolongados. Valida que o arquivo é um PDF real (%PDF)
    antes de salvar.

    Retorna (data_publicacao, caminho_arquivo) ou levanta RuntimeError.
    """
    pasta = Path(dest)
    pasta.mkdir(parents=True, exist_ok=True)

    data_tentativa = ultima_segunda(date.today())

    for _ in range(MAX_TENTATIVAS):
        url = URL_BASE.format(data=data_tentativa.strftime("%Y%m%d"))

        resposta = requests.get(url, headers=CABECALHO, timeout=30, verify=False)

        if resposta.status_code == 200 and resposta.content[:4] == b"%PDF":
            nome = f"focus_{data_tentativa.strftime('%Y-%m-%d')}.pdf"
            caminho = pasta / nome
            caminho.write_bytes(resposta.content)
            return data_tentativa, caminho

        # PDF não encontrado nesta data; avança um dia (cobre feriados que adiam
        # a publicação de segunda para terça, quarta... como descrito no CLAUDE.md)
        data_tentativa += timedelta(days=1)

    raise RuntimeError(
        f"Nenhum PDF encontrado nas {MAX_TENTATIVAS} tentativas a partir de "
        f"{(ultima_segunda(date.today())).strftime('%Y-%m-%d')}."
    )


def main() -> None:
    pasta_dados = Path(__file__).parent.parent / "data"
    data_pub, caminho = baixar(pasta_dados)
    tamanho_kb = caminho.stat().st_size / 1024
    print(f"Focus de {data_pub.strftime('%d/%m/%Y')} salvo em: {caminho}")
    print(f"Tamanho: {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
