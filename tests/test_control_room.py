"""Testes do orquestrador (Control Room): máquinas, jobs, tags, triggers e assets."""

from datetime import datetime

from core.control_room import banco as banco_orq
from core.control_room import servico
from core.control_room import servidor as servidor_orq


def _criar_processo(nome: str = "Processo Teste") -> dict:
    return servico.criar_processo(nome, "descrição", "app.fluxos:tratar_planilha")


# ----------------------------------------------------------------------
# Máquinas
# ----------------------------------------------------------------------
def test_registrar_maquina_e_heartbeat():
    maquina = servico.registrar_maquina("maq-01", tags="sp,financeiro")
    assert maquina["nome"] == "maq-01"
    assert maquina["tags"] == "sp,financeiro"

    maquinas = servico.listar_maquinas()
    assert len(maquinas) == 1
    assert maquinas[0]["estado"] == "online"

    assert servico.heartbeat("maq-01") is not None


def test_registrar_maquina_e_idempotente():
    servico.registrar_maquina("maq-01", tags="sp")
    servico.registrar_maquina("maq-01")
    maquinas = servico.listar_maquinas()
    assert len(maquinas) == 1
    assert maquinas[0]["tags"] == "sp"


def test_cadastrar_atualizar_e_apagar_maquina():
    import pytest

    maquina = servico.cadastrar_maquina("PC-01", tags="sp, financeiro", info="notebook")
    assert maquina["nome"] == "PC-01"
    assert maquina["estado"] == "offline"  # sem heartbeat até um agente conectar
    assert maquina["tags"] == "sp, financeiro"
    assert maquina["info"] == "notebook"
    assert maquina["tem_token"] is False

    with pytest.raises(ValueError):
        servico.cadastrar_maquina("PC-01")

    atualizada = servico.atualizar_maquina("PC-01", tags="rj", info="sala 2")
    assert atualizada["tags"] == "rj"
    assert atualizada["info"] == "sala 2"

    assert servico.apagar_maquina("PC-01") is True
    assert servico.listar_maquinas() == []
    assert servico.apagar_maquina("PC-01") is False


def test_maquinas_nao_expoem_hash_do_token():
    servico.registrar_maquina("maq-01")
    servico.emitir_token_maquina("maq-01")
    maquina = servico.listar_maquinas()[0]
    assert maquina["tem_token"] is True
    assert "token_hash" not in maquina


def test_rotas_de_maquinas_nao_exigem_token_de_agente():
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/maquinas")
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/maquinas/PC-01/editar")
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/maquinas/PC-01/remover")
    assert servidor_orq._permissao_da_rota("POST", "/api/orq/maquinas") == "maquinas.gerir"


# ----------------------------------------------------------------------
# Jobs
# ----------------------------------------------------------------------
def test_criar_e_reservar_job_para_maquina_especifica():
    processo = _criar_processo()
    maquina = servico.registrar_maquina("maq-01")

    job = servico.criar_job(processo["id"], maquina["id"], mensagem="teste")
    assert job["status"] == "pendente"

    reservado = servico.reservar_proximo_job("maq-01")
    assert reservado is not None
    assert reservado["id"] == job["id"]
    assert reservado["status"] == "em_execucao"
    assert reservado["maquina_id"] == maquina["id"]


def test_reservar_nao_pega_job_de_outra_maquina():
    processo = _criar_processo()
    maquina_a = servico.registrar_maquina("maq-a")
    servico.registrar_maquina("maq-b")
    servico.criar_job(processo["id"], maquina_a["id"])

    assert servico.reservar_proximo_job("maq-b") is None


def test_requisito_tag_respeita_pool():
    processo = _criar_processo()
    servico.registrar_maquina("sem-tag")

    job = servico.criar_job(processo["id"], requisito_tag="sp")

    assert servico.reservar_proximo_job("sem-tag") is None

    servico.registrar_maquina("com-tag", tags="financeiro,sp")
    reservado = servico.reservar_proximo_job("com-tag")
    assert reservado is not None
    assert reservado["id"] == job["id"]
    assert reservado["requisito_tag"] == "sp"


def test_cancelar_e_concluir_job():
    processo = _criar_processo()
    servico.registrar_maquina("maq-01")

    job = servico.criar_job(processo["id"])
    cancelado = servico.cancelar_job(job["id"])
    assert cancelado["status"] == "cancelado"

    outro = servico.criar_job(processo["id"])
    servico.reservar_proximo_job("maq-01")
    concluido = servico.concluir_job(outro["id"], sucesso=True, mensagem="ok")
    assert concluido["status"] == "concluido"


