"""Gera o resumo executivo do Boletim Focus via API da Anthropic.

Reproduz em código os passos do routine-prompt.md que podem ser
automatizados de forma confiável dentro do GitHub Actions:

  Passo 1 — localizar o texto mais recente em data/
  Passo 2 — verificar o frescor pela data do nome do arquivo
  Passo 3 — sanity check (tamanho mínimo + palavras-chave)
  Passo 4 — gerar o resumo (chamada à API da Anthropic)
  Passo 5 — salvar idempotente em output/focus/

A criação do rascunho de e-mail (Passo 6) continua a cargo da rotina
remota, que tem acesso ao conector do Gmail.

Requer a variável de ambiente ANTHROPIC_API_KEY.
"""

import argparse
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import anthropic

# A data do ambiente confirma este como o ID exato do Sonnet 4.6.
MODELO = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

TAMANHO_MINIMO = 2000
PALAVRAS_OBRIGATORIAS = ("IPCA", "Selic", "PIB")

# Regra de negócio central do projeto (CLAUDE.md): nenhum número pode ser
# inventado. O prompt do sistema reforça isso e fixa a estrutura do documento.
PROMPT_SISTEMA = """\
Você é um analista que resume o Boletim Focus do Banco Central do Brasil.

REGRA ABSOLUTA E INEGOCIÁVEL: nenhum número, percentual, mediana ou projeção
pode aparecer no resumo que não esteja LITERALMENTE escrito no texto fornecido.
É proibido estimar, interpolar, arredondar ou inferir qualquer valor. Em caso
de dúvida sobre um número, omita-o em vez de arriscar.

Você receberá o texto integral extraído do boletim. Produza EXATAMENTE as duas
seções abaixo, em Markdown, e NADA mais (sem título de nível 1, sem cabeçalho,
sem comentários antes ou depois):

## Medianas principais

Um resumo executivo de ATÉ 200 palavras com as medianas centrais, nesta ordem
de prioridade: IPCA (ano corrente e próximo ano), Selic (fim de ano), PIB (ano
corrente) e câmbio (fim de ano). Para cada indicador, diga se a mediana subiu,
caiu ou ficou estável em relação à edição anterior — mas SOMENTE se essa
comparação estiver presente no texto.

## Três principais revisões da semana

Liste as três revisões de expectativas mais relevantes, no formato:

**1. [Indicador] — de X% para Y%**
Hipótese de motivo: [uma frase com o possível gatilho, derivada apenas do
contexto do próprio texto. Se o texto não der pista suficiente, escreva
exatamente "Motivo não identificado no texto."]

**2. ...** (idem)

**3. ...** (idem)
"""


def texto_mais_recente(pasta_dados: Path) -> tuple[date, Path, str]:
    """Localiza o focus_*.txt de nome lexicograficamente maior (mais recente).

    Retorna (data_publicacao, caminho, conteudo). Levanta FileNotFoundError
    se não houver nenhum arquivo.
    """
    candidatos = sorted(pasta_dados.glob("focus_*.txt"))
    if not candidatos:
        raise FileNotFoundError(
            "Nenhum arquivo encontrado em data/. "
            "Execute primeiro o pipeline de download."
        )

    caminho = candidatos[-1]
    # focus_AAAA-MM-DD.txt → extrai a data do nome
    correspondencia = re.search(r"(\d{4})-(\d{2})-(\d{2})", caminho.stem)
    if not correspondencia:
        raise ValueError(f"Nome de arquivo fora do padrão esperado: {caminho.name}")

    ano, mes, dia = map(int, correspondencia.groups())
    data_pub = date(ano, mes, dia)
    conteudo = caminho.read_text(encoding="utf-8")
    return data_pub, caminho, conteudo


def verificar_frescor(data_pub: date, hoje: date) -> tuple[str | None, bool]:
    """Avalia a idade do boletim (Passo 2).

    Retorna (nota_de_frescor_ou_None, deve_parar).
    - 0 a 3 dias: prossegue sem nota.
    - 4 a 7 dias: prossegue, mas com nota de aviso no cabeçalho.
    - mais de 7 dias: deve parar.
    """
    dias = (hoje - data_pub).days
    if dias > 7:
        return None, True
    if dias >= 4:
        nota = f"⚠️ Texto com {dias} dias — verifique se há edição mais recente."
        return nota, False
    return None, False


