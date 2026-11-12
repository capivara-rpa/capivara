"""Operações com dados (pandas) com cara de low-code.

Tudo loga no terminal e devolve resultados fáceis de usar::

    from core.rpa.dados import ler_csv, escrever_excel, mostrar_df

    df = ler_csv("data/input/clientes.csv")
    mostrar_df(df)
    escrever_excel(df, "data/output/clientes.xlsx")
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger
from rich.console import Console
from rich.table import Table

_console = Console()


# ----------------------------------------------------------------------
# Leitura
# ----------------------------------------------------------------------
def ler_csv(caminho: str | Path, separador: str = ",", codificacao: str = "utf-8", **kwargs) -> pd.DataFrame:
    """Lê um arquivo CSV e retorna um DataFrame."""
    caminho = Path(caminho)
    df = pd.read_csv(caminho, sep=separador, encoding=codificacao, **kwargs)
    logger.success(f"CSV lido: {caminho.name} ({len(df)} linhas)")
    return df


def ler_excel(caminho: str | Path, aba: str | int = 0, cabecalho: int = 0, **kwargs) -> pd.DataFrame:
    """Lê uma aba de um arquivo Excel (.xlsx) e retorna um DataFrame."""
    caminho = Path(caminho)
    df = pd.read_excel(caminho, sheet_name=aba, header=cabecalho, **kwargs)
    logger.success(f"Planilha lida: {caminho.name} / aba '{aba}' ({len(df)} linhas)")
    return df


def ler_json(caminho: str | Path, orientacao: str = "records", **kwargs) -> pd.DataFrame:
    """Lê um arquivo JSON e retorna um DataFrame."""
    caminho = Path(caminho)
    df = pd.read_json(caminho, orient=orientacao, **kwargs)
    logger.success(f"JSON lido: {caminho.name} ({len(df)} linhas)")
    return df


def listar_abas_excel(caminho: str | Path) -> list[str]:
    """Lista os nomes das abas de uma planilha Excel."""
    caminho = Path(caminho)
    abas = pd.ExcelFile(caminho).sheet_names
    logger.info(f"Abas encontradas em {caminho.name}: {abas}")
    return abas


# ----------------------------------------------------------------------
# Escrita
# ----------------------------------------------------------------------
def escrever_csv(df: pd.DataFrame, caminho: str | Path, separador: str = ";", codificacao: str = "utf-8-sig", **kwargs) -> Path:
    """Salva um DataFrame como CSV. O separador padrão é ``;`` (Excel BR)."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, sep=separador, encoding=codificacao, index=False, **kwargs)
    logger.success(f"CSV salvo: {caminho} ({len(df)} linhas)")
    return caminho


def escrever_excel(df: pd.DataFrame, caminho: str | Path, aba: str = "Dados", **kwargs) -> Path:
    """Salva um DataFrame em uma aba de um arquivo Excel."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(caminho, sheet_name=aba, index=False, **kwargs)
    logger.success(f"Planilha salva: {caminho} / aba '{aba}' ({len(df)} linhas)")
    return caminho


def escrever_planilha(abas: dict[str, pd.DataFrame], caminho: str | Path) -> Path:
    """Salva várias abas em um único arquivo Excel.

    Exemplo: ``escrever_planilha({"Clientes": df1, "Resumo": df2}, caminho)``
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(caminho, engine="openpyxl") as escritor:
        for nome_aba, df in abas.items():
            df.to_excel(escritor, sheet_name=nome_aba[:31], index=False)
    logger.success(f"Planilha com {len(abas)} abas salva: {caminho}")
    return caminho


def escrever_json(df: pd.DataFrame, caminho: str | Path, orientacao: str = "records") -> Path:
    """Salva um DataFrame como JSON."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(caminho, orient=orientacao, force_ascii=False, indent=2)
    logger.success(f"JSON salvo: {caminho}")
    return caminho


# ----------------------------------------------------------------------
# Exploração / visualização
# ----------------------------------------------------------------------
def mostrar_df(df: pd.DataFrame, colunas: list[str] | None = None, n_linhas: int = 10, titulo: str = "DataFrame") -> None:
    """Exibe um DataFrame como uma tabela colorida no terminal."""
    colunas_escolhidas = list(df.columns) if colunas is None else colunas

    tabela = Table(title=titulo, header_style="bold cyan", show_lines=False)
    for coluna in colunas_escolhidas:
        tabela.add_column(str(coluna), no_wrap=False)

    for _, linha in df[colunas_escolhidas].head(n_linhas).iterrows():
        tabela.add_row(*(str(valor) if valor is not None else "" for valor in linha))

    _console.print(tabela)


def resumo_df(df: pd.DataFrame, n_primeiras: int = 10) -> None:
    """Mostra resumo do DataFrame: dimensões, tipos e primeiras linhas."""
    logger.info(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")

    tabela = Table(title="Tipos das colunas", header_style="bold magenta")
    tabela.add_column("Coluna")
    tabela.add_column("Tipo")
    for coluna in df.columns:
        tabela.add_row(str(coluna), str(df[coluna].dtype))
    _console.print(tabela)

    mostrar_df(df, n_linhas=n_primeiras, titulo="Primeiras linhas")


def listar_colunas(df: pd.DataFrame) -> list[str]:
    """Retorna a lista de colunas do DataFrame."""
    colunas = list(df.columns)
    logger.info(f"Colunas ({len(colunas)}): {colunas}")
    return colunas


def contar_linhas(df: pd.DataFrame) -> int:
    """Retorna a quantidade de linhas do DataFrame."""
    total = len(df)
    logger.info(f"Total de linhas: {total}")
    return total


# ----------------------------------------------------------------------
# Manipulação
# ----------------------------------------------------------------------
def filtrar_linhas(df: pd.DataFrame, condicao: str) -> pd.DataFrame:
    """Filtra linhas usando uma condição em texto (estilo pandas ``query``).

    Exemplo: ``filtrar_linhas(df, "estado == 'SP' and valor_compra > 1000")``
    """
    filtrado = df.query(condicao)
    logger.success(f"Filtro aplicado: {len(filtrado)} de {len(df)} linhas")
    return filtrado


def unir_tabelas(df_esquerda: pd.DataFrame, df_direita: pd.DataFrame, chave: str, como: str = "left") -> pd.DataFrame:
    """Une dois DataFrames por uma chave (join)."""
    unido = pd.merge(df_esquerda, df_direita, on=chave, how=como)
    logger.success(f"União concluída: {len(unido)} linhas (tipo '{como}')")
    return unido


def agrupar_somar(df: pd.DataFrame, por: str, colunas: list[str]) -> pd.DataFrame:
    """Agrupa por uma coluna e soma outras (útil para resumos).

    Exemplo: ``agrupar_somar(df, "estado", ["valor_compra"])``
    """
    agrupado = df.groupby(por, as_index=False)[colunas].sum()
    logger.success(f"Agrupamento por '{por}' concluído: {len(agrupado)} grupos")
    return agrupado


def converter_para_texto(df: pd.DataFrame, separador: str = ";") -> str:
    """Converte o DataFrame para texto (uma linha por registro)."""
    texto = df.to_csv(sep=separador, index=False).rstrip("\n")
    logger.info(f"DataFrame convertido para texto ({len(df)} registros).")
    return texto