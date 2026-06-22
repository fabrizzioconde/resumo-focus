"""Baixa o PDF mais recente do Boletim Focus do Banco Central do Brasil."""

import logging
import time
from datetime import date, timedelta
from pathlib import Path

import requests
import urllib3

URL_BASE = "https://www.bcb.gov.br/content/focus/focus/R{data}.pdf"
CABECALHO = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Janela de recuo a partir de hoje. Precisa ser grande o bastante para, partindo
# de uma segunda-feira, alcançar a sexta de referência ANTERIOR caso a mais
# recente ainda não exista (feriado prolongado): essa sexta fica a ~10 dias.
MAX_DIAS = 12

# Tentativas por data para erros TRANSITÓRIOS: 5xx, falha de rede ou um 200 que
# não é PDF (típico de bloqueio/WAF ou indisponibilidade momentânea do BCB).
# Um 404 NÃO é transitório — significa "não há PDF nesta data" e leva ao recuo
# imediato, sem retentativa.
TENTATIVAS_TRANSIENTE = 4
ESPERA_BASE = 2.0  # segundos; backoff incremental entre tentativas transitórias

logger = logging.getLogger(__name__)

# O BCB usa certificado com cadeia intermediária ausente no bundle padrão do
# Python no Windows; verify=False contorna isso para este domínio conhecido.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Sentinela: a data consultada respondeu 404 (não existe PDF para ela).
_NAO_EXISTE = object()


def _tentar_data(url: str, sleep) -> bytes | object | None:
    """Tenta baixar o PDF de UMA data, com retentativas para erros transitórios.

    Retorna:
      - os bytes do PDF, se obteve 200 com assinatura %PDF;
      - _NAO_EXISTE, se o servidor respondeu 404 (não há PDF nessa data);
      - None, se houve apenas erros transitórios e as tentativas se esgotaram.
    """
    for tentativa in range(1, TENTATIVAS_TRANSIENTE + 1):
        try:
            resposta = requests.get(url, headers=CABECALHO, timeout=30, verify=False)
        except requests.RequestException as erro:
            # Timeout, conexão recusada, DNS etc. — transitório: vale retentar.
            logger.warning(
                "Erro de rede em %s (tentativa %d/%d): %s",
                url, tentativa, TENTATIVAS_TRANSIENTE, erro,
            )
        else:
            if resposta.status_code == 404:
                return _NAO_EXISTE

            if resposta.status_code == 200 and resposta.content[:4] == b"%PDF":
                return resposta.content

            # 200 sem %PDF, 5xx, 403... — provável bloqueio/erro momentâneo do
            # BCB. Loga status e início do corpo para tornar a falha diagnosticável.
            logger.warning(
                "Resposta não-PDF em %s (tentativa %d/%d): status=%s, "
                "content-type=%s, inicio=%r",
                url, tentativa, TENTATIVAS_TRANSIENTE, resposta.status_code,
                resposta.headers.get("Content-Type", "?"), resposta.content[:60],
            )

        if tentativa < TENTATIVAS_TRANSIENTE:
            sleep(ESPERA_BASE * tentativa)  # backoff: 2s, 4s, 6s...

    return None


def baixar(
    dest: str | Path,
    hoje: date | None = None,
    sleep=time.sleep,
) -> tuple[date, Path]:
    """Baixa o PDF do Focus mais recente e salva em `dest`.

    O arquivo no site do BCB tem como data a SEXTA-FEIRA de referência da pesquisa
    (embora o relatório seja disponibilizado na segunda seguinte). Por isso a busca
    parte de hoje e RECUA um dia por vez (até MAX_DIAS), encontrando a sexta mais
    recente com PDF publicado — o recuo também cobre fins de semana e feriados que
    adiam a data de referência. Valida que o arquivo é um PDF real (%PDF).

    Para cada data, erros transitórios (5xx, falha de rede, 200 sem %PDF) são
    retentados com backoff antes de desistir daquela data; um 404 recua de imediato.
    A trava de frescor do resumidor (resumir_focus.py) é a rede de segurança caso o
    recuo alcance, em um cenário de indisponibilidade prolongada, uma edição antiga.

    `hoje` fixa a data de partida em testes; `sleep` é injetável para neutralizar o
    backoff nos testes. Em produção usam date.today() e time.sleep.

    Retorna (data_publicacao, caminho_arquivo) ou levanta RuntimeError.
    """
    pasta = Path(dest)
    pasta.mkdir(parents=True, exist_ok=True)

    inicio = hoje or date.today()

    for deslocamento in range(MAX_DIAS):
        data_tentativa = inicio - timedelta(days=deslocamento)
        url = URL_BASE.format(data=data_tentativa.strftime("%Y%m%d"))

        resultado = _tentar_data(url, sleep)

        if resultado is _NAO_EXISTE:
            logger.info("%s: sem PDF (404); recuando um dia.", data_tentativa)
            continue

        if resultado is None:
            logger.warning(
                "%s: falhas transitórias esgotadas; recuando um dia.", data_tentativa
            )
            continue

        nome = f"focus_{data_tentativa.strftime('%Y-%m-%d')}.pdf"
        caminho = pasta / nome
        caminho.write_bytes(resultado)
        logger.info(
            "PDF de %s salvo (%d bytes) em %s.", data_tentativa, len(resultado), caminho
        )
        return data_tentativa, caminho

    raise RuntimeError(
        f"Nenhum PDF encontrado nos {MAX_DIAS} dias a partir de "
        f"{inicio.strftime('%Y-%m-%d')}."
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    pasta_dados = Path(__file__).parent.parent / "data"
    data_pub, caminho = baixar(pasta_dados)
    tamanho_kb = caminho.stat().st_size / 1024
    print(f"Focus de {data_pub.strftime('%d/%m/%Y')} salvo em: {caminho}")
    print(f"Tamanho: {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
