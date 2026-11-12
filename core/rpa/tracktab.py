"""Integração com a extensão TrackTab (gravador de elementos/XPath).

O TrackTab (pasta ``tracktab/`` na raiz do projeto) é uma extensão de navegador
que captura elementos de qualquer página e exporta um JSON com três variações
de seletor por elemento. Este módulo lê esse arquivo e entrega os seletores
prontos para usar com o :class:`core.rpa.browser.Navegador`.

Fluxo típico::

    from core.rpa import tracktab

    elementos = tracktab.carregar("data/input/tracktab.json")
    navegador.clicar_elemento(elementos["Botão Entrar"].relativo)

    # ou apenas os seletores, por nome
    seletores = tracktab.seletores("data/input/tracktab.json")
    navegador.escrever_texto(seletores["Input E-mail"], "eu@exemplo.com")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from core.tratador import ErroRPA

TIPOS = {
    "relativo": "relativo",
    "relative": "relativo",
    "custom": "custom",
    "completo": "completo",
    "full": "completo",
}


@dataclass(frozen=True)
class Elemento:
    """Um elemento capturado pelo TrackTab, com seus três seletores."""

    nome: str
    tag: str
    texto: str
    completo: str
    relativo: str
    custom: str

    @property
    def seletor(self) -> str:
        """Melhor seletor disponível (relativo → custom → completo)."""
        return self.relativo or self.custom or self.completo


def _ler_export(caminho: str | Path) -> dict:
    arquivo = Path(caminho)
    if not arquivo.is_file():
        raise ErroRPA(f"Export do TrackTab não encontrado: {arquivo}")
    try:
        return json.loads(arquivo.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ErroRPA(f"JSON inválido em {arquivo}: {erro}") from erro


def carregar(caminho: str | Path) -> dict[str, Elemento]:
    """Lê um export do TrackTab e devolve ``{nome: Elemento}``."""
    dados = _ler_export(caminho)
    elementos: dict[str, Elemento] = {}
    for item in dados.get("elements", []):
        elemento = Elemento(
            nome=item.get("name") or item.get("tag") or "elemento",
            tag=item.get("tag", ""),
            texto=item.get("text", ""),
            completo=item.get("fullXpath", ""),
            relativo=item.get("relativeXpath", ""),
            custom=item.get("customPath", ""),
        )
        elementos[elemento.nome] = elemento

    logger.success(
        f"TrackTab: {len(elementos)} elemento(s) carregado(s) de {Path(caminho).name}"
    )
    return elementos


def seletores(caminho: str | Path, tipo: str = "relativo") -> dict[str, str]:
    """Devolve ``{nome: seletor}`` usando o tipo pedido.

    ``tipo`` aceita ``relativo`` (padrão), ``custom`` ou ``completo``.
    """
    chave = TIPOS.get(tipo)
    if chave is None:
        raise ErroRPA(
            f"Tipo de seletor inválido: {tipo!r}. Use: {', '.join(sorted(TIPOS))}."
        )
    return {
        nome: getattr(elemento, chave)
        for nome, elemento in carregar(caminho).items()
    }


__all__ = ["Elemento", "TIPOS", "carregar", "seletores"]
