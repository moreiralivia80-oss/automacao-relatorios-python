"""Relatório de vendas: lê um CSV de vendas e gera um Excel com o faturamento
por produto e por mês."""

import pandas as pd

from automacao.excel import FORMATO_MOEDA, FORMATO_PERCENTUAL, salvar_excel

COLUNAS_OBRIGATORIAS = ["Data", "Produto", "Quantidade", "PrecoUnitario"]


def carregar_vendas(caminho):
    """Lê o CSV de vendas e confere se os dados estão válidos."""
    vendas = pd.read_csv(caminho, parse_dates=["Data"])

    faltando = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in vendas.columns]
    if faltando:
        raise ValueError(f"O arquivo de vendas não tem as colunas: {', '.join(faltando)}")

    invalidas = vendas[(vendas["Quantidade"] <= 0) | (vendas["PrecoUnitario"] <= 0)]
    if not invalidas.empty:
        # +2 porque o índice começa em 0 e a linha 1 do CSV é o cabeçalho
        linhas = ", ".join(str(indice + 2) for indice in invalidas.index)
        raise ValueError(f"Quantidade ou preço menor ou igual a zero nas linhas: {linhas}")

    return vendas


def calcular_faturamento(vendas):
    """Adiciona a coluna Faturamento (quantidade x preço) em cada venda."""
    vendas = vendas.copy()
    vendas["Faturamento"] = vendas["Quantidade"] * vendas["PrecoUnitario"]
    return vendas


def resumo_por_produto(vendas):
    """Soma quantidade e faturamento de cada produto, do maior para o menor faturamento."""
    resumo = (
        vendas.groupby("Produto", as_index=False)[["Quantidade", "Faturamento"]]
        .sum()
        .sort_values("Faturamento", ascending=False)
        .reset_index(drop=True)
    )
    resumo["Participacao"] = (resumo["Faturamento"] / resumo["Faturamento"].sum()).round(4)
    return resumo


def resumo_por_mes(vendas):
    """Soma o faturamento e conta as vendas de cada mês."""
    resumo = (
        vendas.assign(Mes=vendas["Data"].dt.strftime("%Y-%m"))
        .groupby("Mes", as_index=False)
        .agg(Vendas=("Produto", "count"), Quantidade=("Quantidade", "sum"), Faturamento=("Faturamento", "sum"))
    )
    return resumo


def gerar_relatorio_vendas(caminho_entrada, caminho_saida):
    """Executa a automação completa e devolve os números principais."""
    vendas = calcular_faturamento(carregar_vendas(caminho_entrada))
    por_produto = resumo_por_produto(vendas)
    por_mes = resumo_por_mes(vendas)

    detalhe = vendas.assign(Data=vendas["Data"].dt.strftime("%d/%m/%Y"))

    salvar_excel(
        caminho_saida,
        {"Por produto": por_produto, "Por mês": por_mes, "Vendas": detalhe},
        formatos={
            "PrecoUnitario": FORMATO_MOEDA,
            "Faturamento": FORMATO_MOEDA,
            "Participacao": FORMATO_PERCENTUAL,
        },
    )

    return {
        "vendas": len(vendas),
        "faturamento_total": float(vendas["Faturamento"].sum()),
        "produto_mais_vendido": por_produto.loc[0, "Produto"],
        "por_produto": por_produto,
    }