# ----------------------------------------------------------------------
# Triggers
# ----------------------------------------------------------------------
def test_trigger_intervalo_nao_dispara_antes_da_hora():
    processo = _criar_processo()
    servico.criar_trigger(processo["id"], tipo="intervalo", intervalo_min=30)

    assert servico.verificar_triggers() == 0
    assert servico.listar_jobs(limite=10) == []


def test_trigger_vencido_dispara_e_reagenda():
    processo = _criar_processo()
    trigger = servico.criar_trigger(processo["id"], tipo="intervalo", intervalo_min=30)

    with banco_orq.conectar() as conexao:
        conexao.execute(
            "UPDATE triggers SET proxima_execucao = '2000-01-01 00:00:00.000' WHERE id = ?",
            (trigger["id"],),
        )

    assert servico.verificar_triggers() == 1
    jobs = servico.listar_jobs(limite=10)
    assert len(jobs) == 1

    atualizado = servico.listar_triggers()[0]
    assert atualizado["ultima_execucao"] is not None
    assert atualizado["proxima_execucao"] > "2026-01-01"


def test_trigger_diario_define_proximo_dia():
    processo = _criar_processo()
    trigger = servico.criar_trigger(processo["id"], tipo="diario", hora="06:00")
    assert trigger["tipo"] == "diario"
    assert trigger["proxima_execucao"].endswith("06:00:00.000")


def test_apagar_trigger():
    processo = _criar_processo()
    trigger = servico.criar_trigger(processo["id"], tipo="intervalo", intervalo_min=10)
    servico.apagar_trigger(trigger["id"])
    assert servico.listar_triggers() == []


# ----------------------------------------------------------------------
# Assets
# ----------------------------------------------------------------------
def test_asset_mascara_secretos_e_entrega_valor_real():
    servico.criar_asset("portal_senha", "super-secreta", secreto=True)
    servico.criar_asset("portal_usuario", "rpa_bot", secreto=False)

    mascarados = {a["nome"]: a["valor"] for a in servico.listar_assets(mascarar=True)}
    assert mascarados["portal_senha"] == "••••••••"
    assert mascarados["portal_usuario"] == "rpa_bot"

    assert servico.obter_asset("portal_senha")["valor"] == "super-secreta"


def test_asset_upsert_e_remocao():
    servico.criar_asset("token", "v1")
    servico.criar_asset("token", "v2")
    assets = servico.listar_assets()
    assert len(assets) == 1

    servico.apagar_asset(assets[0]["id"])
    assert servico.listar_assets() == []


# ----------------------------------------------------------------------
# Painel
# ----------------------------------------------------------------------
def test_montar_painel_traz_todas_as_secoes():
    processo = _criar_processo()
    servico.registrar_maquina("maq-01", tags="sp")
    servico.criar_job(processo["id"])
    servico.criar_trigger(processo["id"], tipo="intervalo", intervalo_min=15)
    servico.criar_asset("token", "abc")

    painel = servico.montar_painel()
    for chave in ("resumo", "maquinas", "processos", "jobs", "triggers", "assets", "job_info"):
        assert chave in painel
    assert len(painel["triggers"]) == 1
    assert len(painel["assets"]) == 1


# ----------------------------------------------------------------------
# Autenticação por token (rotas de agente)
# ----------------------------------------------------------------------
def test_rotas_de_agente_sao_identificadas():
    assert servidor_orq._rota_de_agente("POST", "/api/orq/agente/maq-01/proximo")
    assert servidor_orq._rota_de_agente("POST", "/api/orq/agente/maq-01/registrar")
    assert servidor_orq._rota_de_agente("POST", "/api/orq/jobs/3/execucao")
    assert servidor_orq._rota_de_agente("POST", "/api/orq/jobs/3/concluir")
    assert servidor_orq._rota_de_agente("POST", "/api/orq/itens/1/resultado")
    assert servidor_orq._rota_de_agente("POST", "/api/orq/filas/clientes/proximo")
    assert servidor_orq._rota_de_agente("GET", "/api/orq/assets/portal_senha")


def test_rotas_do_painel_nao_exigem_token():
    assert not servidor_orq._rota_de_agente("GET", "/api/orq/painel")
    assert not servidor_orq._rota_de_agente("GET", "/api/orq/assets")
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/jobs")
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/assets")
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/filas")
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/assets/1/remover")
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/jobs/1/cancelar")
    assert not servidor_orq._rota_de_agente("POST", "/api/orq/itens/1/prioridade")


