"""Funções para salvar DataFrames em Excel já formatado."""

from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

FORMATO_MOEDA = '"R$" #,##0.00'
FORMATO_DECIMAL = "0.00"
FORMATO_PERCENTUAL = "0.0%"

COR_CABECALHO = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")


def salvar_excel(caminho, abas, formatos=None):
    """Salva um ou mais DataFrames num arquivo Excel, um por aba.

    abas: dicionário {nome da aba: DataFrame}
    formatos: dicionário {nome da coluna: formato numérico do Excel},
              aplicado em todas as abas que tiverem essa coluna.

    Cada aba sai com o cabeçalho em destaque, a primeira linha congelada
    e a largura das colunas ajustada ao conteúdo.
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    formatos = formatos or {}

    with pd.ExcelWriter(caminho, engine="openpyxl") as escritor:
        for nome_aba, tabela in abas.items():
            tabela.to_excel(escritor, sheet_name=nome_aba, index=False)
            planilha = escritor.sheets[nome_aba]

            for celula in planilha[1]:
                celula.font = Font(bold=True, color="FFFFFF")
                celula.fill = COR_CABECALHO
            planilha.freeze_panes = "A2"

            for indice, coluna in enumerate(tabela.columns, start=1):
                letra = get_column_letter(indice)

                if coluna in formatos:
                    for (celula,) in planilha.iter_rows(min_row=2, min_col=indice, max_col=indice):
                        celula.number_format = formatos[coluna]

                maior_texto = max([len(str(coluna))] + [len(str(valor)) for valor in tabela[coluna]])
                planilha.column_dimensions[letra].width = min(maior_texto + 4, 50)

    return caminho
