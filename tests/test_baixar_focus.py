"""Testes para src/baixar_focus.py."""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

# Permite importar os módulos de src/ sem instalar o pacote
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from baixar_focus import ultima_segunda, baixar


# ---------------------------------------------------------------------------
# Testes offline (sem rede) — ultima_segunda
# ---------------------------------------------------------------------------

def test_ultima_segunda_quinta():
    # 2026-06-04 é quinta-feira (weekday=3); segunda da mesma semana é 2026-06-01
    assert ultima_segunda(date(2026, 6, 4)) == date(2026, 6, 1)


def test_ultima_segunda_terca():
    # 2026-06-02 é terça-feira (weekday=1); segunda da mesma semana é 2026-06-01
    assert ultima_segunda(date(2026, 6, 2)) == date(2026, 6, 1)


def test_ultima_segunda_quando_hoje_e_segunda():
    # 2026-06-01 é segunda-feira; deve recuar uma semana inteira para 2026-05-25
    assert ultima_segunda(date(2026, 6, 1)) == date(2026, 5, 25)


def test_ultima_segunda_domingo():
    # 2026-05-31 é domingo (weekday=6); segunda da mesma semana é 2026-05-25
    assert ultima_segunda(date(2026, 5, 31)) == date(2026, 5, 25)


def test_ultima_segunda_varredura_60_dias():
    # Para qualquer dia em uma janela de 60 dias:
    #   1. o resultado deve ser uma segunda-feira (weekday == 0)
    #   2. o resultado deve ser ESTRITAMENTE anterior à data dada
    base = date(2026, 6, 1)
    for offset in range(60):
        hoje = base + timedelta(days=offset)
        resultado = ultima_segunda(hoje)
        assert resultado.weekday() == 0, (
            f"{hoje} ({hoje.strftime('%A')}): "
            f"esperava segunda, obteve {resultado} ({resultado.strftime('%A')})"
        )
        assert resultado < hoje, (
            f"{hoje}: resultado {resultado} não é estritamente anterior"
        )


# ---------------------------------------------------------------------------
# Teste com rede — baixar()
# ---------------------------------------------------------------------------

@pytest.mark.network
def test_baixar_retorna_pdf_valido(tmp_path):
    """Faz o download real e valida o arquivo recebido."""
    data_pub, caminho = baixar(tmp_path)

    # Arquivo existe no disco
    assert caminho.exists()

    # Conteúdo começa com a assinatura de PDF
    assert caminho.read_bytes()[:4] == b"%PDF"

    # Tamanho mínimo razoável para um boletim Focus
    assert caminho.stat().st_size > 50 * 1024, "PDF menor que 50 KB — suspeito"

    # Nome do arquivo corresponde à data retornada
    assert caminho.name == f"focus_{data_pub.strftime('%Y-%m-%d')}.pdf"

    # Data está dentro da janela esperada: não é futura nem muito antiga
    hoje = date.today()
    assert data_pub <= hoje, "Data de publicação no futuro"
    assert data_pub >= hoje - timedelta(days=14), "Data de publicação muito antiga"