def test_permissao_da_rota_de_cancelar():
    assert servidor_orq._permissao_da_rota("POST", "/api/orq/jobs/7/cancelar") == "jobs.cancelar"
    assert servidor_orq._permissao_da_rota("POST", "/api/orq/jobs") == "jobs.disparar"
    # instalar do Git exige a mesma permissão do .zip
    assert servidor_orq._permissao_da_rota("POST", "/api/orq/automacoes/git") == "pacotes.instalar"
    assert (
        servidor_orq._permissao_da_rota("POST", "/api/orq/automacoes/git/atualizar")
        == "pacotes.instalar"
    )


def test_token_confere_bearer_x_token_e_vazio():
    # Sem token configurado, tudo é liberado (dev/rede local)
    assert servidor_orq._token_confere({}, "")

    cabecalhos = {"Authorization": "Bearer segredo"}
    assert servidor_orq._token_confere(cabecalhos, "segredo")
    assert servidor_orq._token_confere({"X-Token": "segredo"}, "segredo")

    assert not servidor_orq._token_confere(cabecalhos, "outro")
    assert not servidor_orq._token_confere({}, "segredo")
    assert not servidor_orq._token_confere({"Authorization": "Bearer errado"}, "segredo")


class _PedidoFalso:
    def __init__(self, cabecalhos: dict | None = None) -> None:
        self.headers = cabecalhos or {}


def test_token_agente_exigido_quando_auth_ligado(monkeypatch):
    metodo = servidor_orq.ManipuladorControlRoom._token_agente_ok
    monkeypatch.setattr(servidor_orq, "CONTROL_ROOM_TOKEN", "")
    monkeypatch.setattr(servidor_orq, "CONTROL_ROOM_AUTH", True)

    assert not metodo(_PedidoFalso())

    servico.registrar_maquina("maq-tok")
    token = servico.emitir_token_maquina("maq-tok")
    assert metodo(_PedidoFalso({"Authorization": f"Bearer {token}"}))

    monkeypatch.setattr(servidor_orq, "CONTROL_ROOM_AUTH", False)
    assert metodo(_PedidoFalso())


# ----------------------------------------------------------------------
# Push em tempo real (revisão)
# ----------------------------------------------------------------------
def test_revisao_detecta_mudancas():
    r0 = servico.revisao()
    processo = _criar_processo()
    r1 = servico.revisao()

    job = servico.criar_job(processo["id"])
    r2 = servico.revisao()

    servico.registrar_maquina("maq-01")
    servico.reservar_proximo_job("maq-01")
    servico.concluir_job(job["id"], True, "ok")
    r3 = servico.revisao()

    assert r0 != r1
    assert r1 != r2
    assert r2 != r3


# ----------------------------------------------------------------------
# Cron
# ----------------------------------------------------------------------
def test_trigger_cron_calcula_proxima_execucao():
    processo = _criar_processo()
    trigger = servico.criar_trigger(
        processo["id"], tipo="cron", expressao="*/15 9-18 * * seg-sex"
    )
    assert trigger["tipo"] == "cron"
    assert trigger["expressao"] == "*/15 9-18 * * seg-sex"
    assert trigger["proxima_execucao"] > "2026-01-01"


def test_cron_expressao_invalida_levanta_erro():
    processo = _criar_processo()
    try:
        servico.criar_trigger(processo["id"], tipo="cron", expressao="nao-e-cron")
    except ValueError:
        return
    raise AssertionError("deveria recusar expressão cron inválida")


# ----------------------------------------------------------------------
# Agendamento avançado (dias, fins de semana, feriados)
# ----------------------------------------------------------------------
def test_trigger_guarda_dias_e_flags():
    processo = _criar_processo()
    trigger = servico.criar_trigger(
        processo["id"],
        tipo="intervalo",
        intervalo_min=10,
        dias_semana=[1, 2, 3, 4, 5],
        incluir_fins=False,
        incluir_feriados=False,
    )
    assert trigger["dias_semana"] == "1,2,3,4,5"
    assert trigger["incluir_fins"] == 0
    assert trigger["incluir_feriados"] == 0


def test_normalizar_dias_aceita_nomes_e_completo():
    assert servico._normalizar_dias("seg,sex") == "1,5"
    assert servico._normalizar_dias([7, 1]) == "1,7"
    assert servico._normalizar_dias("1,2,3,4,5,6,7") is None
    assert servico._normalizar_dias("xpto") is None


