"""Testes para src/baixar_focus.py."""

import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
import requests

# Permite importar os módulos de src/ sem instalar o pacote
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import baixar_focus
from baixar_focus import baixar


# ---------------------------------------------------------------------------
# Infra de teste offline — simula o requests.get sem acessar a rede
# ---------------------------------------------------------------------------

class _FakeResp:
    def __init__(self, status_code: int, content: bytes, headers: dict | None = None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


def _data_da_url(url: str) -> date:
    """Extrai a data AAAAMMDD do padrão R<AAAAMMDD>.pdf na URL."""
    m = re.search(r"R(\d{8})\.pdf", url)
    return datetime.strptime(m.group(1), "%Y%m%d").date()


def _fake_get_factory(datas_com_pdf: set[date]):
    """Devolve um fake de requests.get que só serve %PDF nas datas informadas."""
    def fake_get(url, **kwargs):
        d = _data_da_url(url)
        if d in datas_com_pdf:
            return _FakeResp(200, b"%PDF-1.7 conteudo simulado")
        return _FakeResp(404, b"<html>nao encontrado</html>")
    return fake_get


# ---------------------------------------------------------------------------
# Testes offline — baixar() recua a partir de hoje até achar a sexta de referência
# ---------------------------------------------------------------------------

def test_baixar_recua_ate_a_sexta(tmp_path, monkeypatch):
    # Hoje = quinta 2026-06-18; PDF só existe na sexta anterior 2026-06-12
    hoje = date(2026, 6, 18)
    sexta = date(2026, 6, 12)
    monkeypatch.setattr(baixar_focus.requests, "get", _fake_get_factory({sexta}))

    data_pub, caminho = baixar(tmp_path, hoje=hoje)

    assert data_pub == sexta
    assert caminho.name == "focus_2026-06-12.pdf"
    assert caminho.exists()
    assert caminho.read_bytes()[:4] == b"%PDF"


def test_baixar_para_na_primeira_data_valida(tmp_path, monkeypatch):
    # Se hoje já tem PDF, deve parar em hoje sem recuar
    hoje = date(2026, 6, 12)
    monkeypatch.setattr(baixar_focus.requests, "get", _fake_get_factory({hoje}))

    data_pub, caminho = baixar(tmp_path, hoje=hoje)

    assert data_pub == hoje
    assert caminho.name == "focus_2026-06-12.pdf"


def test_baixar_levanta_quando_nada_encontrado(tmp_path, monkeypatch):
    # Nenhuma data tem PDF → estoura RuntimeError após MAX_TENTATIVAS
    monkeypatch.setattr(baixar_focus.requests, "get", _fake_get_factory(set()))

    with pytest.raises(RuntimeError, match="Nenhum PDF encontrado"):
        baixar(tmp_path, hoje=date(2026, 6, 18))


def test_baixar_ignora_status_200_que_nao_e_pdf(tmp_path, monkeypatch):
    # Site pode responder 200 com HTML; só conteúdo iniciando em %PDF vale.
    # Cada data não-PDF é retentada (transitório) e depois recua; sleep no-op
    # mantém o teste rápido.
    def fake_get(url, **kwargs):
        d = _data_da_url(url)
        if d == date(2026, 6, 12):
            return _FakeResp(200, b"%PDF-1.7 ok")
        return _FakeResp(200, b"<html>pagina de erro</html>")
    monkeypatch.setattr(baixar_focus.requests, "get", fake_get)

    data_pub, _ = baixar(tmp_path, hoje=date(2026, 6, 18), sleep=lambda *_: None)
    assert data_pub == date(2026, 6, 12)


def test_baixar_repete_em_erro_transitorio_e_sucede(tmp_path, monkeypatch):
    # O BCB responde 5xx nas primeiras vezes para a SEXTA e o PDF em seguida
    # (soluço transitório). Deve retentar a MESMA data e NÃO recuar para uma
    # edição mais antiga.
    sexta = date(2026, 6, 12)
    estado = {"falhas_restantes": 2}

    def fake_get(url, **kwargs):
        d = _data_da_url(url)
        if d != sexta:
            return _FakeResp(404, b"")
        if estado["falhas_restantes"] > 0:
            estado["falhas_restantes"] -= 1
            return _FakeResp(503, b"<html>indisponivel</html>")
        return _FakeResp(200, b"%PDF-1.7 ok")
    monkeypatch.setattr(baixar_focus.requests, "get", fake_get)

    data_pub, caminho = baixar(tmp_path, hoje=sexta, sleep=lambda *_: None)

    assert data_pub == sexta  # retentou a mesma data, não recuou
    assert caminho.read_bytes()[:4] == b"%PDF"


def test_baixar_repete_em_erro_de_rede(tmp_path, monkeypatch):
    # Exceção de rede (timeout/conexão) é transitória: deve retentar em vez de
    # derrubar o processo.
    sexta = date(2026, 6, 12)
    estado = {"falhas_restantes": 1}

    def fake_get(url, **kwargs):
        d = _data_da_url(url)
        if d != sexta:
            return _FakeResp(404, b"")
        if estado["falhas_restantes"] > 0:
            estado["falhas_restantes"] -= 1
            raise requests.exceptions.ConnectionError("timeout simulado")
        return _FakeResp(200, b"%PDF-1.7 ok")
    monkeypatch.setattr(baixar_focus.requests, "get", fake_get)

    data_pub, _ = baixar(tmp_path, hoje=sexta, sleep=lambda *_: None)

    assert data_pub == sexta


# ---------------------------------------------------------------------------
# Teste com rede — baixar() real contra o site do BCB
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
