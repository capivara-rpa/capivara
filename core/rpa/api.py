"""Cliente HTTP simples (requests) com logs coloridos e retry automático.

Uso rápido::

    from core.rpa.api import api_get, api_post

    resposta = api_get("https://api.exemplo.com/usuarios")
    if resposta.status_code == 200:
        dados = resposta.json()
"""

from __future__ import annotations

import time
from typing import Any

import requests
from loguru import logger

from core.tratador import tentar_novamente
from settings.parametros import API_BASE_URL, API_TOKEN


class ClienteAPI:
    """Cliente HTTP reutilizável dentro dos robôs.

    Exemplo::

        api = ClienteAPI(base_url="https://api.exemplo.com", token="...")
        api.api_get("/usuarios")
        api.api_post("/pedidos", json={...})
    """

    def __init__(
        self,
        base_url: str = "",
        token: str | None = None,
        headers: dict[str, str] | None = None,
        tempo_timeout: int = 30,
        verificar_ssl: bool = True,
    ) -> None:
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.sessao = requests.Session()
        self.sessao.headers.update({"User-Agent": "Template-RPA-Brasil/1.0"})
        if headers:
            self.sessao.headers.update(headers)
        if token:
            self.sessao.headers.update({"Authorization": f"Bearer {token}"})
        elif API_TOKEN:
            self.sessao.headers.update({"Authorization": f"Bearer {API_TOKEN}"})
        self.tempo_timeout = tempo_timeout
        self.verificar_ssl = verificar_ssl

    # --------------------------------------------------------------
    @tentar_novamente(vezes=3, espera=1.5, excecoes=(requests.exceptions.RequestException,))
    def _requisitar(self, metodo: str, caminho: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{caminho.lstrip('/')}" if caminho else self.base_url
        kwargs.setdefault("timeout", self.tempo_timeout)
        kwargs.setdefault("verify", self.verificar_ssl)

        inicio = time.perf_counter()
        resposta = self.sessao.request(metodo.upper(), url, **kwargs)
        duracao = time.perf_counter() - inicio

        if resposta.ok:
            logger.success(f"{metodo.upper()} {url} -> {resposta.status_code} ({duracao:.2f}s)")
        else:
            logger.error(f"{metodo.upper()} {url} -> {resposta.status_code} ({duracao:.2f}s)")

        return resposta

    def api_get(self, caminho: str = "", params: dict[str, Any] | None = None, **kwargs) -> requests.Response:
        """Faz uma requisição GET."""
        return self._requisitar("GET", caminho, params=params, **kwargs)

    def api_post(self, caminho: str = "", json: dict[str, Any] | None = None, dados: dict[str, Any] | None = None, **kwargs) -> requests.Response:
        """Faz uma requisição POST."""
        return self._requisitar("POST", caminho, json=json, data=dados, **kwargs)

    def api_put(self, caminho: str = "", json: dict[str, Any] | None = None, **kwargs) -> requests.Response:
        """Faz uma requisição PUT."""
        return self._requisitar("PUT", caminho, json=json, **kwargs)

    def api_delete(self, caminho: str = "", **kwargs) -> requests.Response:
        """Faz uma requisição DELETE."""
        return self._requisitar("DELETE", caminho, **kwargs)


# ----------------------------------------------------------------------
# Padrão da biblioteca padrão: instância de uso simples
# ----------------------------------------------------------------------
def _cliente_padrao() -> ClienteAPI:
    return ClienteAPI()


def api_get(caminho: str = "", params: dict[str, Any] | None = None, **kwargs) -> requests.Response:
    """Requisição GET com o cliente padrão (usa API_BASE_URL do .env)."""
    return _cliente_padrao().api_get(caminho, params=params, **kwargs)


def api_post(caminho: str = "", json: dict[str, Any] | None = None, dados: dict[str, Any] | None = None, **kwargs) -> requests.Response:
    """Requisição POST com o cliente padrão (usa API_BASE_URL do .env)."""
    return _cliente_padrao().api_post(caminho, json=json, dados=dados, **kwargs)