def test_trigger_pula_dia_nao_permitido():
    processo = _criar_processo()
    hoje = datetime.now().isoweekday()
    outro = 1 if hoje != 1 else 2
    trigger = servico.criar_trigger(
        processo["id"], tipo="intervalo", intervalo_min=10, dias_semana=[outro]
    )
    with banco_orq.conectar() as conexao:
        conexao.execute(
            "UPDATE triggers SET proxima_execucao = '2000-01-01 00:00:00.000' WHERE id = ?",
            (trigger["id"],),
        )

    assert servico.verificar_triggers() == 0
    assert servico.listar_jobs(limite=10) == []
    assert servico.listar_triggers()[0]["proxima_execucao"] > "2026-01-01"


def test_trigger_pausado_nao_dispara():
    processo = _criar_processo()
    trigger = servico.criar_trigger(processo["id"], tipo="intervalo", intervalo_min=5)

    servico.definir_trigger_ativo(trigger["id"], False)
    with banco_orq.conectar() as conexao:
        conexao.execute(
            "UPDATE triggers SET proxima_execucao = '2000-01-01 00:00:00.000' WHERE id = ?",
            (trigger["id"],),
        )
    assert servico.verificar_triggers() == 0

    servico.definir_trigger_ativo(trigger["id"], True)
    with banco_orq.conectar() as conexao:
        conexao.execute(
            "UPDATE triggers SET proxima_execucao = '2000-01-01 00:00:00.000' WHERE id = ?",
            (trigger["id"],),
        )
    assert servico.verificar_triggers() == 1


def test_disparar_trigger_manual_cria_job():
    processo = _criar_processo()
    trigger = servico.criar_trigger(processo["id"], tipo="diario", hora="06:00")

    assert servico.disparar_trigger(trigger["id"]) is not None
    assert len(servico.listar_jobs(limite=10)) == 1
    assert servico.disparar_trigger(9999) is None


def test_apagar_processo_remove_triggers():
    processo = _criar_processo()
    servico.criar_trigger(processo["id"], tipo="intervalo", intervalo_min=5)
    servico.criar_job(processo_id=processo["id"])

    assert servico.apagar_processo(processo["id"]) is True
    assert servico.listar_processos() == []
    assert servico.listar_triggers() == []
    assert servico.listar_jobs() == []
    assert servico.apagar_processo(9999) is False


# ----------------------------------------------------------------------
# Token por máquina
# ----------------------------------------------------------------------
def test_token_por_maquina_valida_e_revoga():
    servico.registrar_maquina("maq-token")
    token = servico.emitir_token_maquina("maq-token")

    assert servico.validar_token_maquina(token)["nome"] == "maq-token"
    assert servico.validar_token_maquina("errado") is None
    assert servico.validar_token_maquina(None) is None

    servico.revogar_token_maquina("maq-token")
    assert servico.validar_token_maquina(token) is None


# ----------------------------------------------------------------------
# RBAC / sessões
# ----------------------------------------------------------------------
def test_autenticacao_e_sessao():
    servico.garantir_admin_padrao()
    servico.criar_usuario("Ana", "ana@x.com", "segredo", papeis=["admin"], admin=True)

    assert servico.autenticar("ana@x.com", "segredo") is not None
    assert servico.autenticar("ana@x.com", "errado") is None

    usuario = servico.autenticar("ana@x.com", "segredo")
    token = servico.criar_sessao(usuario)
    sessao = servico.validar_sessao(token)
    assert sessao["usuario"]["email"] == "ana@x.com"
    assert "painel.ver" in sessao["permissoes"]

    servico.apagar_sessao(token)
    assert servico.validar_sessao(token) is None


def test_garantir_admin_padrao_e_idempotente():
    servico.garantir_admin_padrao()
    servico.garantir_admin_padrao()
    admins = [u for u in servico.listar_usuarios() if u["admin"]]
    assert len(admins) == 1


# ----------------------------------------------------------------------
# Auditoria (expurgo + CSV)
# ----------------------------------------------------------------------
def test_exportar_auditoria_csv():
    servico.registrar_auditoria("assets.ler", recurso="portal", ator="maq-01")
    csv = servico.exportar_auditoria_csv()
    assert "acao" in csv
    assert "assets.ler" in csv


def test_expurgar_auditoria_remove_antigos():
    servico.registrar_auditoria("evento.antigo", ator="x")
    with banco_orq.conectar() as conexao:
        conexao.execute("UPDATE auditoria SET quando = '2000-01-01 00:00:00.000'")
    removidos = servico.expurgar_auditoria(30)
    assert removidos >= 1


