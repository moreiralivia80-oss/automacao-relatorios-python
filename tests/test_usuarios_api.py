"""Os testes não acessam a internet: a resposta da API é simulada com monkeypatch."""

import pandas as pd
import pytest
import requests

from automacao import usuarios_api
from automacao.usuarios_api import ErroAPI, buscar_usuarios, filtrar_por_cidade, gerar_relatorio_usuarios, montar_tabela

USUARIOS_FALSOS = [
    {"id": 1, "name": "Leanne Graham", "username": "Bret", "email": "leanne@exemplo.com",
     "address": {"city": "Gwenborough"}, "company": {"name": "Romaguera-Crona"}},
    {"id": 2, "name": "Ervin Howell", "username": "Antonette", "email": "ervin@exemplo.com",
     "address": {"city": "Wisokyburgh"}, "company": {"name": "Deckow-Crist"}},
    {"id": 3, "name": "Clementine Bauch", "username": "Samantha", "email": "clementine@exemplo.com",
     "address": {"city": "Gwenborough"}, "company": {"name": "Romaguera-Jacobson"}},
]


class RespostaFalsa:
    def __init__(self, dados, status=200):
        self._dados = dados
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} Error")

    def json(self):
        return self._dados


@pytest.fixture
def api_falsa(monkeypatch):
    monkeypatch.setattr(usuarios_api.requests, "get", lambda url, timeout: RespostaFalsa(USUARIOS_FALSOS))


def test_monta_tabela_com_campos_aninhados():
    tabela = montar_tabela(USUARIOS_FALSOS)
    assert list(tabela.columns) == ["Id", "Nome", "Usuario", "Email", "Cidade", "Empresa"]
    assert tabela["Nome"].tolist() == ["Clementine Bauch", "Ervin Howell", "Leanne Graham"]


def test_filtra_por_cidade_sem_diferenciar_maiusculas():
    tabela = filtrar_por_cidade(montar_tabela(USUARIOS_FALSOS), "gwenborough")
    assert len(tabela) == 2


def test_busca_usuarios(api_falsa):
    assert len(buscar_usuarios()) == 3


def test_erro_http_vira_erro_api(monkeypatch):
    monkeypatch.setattr(usuarios_api.requests, "get", lambda url, timeout: RespostaFalsa([], status=500))
    with pytest.raises(ErroAPI, match="500"):
        buscar_usuarios()


def test_sem_conexao_vira_erro_api(monkeypatch):
    def sem_internet(url, timeout):
        raise requests.exceptions.ConnectionError("sem conexão")

    monkeypatch.setattr(usuarios_api.requests, "get", sem_internet)
    with pytest.raises(ErroAPI, match="sem conexão"):
        buscar_usuarios()


def test_gera_excel_filtrado(api_falsa, tmp_path):
    saida = tmp_path / "usuarios.xlsx"
    gerar_relatorio_usuarios(saida, cidade="Gwenborough")

    usuarios = pd.read_excel(saida, sheet_name="Usuarios")
    por_cidade = pd.read_excel(saida, sheet_name="Por cidade")
    assert set(usuarios["Cidade"]) == {"Gwenborough"}
    assert por_cidade.set_index("Cidade").loc["Gwenborough", "Usuarios"] == 2
