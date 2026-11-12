"""Envio de e-mail (SMTP) com logs coloridos.

Uso::

    from core.rpa.email import enviar_email

    enviar_email(
        destinatarios=["cliente@exemplo.com"],
        assunto="Relatório do robô",
        corpo="Segue o relatório em anexo.",
        anexos=["data/output/relatorio.xlsx"],
    )

As configurações do servidor podem vir do ``.env`` (SMTP_SERVIDOR etc.).
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path

from loguru import logger

from core.tratador import ErroRPA
from settings.parametros import SMTP_ORIGEM, SMTP_PORTA, SMTP_SENHA, SMTP_SERVIDOR, SMTP_USUARIO


def enviar_email(
    destinatarios: list[str] | tuple[str, ...] | str,
    assunto: str,
    corpo: str = "",
    anexos: list[str | Path] | None = None,
    servidor: str | None = None,
    porta: int | None = None,
    usuario: str | None = None,
    senha: str | None = None,
    remetente: str | None = None,
) -> None:
    """Envia um e-mail em texto simples, com anexos opcionais.

    Parâmetros que não forem informados são lidos do ``.env``.
    """
    servidor = servidor or SMTP_SERVIDOR
    porta = porta or SMTP_PORTA
    usuario = SMTP_USUARIO if usuario is None else usuario
    senha = SMTP_SENHA if senha is None else senha
    remetente = remetente or SMTP_ORIGEM or usuario

    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]

    if not servidor or not remetente:
        raise ErroRPA(
            "Configuração de e-mail incompleta. Preencha SMTP_SERVIDOR e SMTP_ORIGEM no .env."
        )

    mensagem = EmailMessage()
    mensagem["From"] = remetente
    mensagem["To"] = ", ".join(destinatarios)
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo or "")

    for anexo in anexos or []:
        caminho = Path(anexo)
        if not caminho.is_file():
            raise ErroRPA(f"Anexo não encontrado: {caminho}")
        mensagem.add_attachment(
            caminho.read_bytes(),
            maintype="application",
            subtype="octet-stream",
            filename=caminho.name,
        )

    logger.info(
        f"Enviando e-mail para {len(destinatarios)} destinatário(s) via {servidor}:{porta}..."
    )

    if porta == 465:
        conexao = smtplib.SMTP_SSL(servidor, porta)
    else:
        conexao = smtplib.SMTP(servidor, porta)
        conexao.starttls()

    try:
        if usuario and senha:
            conexao.login(usuario, senha)
        conexao.send_message(mensagem)
        logger.success(f"E-mail enviado para: {', '.join(destinatarios)}")
    except Exception as erro:  # noqa: BLE001
        raise ErroRPA(f"Falha ao enviar e-mail: {erro}") from erro
    finally:
        conexao.quit()