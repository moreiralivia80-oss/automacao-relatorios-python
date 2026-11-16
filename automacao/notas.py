"""Boletim de notas: lê as notas dos alunos, calcula a média e a situação de
cada um e gera um Excel com o boletim e o resumo da turma."""

import pandas as pd

from automacao.excel import FORMATO_DECIMAL, salvar_excel

MEDIA_APROVACAO = 7.0
COLUNAS_NOTAS = ["Nota1", "Nota2"]


def carregar_notas(caminho):
    """Lê o CSV de notas e confere se todas estão entre 0 e 10."""
    alunos = pd.read_csv(caminho)

    faltando = [coluna for coluna in ["Nome", *COLUNAS_NOTAS] if coluna not in alunos.columns]
    if faltando:
        raise ValueError(f"O arquivo de notas não tem as colunas: {', '.join(faltando)}")

    fora_da_faixa = alunos[~alunos[COLUNAS_NOTAS].apply(lambda nota: nota.between(0, 10)).all(axis=1)]
    if not fora_da_faixa.empty:
        nomes = ", ".join(fora_da_faixa["Nome"])
        raise ValueError(f"Notas fora do intervalo de 0 a 10 para: {nomes}")

    return alunos


def calcular_situacao(alunos, media_aprovacao=MEDIA_APROVACAO):
    """Adiciona a média e a situação (Aprovado ou Reprovado) de cada aluno."""
    alunos = alunos.copy()
    alunos["Media"] = alunos[COLUNAS_NOTAS].mean(axis=1).round(2)
    alunos["Situacao"] = alunos["Media"].apply(
        lambda media: "Aprovado" if media >= media_aprovacao else "Reprovado"
    )
    return alunos.sort_values("Media", ascending=False).reset_index(drop=True)


def resumo_da_turma(boletim):
    """Monta uma tabela com os números gerais da turma."""
    aprovados = int((boletim["Situacao"] == "Aprovado").sum())
    total = len(boletim)
    return pd.DataFrame(
        {
            "Indicador": ["Total de alunos", "Aprovados", "Reprovados", "Taxa de aprovação (%)", "Média da turma"],
            "Valor": [total, aprovados, total - aprovados, round(aprovados / total * 100, 1), round(boletim["Media"].mean(), 2)],
        }
    )


def gerar_boletim(caminho_entrada, caminho_saida, media_aprovacao=MEDIA_APROVACAO):
    """Executa a automação completa e devolve os números principais."""
    boletim = calcular_situacao(carregar_notas(caminho_entrada), media_aprovacao)
    resumo = resumo_da_turma(boletim)

    salvar_excel(
        caminho_saida,
        {"Boletim": boletim, "Resumo": resumo},
        formatos={"Nota1": FORMATO_DECIMAL, "Nota2": FORMATO_DECIMAL, "Media": FORMATO_DECIMAL},
    )

    return {"boletim": boletim, "resumo": resumo}

