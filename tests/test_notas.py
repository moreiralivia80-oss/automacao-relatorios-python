import pandas as pd
import pytest

from automacao.notas import calcular_situacao, carregar_notas, gerar_boletim, resumo_da_turma


@pytest.fixture
def csv_notas(tmp_path):
    caminho = tmp_path / "alunos.csv"
    caminho.write_text("Nome,Nota1,Nota2\nAna,8,9\nBruno,5,6\nCamila,7,7\n", encoding="utf-8")
    return caminho


def test_media_e_situacao(csv_notas):
    boletim = calcular_situacao(carregar_notas(csv_notas)).set_index("Nome")
    assert boletim.loc["Ana", "Media"] == 8.5
    assert boletim.loc["Ana", "Situacao"] == "Aprovado"
    assert boletim.loc["Bruno", "Situacao"] == "Reprovado"


def test_media_exatamente_igual_a_minima_aprova(csv_notas):
    boletim = calcular_situacao(carregar_notas(csv_notas)).set_index("Nome")
    assert boletim.loc["Camila", "Situacao"] == "Aprovado"


def test_media_minima_personalizada(csv_notas):
    boletim = calcular_situacao(carregar_notas(csv_notas), media_aprovacao=5.0).set_index("Nome")
    assert boletim.loc["Bruno", "Situacao"] == "Aprovado"


def test_nota_fora_do_intervalo_gera_erro(tmp_path):
    caminho = tmp_path / "alunos.csv"
    caminho.write_text("Nome,Nota1,Nota2\nAna,8,11\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Ana"):
        carregar_notas(caminho)


def test_resumo_da_turma(csv_notas):
    resumo = resumo_da_turma(calcular_situacao(carregar_notas(csv_notas))).set_index("Indicador")
    assert resumo.loc["Aprovados", "Valor"] == 2
    assert resumo.loc["Reprovados", "Valor"] == 1


def test_gera_excel(csv_notas, tmp_path):
    saida = tmp_path / "boletim.xlsx"
    gerar_boletim(csv_notas, saida)
    boletim = pd.read_excel(saida, sheet_name="Boletim")
    assert boletim["Nome"].tolist() == ["Ana", "Camila", "Bruno"]
