"""Operações com arquivos e pastas (explorer) com cara de low-code.

Inclui listar, copiar, mover, renomear, apagar, baixar, compactar e extrair::

    from core.rpa import arquivo

    arquivos = arquivo.listar_arquivos("data/input")
    arquivo.mover_arquivo("data/input/a.csv", "data/output/a.csv")
    arquivo.baixar_arquivo("https://.../relatorio.pdf", "data/output/")
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import requests
from loguru import logger
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from core.tratador import ErroRPA


# ----------------------------------------------------------------------
# Explorar / listar
# ----------------------------------------------------------------------
def listar_arquivos(pasta: str | Path, extensao: str | None = None, completo: bool = True) -> list[Path]:
    """Lista os arquivos de uma pasta (opcionalmente filtrando por extensão).

    ``extensao`` pode ser passada com ou sem ponto (ex.: ``"csv"`` ou ``".CSV"``).
    """
    pasta = Path(pasta)
    if not pasta.is_dir():
        raise ErroRPA(f"Pasta não encontrada: {pasta}")

    padrao = "*" if extensao is None else f"*.{extensao.lower().lstrip('.')}"
    arquivos = [p for p in pasta.glob(padrao) if p.is_file()]
    ordenados = sorted(arquivos, key=lambda p: p.name.lower())

    logger.info(f"{len(ordenados)} arquivo(s) em '{pasta}'{f' ({extensao})' if extensao else ''}:")
    for arquivo in ordenados:
        logger.info(f"  - {arquivo.name}")
    return [p.resolve() for p in ordenados] if completo else ordenados


def criar_pasta(caminho: str | Path) -> Path:
    """Cria uma pasta (e subpastas) se ela não existir."""
    caminho = Path(caminho)
    caminho.mkdir(parents=True, exist_ok=True)
    logger.success(f"Pasta garantida: {caminho}")
    return caminho


def listar_pastas(pasta: str | Path, completo: bool = True) -> list[Path]:
    """Lista as subpastas de um diretório."""
    pasta = Path(pasta)
    pastas = sorted(p for p in pasta.iterdir() if p.is_dir())
    logger.info(f"{len(pastas)} pasta(s) em '{pasta}': {[p.name for p in pastas]}")
    return [p.resolve() for p in pastas] if completo else pastas


# ----------------------------------------------------------------------
# Texto puro
# ----------------------------------------------------------------------
def ler_arquivo_texto(caminho: str | Path, codificacao: str = "utf-8") -> str:
    """Lê o conteúdo de um arquivo de texto."""
    caminho = Path(caminho)
    conteudo = caminho.read_text(encoding=codificacao)
    logger.info(f"Arquivo lido: {caminho.name} ({len(conteudo)} caracteres)")
    return conteudo


def escrever_arquivo_texto(caminho: str | Path, conteudo: str, codificacao: str = "utf-8") -> Path:
    """Escreve um conteúdo de texto em um arquivo."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding=codificacao)
    logger.success(f"Arquivo escrito: {caminho}")
    return caminho


# ----------------------------------------------------------------------
# Copiar / mover / renomear / apagar
# ----------------------------------------------------------------------
def _resolver_destino(origem: Path, destino: Path) -> Path:
    if destino.is_dir() or str(destino).endswith(("/", "\\")):
        return destino / origem.name
    return destino


