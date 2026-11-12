"""Motor low-code de RPA: web, dados, arquivos, API e e-mail.

Facilita o uso de bibliotecas complexas (Selenium, pandas, requests...)
através de funções descritivas em português.
"""

from core.rpa import arquivo, dados, email, fila, interacao, tracktab, vault
from core.rpa.api import ClienteAPI, api_get, api_post
from core.rpa.browser import Navegador

__all__ = [
    "arquivo",
    "dados",
    "email",
    "fila",
    "interacao",
    "tracktab",
    "vault",
    "ClienteAPI",
    "api_get",
    "api_post",
    "Navegador",
]