# ----------------------------------------------------------------------
# Filas ativas/inativas
# ----------------------------------------------------------------------
def test_fila_pausada_nao_reserva_item():
    processo = _criar_processo()
    fila = servico.criar_fila("fila-ativa", processo["id"])
    servico.adicionar_item(fila["id"], {"nome": "ACME"})

    servico.definir_fila_ativa(fila["id"], False)
    assert servico.reservar_item("fila-ativa", "maq-01") is None

    servico.definir_fila_ativa(fila["id"], True)
    servico.registrar_maquina("maq-01")
    item = servico.reservar_item("fila-ativa", "maq-01")
    assert item is not None
    assert item["status"] == "em_processamento"


# ----------------------------------------------------------------------
# SLA / alertas
# ----------------------------------------------------------------------
def test_alerta_sla_marca_job_excedido():
    processo = _criar_processo()
    servico.registrar_maquina("maq-sla")
    job = servico.criar_job(processo["id"])
    servico.reservar_proximo_job("maq-sla")

    with banco_orq.conectar() as conexao:
        conexao.execute(
            "UPDATE jobs SET iniciado_em = '2000-01-01 00:00:00.000' WHERE id = ?",
            (job["id"],),
        )

    alertas = servico.listar_alertas()
    assert any(a["id"] == job["id"] and a["alerta"] == "excedido" for a in alertas)
    assert servico.classificar_job(servico.obter_job(job["id"])) == "excedido"


# ----------------------------------------------------------------------
# Painel com identidade
# ----------------------------------------------------------------------
def test_painel_traz_identidade_e_sla():
    servico.garantir_admin_padrao()
    painel = servico.montar_painel()
    for chave in ("usuarios", "papeis", "permissoes", "empresas", "alertas", "sla"):
        assert chave in painel
    assert len(painel["usuarios"]) >= 1
    assert painel["sla"]["limite_segundos"] >= 1


# ----------------------------------------------------------------------
# Cancelar job em execução + prioridade por item + round-robin
# ----------------------------------------------------------------------
def test_cancelar_job_em_execucao_e_conclusao_respeita_cancelamento():
    processo = _criar_processo()
    servico.registrar_maquina("maq-cancel")
    job = servico.criar_job(processo["id"])
    servico.reservar_proximo_job("maq-cancel")

    assert servico.job_cancelado(job["id"]) is False
    cancelado = servico.cancelar_job(job["id"])
    assert cancelado["status"] == "cancelado"
    assert servico.job_cancelado(job["id"]) is True

    concluido = servico.concluir_job(job["id"], sucesso=True, mensagem="terminou tarde")
    assert concluido["status"] == "cancelado"
    assert "terminou tarde" in (concluido["mensagem"] or "")


def test_prioridade_por_item_e_alteracao():
    processo = _criar_processo()
    fila = servico.criar_fila("fila-prio", processo["id"])
    servico.adicionar_itens(fila["id"], [{"nome": "baixa"}, {"nome": "alta", "prioridade": 9}])

    servico.registrar_maquina("maq-prio")
    primeiro = servico.reservar_item("fila-prio", "maq-prio")
    assert primeiro["dados"]["nome"] == "alta"

    segundo = servico.listar_itens(fila["id"])
    alvo = next(i for i in segundo if i["dados"]["nome"] == "baixa")
    atualizado = servico.definir_prioridade_item(alvo["id"], 100)
    assert atualizado["prioridade"] == 100


def test_round_robin_entre_processos_da_fila():
    p1 = _criar_processo("Executor A")
    p2 = _criar_processo("Executor B")
    fila = servico.criar_fila("fila-rr", p1["id"], processos=[p1["id"], p2["id"]])
    assert {p["id"] for p in fila["processos"]} == {p1["id"], p2["id"]}

    servico.adicionar_itens(fila["id"], [{"n": i} for i in range(4)])
    servico.registrar_maquina("maq-rr")

    processos = []
    for _ in range(4):
        resposta = servico.reservar_item_e_job("fila-rr", "maq-rr")
        assert resposta["job"] is not None
        processos.append(resposta["job"]["processo_id"])

    assert processos[0] != processos[1]
    assert processos[0] == processos[2]
    assert processos[1] == processos[3]

    servico.apagar_fila(fila["id"])


def test_executores_da_fila_sao_removidos_junto_com_a_fila():
    p1 = _criar_processo("Exec A")
    p2 = _criar_processo("Exec B")
    fila = servico.criar_fila("fila-limpa", p1["id"], processos=[p1["id"], p2["id"]])
    servico.apagar_fila(fila["id"])
    assert servico.listar_filas() == []
