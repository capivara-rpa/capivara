"""Motor low-code de RPA: web, dados, arquivos, API, e-mail e utilidades.

Facilita o uso de bibliotecas complexas (Selenium, pandas, requests...)
através de funções descritivas em português: texto, validação BR, banco,
segurança, sistema, notificações e muito mais.
"""

from core.rpa import (
    arquivo,
    banco,
    dados,
    email,
    fila,
    interacao,
    notificacoes,
    seguranca,
    sistema,
    texto,
    tracktab,
    validacao,
    vault,
)
from core.rpa.api import (
    ClienteAPI,
    api_delete,
    api_download,
    api_get,
    api_patch,
    api_post,
    api_put,
    api_upload,
)
from core.rpa.browser import Navegador

__all__ = [
    "arquivo",
    "banco",
    "dados",
    "email",
    "fila",
    "interacao",
    "notificacoes",
    "seguranca",
    "sistema",
    "texto",
    "tracktab",
    "validacao",
    "vault",
    "ClienteAPI",
    "api_delete",
    "api_download",
    "api_get",
    "api_patch",
    "api_post",
    "api_put",
    "api_upload",
    "Navegador",
]