def copiar_arquivo(origem: str | Path, destino: str | Path, sobrescrever: bool = True) -> Path:
    """Copia um arquivo para outro local."""
    origem, destino = Path(origem), Path(destino)
    if not origem.is_file():
        raise ErroRPA(f"Arquivo de origem não encontrado: {origem}")
    destino = _resolver_destino(origem, destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and not sobrescrever:
        raise ErroRPA(f"Destino já existe e sobrescrever=False: {destino}")
    shutil.copy2(origem, destino)
    logger.success(f"Arquivo copiado: {origem.name} -> {destino}")
    return destino


def mover_arquivo(origem: str | Path, destino: str | Path, sobrescrever: bool = True) -> Path:
    """Move um arquivo para outro local (corta e cola)."""
    origem, destino = Path(origem), Path(destino)
    if not origem.is_file():
        raise ErroRPA(f"Arquivo de origem não encontrado: {origem}")
    destino = _resolver_destino(origem, destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and not sobrescrever:
        raise ErroRPA(f"Destino já existe e sobrescrever=False: {destino}")
    shutil.move(str(origem), str(destino))
    logger.success(f"Arquivo movido: {origem.name} -> {destino}")
    return destino


def renomear_arquivo(origem: str | Path, novo_nome: str) -> Path:
    """Renomeia um arquivo dentro da mesma pasta."""
    origem = Path(origem)
    destino = origem.parent / novo_nome
    if destino.exists():
        raise ErroRPA(f"Já existe um arquivo com o nome: {destino}")
    origem.rename(destino)
    logger.success(f"Arquivo renomeado: {origem.name} -> {novo_nome}")
    return destino


def apagar_arquivo(caminho: str | Path, confirmar: bool = False) -> None:
    """Apaga um arquivo. Marque ``confirmar=True`` para executar de fato."""
    caminho = Path(caminho)
    if not caminho.is_file():
        raise ErroRPA(f"Arquivo não encontrado: {caminho}")
    if not confirmar:
        logger.warning(f"Apagamento evitado (confirme com confirmar=True): {caminho}")
        return
    caminho.unlink()
    logger.success(f"Arquivo apagado: {caminho}")


# ----------------------------------------------------------------------
# Download
# ----------------------------------------------------------------------
def baixar_arquivo(url: str, destino: str | Path, tempo_max: int = 120, nome_arquivo: str | None = None) -> Path:
    """Baixa um arquivo de uma URL, exibindo barra de progresso."""
    destino = Path(destino)
    if destino.is_dir() or str(destino).endswith(("/", "\\")):
        nome = nome_arquivo or url.split("/")[-1].split("?")[0] or "download"
        destino = destino / nome
    destino.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=tempo_max) as resposta:
        resposta.raise_for_status()
        total = int(resposta.headers.get("content-length", 0))

        with Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progresso:
            tarefa = progresso.add_task(f"Baixando {destino.name}...", total=total)
            with open(destino, "wb") as arquivo:
                for parte in resposta.iter_content(chunk_size=1024 * 256):
                    if parte:
                        arquivo.write(parte)
                        progresso.update(tarefa, advance=len(parte))

    logger.success(f"Download concluído: {destino}")
    return destino


# ----------------------------------------------------------------------
# ZIP
# ----------------------------------------------------------------------
def compactar_pasta(pasta: str | Path, destino_zip: str | Path | None = None) -> Path:
    """Compacta uma pasta inteira em um arquivo .zip."""
    pasta = Path(pasta)
    if not pasta.is_dir():
        raise ErroRPA(f"Pasta não encontrada: {pasta}")
    destino_zip = Path(destino_zip or pasta.parent / f"{pasta.name}.zip")
    destino_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_DEFLATED) as zip_final:
        for arquivo in pasta.rglob("*"):
            if arquivo.is_file():
                zip_final.write(arquivo, arquivo.relative_to(pasta))

    logger.success(f"Pasta compactada: {pasta.name} -> {destino_zip}")
    return destino_zip


def extrair_zip(caminho_zip: str | Path, pasta_destino: str | Path | None = None) -> Path:
    """Extrai um arquivo .zip para uma pasta."""
    caminho_zip = Path(caminho_zip)
    if not caminho_zip.is_file():
        raise ErroRPA(f"Arquivo ZIP não encontrado: {caminho_zip}")
    pasta_destino = Path(pasta_destino or caminho_zip.parent / caminho_zip.stem)
    pasta_destino.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(caminho_zip, "r") as zip_aberto:
        zip_aberto.extractall(pasta_destino)

    logger.success(f"ZIP extraído: {caminho_zip.name} -> {pasta_destino}")
    return pasta_destino