def sanity_check(texto: str) -> tuple[bool, str]:
    """Verifica tamanho mínimo e presença das palavras-chave (Passo 3).

    Retorna (ok, motivo_da_falha). motivo é "" quando ok.
    """
    if len(texto) < TAMANHO_MINIMO:
        return False, f"texto com apenas {len(texto)} caracteres (mínimo {TAMANHO_MINIMO})"

    ausentes = [p for p in PALAVRAS_OBRIGATORIAS if p not in texto]
    if ausentes:
        return False, f"palavra(s) obrigatória(s) ausente(s): {', '.join(ausentes)}"

    return True, ""


def gerar_resumo(
    texto: str,
    data_pub: date,
    nota_frescor: str | None,
    client: anthropic.Anthropic,
) -> str:
    """Monta o documento Markdown completo (Passo 4).

    O cabeçalho é construído de forma determinística aqui; apenas o corpo
    (as duas seções de análise) vem da API.
    """
    resposta = client.messages.create(
        model=MODELO,
        max_tokens=1500,
        system=PROMPT_SISTEMA,
        messages=[
            {
                "role": "user",
                "content": (
                    "Texto integral do Boletim Focus a resumir:\n\n"
                    f"{texto}"
                ),
            }
        ],
    )
    corpo = resposta.content[0].text.strip()

    cabecalho = [
        f"# Focus — {data_pub.strftime('%d/%m/%Y')}",
        f"> Resumo gerado em {date.today().strftime('%Y-%m-%d')}.",
    ]
    if nota_frescor:
        cabecalho.append(nota_frescor)

    return "\n".join(cabecalho) + "\n\n" + corpo + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera o resumo executivo do Focus mais recente via API da Anthropic."
    )
    parser.add_argument(
        "--txt",
        metavar="CAMINHO",
        help="Caminho explícito para o .txt. Se omitido, usa o mais recente de data/.",
    )
    args = parser.parse_args()

    raiz = Path(__file__).parent.parent
    pasta_dados = raiz / "data"
    pasta_saida = raiz / "output" / "focus"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    # Passo 1 — localizar o texto
    try:
        if args.txt:
            caminho_txt = Path(args.txt)
            correspondencia = re.search(r"(\d{4})-(\d{2})-(\d{2})", caminho_txt.stem)
            if not correspondencia:
                print(f"Nome fora do padrão: {caminho_txt.name}", file=sys.stderr)
                sys.exit(1)
            ano, mes, dia = map(int, correspondencia.groups())
            data_pub = date(ano, mes, dia)
            texto = caminho_txt.read_text(encoding="utf-8")
        else:
            data_pub, caminho_txt, texto = texto_mais_recente(pasta_dados)
    except (FileNotFoundError, ValueError) as erro:
        print(str(erro), file=sys.stderr)
        sys.exit(1)

    print(f"Texto mais recente: {caminho_txt.name} (publicação {data_pub})")

    # Passo 5 (verificação antecipada) — idempotência
    destino = pasta_saida / f"focus_{data_pub.strftime('%Y-%m-%d')}.md"
    if destino.exists():
        print(f"Resumo para esta data já existe em {destino}. Nenhuma ação tomada.")
        return

    # Passo 2 — frescor
    nota_frescor, deve_parar = verificar_frescor(data_pub, date.today())
    if deve_parar:
        print(
            "Arquivo com mais de 7 dias. Rode novamente o pipeline de download "
            "antes de gerar o resumo.",
            file=sys.stderr,
        )
        sys.exit(1)
    if nota_frescor:
        print(f"Aviso de frescor: {nota_frescor}")

    # Passo 3 — sanity check
    ok, motivo = sanity_check(texto)
    if not ok:
        print(f"Sanity check falhou: {motivo}. Resumo não gerado.", file=sys.stderr)
        sys.exit(1)

    # Passo 4 — gerar (requer ANTHROPIC_API_KEY no ambiente)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY não definida. Configure o secret no repositório "
            "ou exporte a variável localmente.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.Anthropic()
    markdown = gerar_resumo(texto, data_pub, nota_frescor, client)

    # Passo 5 — salvar
    destino.write_text(markdown, encoding="utf-8")
    print(f"Resumo salvo em: {destino}")


if __name__ == "__main__":
    main()
