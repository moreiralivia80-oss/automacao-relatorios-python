"""Usuários de uma API: busca os usuários na API pública JSONPlaceholder,
organiza os dados, filtra por cidade (opcional) e gera um Excel."""

import pandas as pd
import requests

from automacao.excel import salvar_excel

URL_API = "https://jsonplaceholder.typicode.com/users"


class ErroAPI(Exception):
    """Erro ao buscar os dados na API."""


def buscar_usuarios(url=URL_API, timeout=10):
    """Faz a requisição GET e devolve a lista de usuários (JSON)."""
    try:
        resposta = requests.get(url, timeout=timeout)
        resposta.raise_for_status()  # gera erro se o status não for 2xx (ex.: 404, 500)
    except requests.exceptions.RequestException as erro:
        raise ErroAPI(f"Não foi possível acessar a API: {erro}") from erro

    dados = resposta.json()
    if not isinstance(dados, list):
        raise ErroAPI("A API devolveu um formato inesperado (era esperada uma lista).")
    return dados


def montar_tabela(dados):
    """Transforma o JSON em DataFrame só com as colunas que interessam.

    Os campos aninhados (address.city, company.name) viram colunas simples.
    """
    usuarios = pd.json_normalize(dados)
    tabela = usuarios[["id", "name", "username", "email", "address.city", "company.name"]].rename(
        columns={
            "id": "Id",
            "name": "Nome",
            "username": "Usuario",
            "email": "Email",
            "address.city": "Cidade",
            "company.name": "Empresa",
        }
    )
    return tabela.sort_values("Nome").reset_index(drop=True)


def filtrar_por_cidade(tabela, cidade):
    """Mantém só os usuários da cidade informada (sem diferenciar maiúsculas)."""
    return tabela[tabela["Cidade"].str.lower() == cidade.lower()].reset_index(drop=True)


def contar_por_cidade(tabela):
    """Conta quantos usuários existem em cada cidade."""
    return tabela["Cidade"].value_counts().rename_axis("Cidade").reset_index(name="Usuarios")


def gerar_relatorio_usuarios(caminho_saida, cidade=None, url=URL_API):
    """Executa a automação completa e devolve os números principais."""
    tabela = montar_tabela(buscar_usuarios(url))
    por_cidade = contar_por_cidade(tabela)

    if cidade:
        tabela = filtrar_por_cidade(tabela, cidade)

    salvar_excel(caminho_saida, {"Usuarios": tabela, "Por cidade": por_cidade})

    return {"usuarios": tabela, "por_cidade": por_cidade}

