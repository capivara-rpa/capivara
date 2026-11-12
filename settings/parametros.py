"""Configurações centrais do projeto.

Todos os robôs leem os parâmetros deste módulo. Você pode editar os valores
diretamente aqui ou sobrescrevê-los via arquivo ``.env`` (recomendado para
senhas, tokens e valores diferentes entre máquinas).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from settings.ambiente import carregar_variaveis

carregar_variaveis()

# Quando o app roda empacotado (PyInstaller), não existe um "projeto" físico:
# os dados ficam num diretório configurável (RPA_PASTA_DADOS) para persistirem
# entre execuções do binário instalado.
_EMBALADO = bool(getattr(sys, "frozen", False))


def _como_bool(valor: str | None, padrao: bool = False) -> bool:
    if valor is None:
        return padrao
    return valor.strip().lower() in {"1", "true", "sim", "yes", "on"}


def _como_int(valor: str | None, padrao: int) -> int:
    if valor is None or not valor.strip().isdigit():
        return padrao
    return int(valor.strip())


# ----------------------------------------------------------------------
# Caminhos do projeto
# ----------------------------------------------------------------------
RAIZ_PROJETO = Path(__file__).resolve().parents[1]

# Em binários instalados, os dados (bancos, logs, vault) vão para RPA_PASTA_DADOS
# para não se perderem a cada execução extraída no _MEIPASS.
_PASTA_DADOS = os.getenv("RPA_PASTA_DADOS", "")
PASTA_DATA = Path(_PASTA_DADOS) if _PASTA_DADOS else RAIZ_PROJETO / "data"
PASTA_INPUT = PASTA_DATA / "input"
PASTA_OUTPUT = PASTA_DATA / "output"
PASTA_LOGS = PASTA_DATA / "logs"

for _pasta in (PASTA_INPUT, PASTA_OUTPUT, PASTA_LOGS):
    _pasta.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Ambiente de execução
# ----------------------------------------------------------------------
# dev  -> abre a janela do navegador (ideal para desenvolvimento)
# prod -> executa em modo headless (sem janela, ideal para servidores/Docker)
AMBIENTE = os.getenv("AMBIENTE", "dev").strip().lower()

# Se AMBIENTE == "prod", o navegador roda escondido por padrão
HEADLESS = _como_bool(os.getenv("HEADLESS"), AMBIENTE == "prod")

# Tempos (segundos)
TEMPO_ESPERA_PADRAO = _como_int(os.getenv("TEMPO_ESPERA_PADRAO"), 5)
TEMPO_TIMEOUT = _como_int(os.getenv("TEMPO_TIMEOUT"), 15)

# URL utilizada pelos robôs de exemplo
SITE_DEMO = os.getenv("SITE_DEMO", "https://www.google.com.br/")

# ----------------------------------------------------------------------
# Credenciais (sempre via .env, nunca hardcoded!)
# ----------------------------------------------------------------------
USUARIO = os.getenv("USUARIO", "")
SENHA = os.getenv("SENHA", "")

# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "")
API_TOKEN = os.getenv("API_TOKEN", "")

# ----------------------------------------------------------------------
# E-mail / SMTP
# ----------------------------------------------------------------------
SMTP_SERVIDOR = os.getenv("SMTP_SERVIDOR", "")
SMTP_PORTA = _como_int(os.getenv("SMTP_PORTA"), 465)
SMTP_USUARIO = os.getenv("SMTP_USUARIO", "")
SMTP_SENHA = os.getenv("SMTP_SENHA", "")
SMTP_ORIGEM = os.getenv("SMTP_ORIGEM", "")

# ----------------------------------------------------------------------
# Logs
# ----------------------------------------------------------------------
NOME_LOG = os.getenv("NOME_LOG", "rpa.log")
NIVEL_LOG = os.getenv("NIVEL_LOG", "DEBUG").strip().upper()

# ----------------------------------------------------------------------
# Monitor / painel web de trace (core/monitor)
# ----------------------------------------------------------------------
# Banco SQLite onde ficam as execuções e o passo a passo dos robôs.
_caminho_banco = os.getenv("BANCO_MONITOR", "").strip()
BANCO_MONITOR = Path(_caminho_banco) if _caminho_banco else PASTA_DATA / "monitor.db"

# Porta do painel local (http://localhost:8765)
PORTA_MONITOR = _como_int(os.getenv("PORTA_MONITOR"), 8765)

# Host/interface do painel. Use 0.0.0.0 para aceitar conexões da rede local.
HOST_MONITOR = os.getenv("HOST_MONITOR", "127.0.0.1").strip()

# Abrir o navegador automaticamente ao subir o painel
ABRIR_PAINEL = _como_bool(os.getenv("ABRIR_PAINEL"), True)

# ----------------------------------------------------------------------
# Orquestrador / Control Room (core/control_room)
# ----------------------------------------------------------------------
# Banco com máquinas, processos e jobs (separado do trace do monitor)
_caminho_orq = os.getenv("BANCO_ORQUESTRADOR", "").strip()
BANCO_ORQUESTRADOR = Path(_caminho_orq) if _caminho_orq else PASTA_DATA / "orquestrador.db"

# Porta da Control Room (serve também o painel de trace em /monitor/)
PORTA_CONTROL_ROOM = _como_int(os.getenv("PORTA_CONTROL_ROOM"), 8765)

# Host/interface da Control Room. Use 0.0.0.0 para aceitar runners da rede local.
HOST_CONTROL_ROOM = os.getenv("HOST_CONTROL_ROOM", "127.0.0.1").strip()

# Segundos sem heartbeat até considerar uma máquina "offline"
SEGUNDOS_OFFLINE = _como_int(os.getenv("SEGUNDOS_OFFLINE"), 20)

# Intervalo (segundos) da verificação de agendamentos (triggers)
INTERVALO_TRIGGERS = _como_int(os.getenv("INTERVALO_TRIGGERS"), 15)

# URL da Control Room usada pelos robôs/CLI para consumir vault e filas
CONTROL_ROOM_URL = os.getenv("CONTROL_ROOM_URL", "http://127.0.0.1:8765").rstrip("/")

# Token que os agentes enviam à Control Room (cabeçalho Authorization: Bearer).
# Vazio = Control Room aberta (ideal para dev/rede local). Defina para expor a
# Control Room fora da rede confiável (VPN/hosted): todos os agentes precisam do
# mesmo token.
CONTROL_ROOM_TOKEN = os.getenv("CONTROL_ROOM_TOKEN", "").strip()

# Login/RBAC da Control Room (interface web). O primeiro admin é criado na
# primeira subida com estas credenciais (troque a senha depois!).
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@rpa.local").strip()
ADMIN_SENHA = os.getenv("ADMIN_SENHA", "admin")

# Exigir login (sessão) para as ações do painel? Desligado por padrão para não
# atrapalhar o uso local/dev. Ligue em ambientes compartilhados/rede.
CONTROL_ROOM_AUTH = _como_bool(os.getenv("CONTROL_ROOM_AUTH"), False)

# Horas de validade de uma sessão de usuário
SESSAO_HORAS = _como_int(os.getenv("SESSAO_HORAS"), 12)

# Retenção da trilha de auditoria em dias (0 = nunca expurgar)
RETENCAO_AUDITORIA_DIAS = _como_int(os.getenv("RETENCAO_AUDITORIA_DIAS"), 90)

# SLA de execução: acima disso um job é "excedido" (e 75% disso = "lento")
LIMITE_JOB_SEGUNDOS = _como_int(os.getenv("LIMITE_JOB_SEGUNDOS"), 300)

# TLS (HTTPS) opcional para expor a Control Room/monitor fora da rede local.
# Informe o certificado e a chave em PEM. Vazio = HTTP puro (dev/rede local).
TLS_CERT = os.getenv("TLS_CERT", "").strip()
TLS_CHAVE = os.getenv("TLS_CHAVE", "").strip()

# ----------------------------------------------------------------------
# Cofre de credenciais (vault) — segredos cifrados
# ----------------------------------------------------------------------
# Frase-senha usada para cifrar os segredos. Se vazia, o cofre gera e guarda
# uma chave local em ``data/vault.key`` (fora do Git). Em produção, defina no
# ``.env`` e mantenha a mesma chave em todas as máquinas que consomem o cofre.
VAULT_CHAVE = os.getenv("VAULT_CHAVE", "")

# Arquivo de chave local (usado só quando VAULT_CHAVE não está definida)
VAULT_ARQUIVO_CHAVE = PASTA_DATA / "vault.key"

# Guardar a chave do cofre no chaveiro do sistema (macOS Keychain, Windows
# Credential Manager, Secret Service no Linux) em vez do arquivo local. Requer
# o extra ``keyring`` (``pip install -e ".[keyring]"``). Ignorado quando
# ``VAULT_CHAVE`` está definida. Para um KMS/segredo externo, basta alimentar
# ``VAULT_CHAVE`` a partir dele.
VAULT_USAR_KEYRING = _como_bool(os.getenv("VAULT_USAR_KEYRING"), False)

# ----------------------------------------------------------------------
# Pacotes de robôs (.zip) enviados para a Control Room
# ----------------------------------------------------------------------
# Pasta onde os pacotes enviados são extraídos e registrados automaticamente
# Pasta onde os robôs empacotados (.zip) são instalados
if _EMBALADO:
    PASTA_ROBOS = PASTA_DATA / "robos"
else:
    PASTA_ROBOS = Path(os.getenv("PASTA_ROBOS", "") or (RAIZ_PROJETO / "app" / "robos"))

# Quando verdadeiro, robôs publicados com um requirements.txt próprio ganham um
# ambiente isolado (.venv): o agente cria a venv, atualiza o pip, instala as
# dependências e executa o fluxo nesse ambiente. Desligue com
# RPA_INSTALAR_DEPENDENCIAS=false para sempre rodar no ambiente do agente.
INSTALAR_DEPENDENCIAS = _como_bool(os.getenv("RPA_INSTALAR_DEPENDENCIAS"), True)