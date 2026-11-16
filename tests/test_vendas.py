import pandas as pd
import pytest
from openpyxl import load_workbook

from automacao.vendas import calcular_faturamento, carregar_vendas, gerar_relatorio_vendas, resumo_por_produto


@pytest.fixture
def csv_vendas(tmp_path):
    caminho = tmp_path / "vendas.csv"
    caminho.write_text(
        "Data,Produto,Quantidade,PrecoUnitario\n"
        "2026-01-10,Mouse,10,40\n"
        "2026-01-20,Monitor,3,800\n"
        "2026-02-05,Mouse,5,40\n",
        encoding="utf-8",
    )
    return caminho


def test_faturamento_e_quantidade_vezes_preco(csv_vendas):
    vendas = calcular_faturamento(carregar_vendas(csv_vendas))
    assert vendas["Faturamento"].tolist() == [400, 2400, 200]


def test_resumo_ordena_pelo_maior_faturamento(csv_vendas):
    resumo = resumo_por_produto(calcular_faturamento(carregar_vendas(csv_vendas)))
    assert resumo["Produto"].tolist() == ["Monitor", "Mouse"]
    assert resumo.loc[1, "Quantidade"] == 15
    assert resumo["Participacao"].sum() == pytest.approx(1.0)


def test_coluna_faltando_gera_erro(tmp_path):
    caminho = tmp_path / "vendas.csv"
    caminho.write_text("Data,Produto,Quantidade\n2026-01-10,Mouse,10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PrecoUnitario"):
        carregar_vendas(caminho)


def test_quantidade_invalida_informa_a_linha(tmp_path):
    caminho = tmp_path / "vendas.csv"
    caminho.write_text(
        "Data,Produto,Quantidade,PrecoUnitario\n2026-01-10,Mouse,10,40\n2026-01-11,Mouse,0,40\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="linhas: 3"):
        carregar_vendas(caminho)


def test_gera_excel_com_as_tres_abas(csv_vendas, tmp_path):
    saida = tmp_path / "relatorio.xlsx"
    resultado = gerar_relatorio_vendas(csv_vendas, saida)

    assert resultado["faturamento_total"] == 3000
    assert load_workbook(saida).sheetnames == ["Por produto", "Por mês", "Vendas"]
    por_mes = pd.read_excel(saida, sheet_name="Por mês")
    assert por_mes["Faturamento"].tolist() == [2800, 200]
