"""Ponto de entrada das automações.

Uso:
    python main.py vendas
    python main.py notas
    python main.py usuarios --cidade Gwenborough

Use "python main.py <automação> --help" para ver todas as opções.
"""

import argparse
import sys
from pathlib import Path

from automacao.notas import MEDIA_APROVACAO, gerar_boletim
from automacao.usuarios_api import ErroAPI, gerar_relatorio_usuarios
from automacao.vendas import gerar_relatorio_vendas

PASTA_PROJETO = Path(__file__).parent
PASTA_DADOS = PASTA_PROJETO / "dados"
PASTA_SAIDA = PASTA_PROJETO / "saida"


def moeda(valor):
    """Formata um número no padrão brasileiro: R$ 1.234,56."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def percentual(valor):
    """Formata uma fração no padrão brasileiro: 0.563 -> 56,3%."""
    return f"{valor:.1%}".replace(".", ",")


def executar_vendas(args):
    resultado = gerar_relatorio_vendas(args.entrada, args.saida)
    print(f"Vendas processadas: {resultado['vendas']}")
    print(f"Faturamento total: {moeda(resultado['faturamento_total'])}")
    print(f"Produto com maior faturamento: {resultado['produto_mais_vendido']}")
    print()
    for _, linha in resultado["por_produto"].iterrows():
        print(f"  {linha['Produto']:<10} {moeda(linha['Faturamento']):>14}  ({percentual(linha['Participacao'])})")


def executar_notas(args):
    resultado = gerar_boletim(args.entrada, args.saida, args.media)
    for _, linha in resultado["boletim"].iterrows():
        media = f"{linha['Media']:.2f}".replace(".", ",")
        print(f"  {linha['Nome']:<10} média {media:>5}  {linha['Situacao']}")
    print()
    for _, linha in resultado["resumo"].iterrows():
        print(f"{linha['Indicador']}: {linha['Valor']:g}".replace(".", ","))


def executar_usuarios(args):
    resultado = gerar_relatorio_usuarios(args.saida, cidade=args.cidade)
    usuarios = resultado["usuarios"]
    filtro = f" da cidade {args.cidade}" if args.cidade else ""
    print(f"Usuários encontrados{filtro}: {len(usuarios)}")
    for _, linha in usuarios.iterrows():
        print(f"  {linha['Nome']:<26} {linha['Email']:<28} {linha['Cidade']}")


def criar_parser():
    parser = argparse.ArgumentParser(description="Automações de relatórios em Excel com Python e Pandas.")
    subparsers = parser.add_subparsers(dest="automacao", required=True, metavar="automação")

    vendas = subparsers.add_parser("vendas", help="relatório de faturamento a partir de um CSV de vendas")
    vendas.add_argument("--entrada", type=Path, default=PASTA_DADOS / "vendas.csv", help="CSV de vendas")
    vendas.add_argument("--saida", type=Path, default=PASTA_SAIDA / "relatorio_vendas.xlsx", help="Excel gerado")
    vendas.set_defaults(funcao=executar_vendas)

    notas = subparsers.add_parser("notas", help="boletim com média e situação de cada aluno")
    notas.add_argument("--entrada", type=Path, default=PASTA_DADOS / "alunos.csv", help="CSV de notas")
    notas.add_argument("--saida", type=Path, default=PASTA_SAIDA / "boletim_alunos.xlsx", help="Excel gerado")
    notas.add_argument("--media", type=float, default=MEDIA_APROVACAO,
                       help=f"média mínima para aprovação (padrão: {MEDIA_APROVACAO})")
    notas.set_defaults(funcao=executar_notas)

    usuarios = subparsers.add_parser("usuarios", help="usuários da API JSONPlaceholder exportados para Excel")
    usuarios.add_argument("--cidade", help="filtra os usuários por cidade (ex.: Gwenborough)")
    usuarios.add_argument("--saida", type=Path, default=PASTA_SAIDA / "usuarios.xlsx", help="Excel gerado")
    usuarios.set_defaults(funcao=executar_usuarios)

    return parser


def main(argumentos=None):
    args = criar_parser().parse_args(argumentos)
    try:
        args.funcao(args)
    except (FileNotFoundError, ValueError, ErroAPI) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"Erro: não foi possível salvar {args.saida}. O arquivo está aberto no Excel?", file=sys.stderr)
        return 1

    saida = args.saida.resolve()
    if saida.is_relative_to(Path.cwd()):
        saida = saida.relative_to(Path.cwd())
    print(f"\nRelatório salvo em: {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
