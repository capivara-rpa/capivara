# Rodando os robôs fora da sua máquina (rede, token, TLS e VPN)

A Control Room sobe por padrão em `http://127.0.0.1:8765` (só a própria máquina).
Este guia mostra como liberar **agentes em outras máquinas**, com segurança.

> Resumo: rede local = abrir o host; fora da rede = **token** (+ **TLS**) e,
> de preferência, uma **VPN/overlay** (Tailscale).

## 1. Mesma rede local (LAN) — piloto

No `settings/parametros.py` (ou no `.env`):

```dotenv
HOST_CONTROL_ROOM=0.0.0.0     # escuta a rede
CONTROL_ROOM_TOKEN=um-segredo-forte
```

Suba a Control Room e veja no log o comando pronto para os runners:

```bash
python -m core.control_room.servidor
# SUCCESS | Control Room disponível em http://0.0.0.0:8765
# INFO    | Runners na rede: --control-room http://192.168.0.10:8765
```

Em cada máquina da rede:

```bash
python -m core.control_room.agente \
    --control-room http://192.168.0.10:8765 \
    --maquina maquina-sp-01 --tags sp --token um-segredo-forte
```

No Mac, o serviço já sai configurado em um passo: `scripts/instalar_agente_mac.sh
--control-room http://192.168.0.10:8765 --tags sp --token um-segredo-forte`.

> Se a máquina tiver firewall, libere a porta 8765 (ex.: no macOS,
> Preferências → Rede → Firewall; no Windows, libere no instalador/Defender).

## 2. Token: o que ele protege

Quando `CONTROL_ROOM_TOKEN` está **definido**, só as **rotas de agente** pedem o
token (`Authorization: Bearer` ou `X-Token`):

| Rota | Método |
|---|---|
| `/api/orq/agente/*` | POST |
| `/api/orq/jobs/<id>/execucao` · `/concluir` | POST |
| `/api/orq/itens/<id>/resultado` · `/abandonar` | POST |
| `/api/orq/filas/<nome>/proximo` | POST |
| `/api/orq/assets/<nome>` | GET |

O **painel** (e as rotas de leitura/criação de jobs) fica aberto — é a interface
humana. Com o token **vazio**, tudo fica aberto (ideal só para dev/rede local).

Os clientes do template já mandam o token sozinhos quando `CONTROL_ROOM_TOKEN`
está no ambiente: o **agente** (`--token`), `core/rpa/vault.py` e
`core/rpa/fila.py`.

## 3. TLS (HTTPS) — tráfego cifrado

Gere um certificado (self-signed serve para testar):

```bash
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout data/chave.pem -out data/cert.pem \
  -subj "/CN=rpa.local" \
  -addext "subjectAltName=DNS:rpa.local,IP:192.168.0.10"
```

Suba a Control Room com TLS (ou use `TLS_CERT`/`TLS_CHAVE` no `.env`):

```bash
python -m core.control_room.servidor \
    --host 0.0.0.0 --cert data/cert.pem --chave data/chave.pem
```

Os agentes passam a usar `https://`:

```bash
python -m core.control_room.agente \
    --control-room https://192.168.0.10:8765 \
    --maquina maquina-sp-01 --token um-segredo-forte
```

O painel de trace (`/monitor/`) também sobe em HTTPS. Como o certificado é
self-signed, o navegador vai pedir para confirmar uma vez.

> Se o OpenSSL do seu Mac não aceitar `-addext`, crie um arquivo de config com
> `[v3_req] subjectAltName=...` e passe `-extensions v3_req -config seu.cnf`.

## 4. Fora da rede: VPN/overlay com Tailscale

Para máquinas em redes diferentes (casa, escritório, cloud), o caminho mais
simples e seguro é um **overlay** — todas entram numa rede privada virtual e a
Control Room continua sendo "local" para os agentes.

1. Instale o [Tailscale](https://tailscale.com/download) nas máquinas.
2. Em cada uma: `tailscale up` e faça login na mesma conta.
3. `tailscale ip -4` mostra o IP (ex.: `100.101.102.103`).
4. Suba a Control Room com `HOST_CONTROL_ROOM=0.0.0.0` (o Tailscale já cifra o
   tráfego; o token continua valendo como 2ª camada).
5. Aponte os agentes para `http://100.101.102.103:8765`.

Vantagens: sem abrir portas no roteador, sem IP fixo, tráfego cifrado pelo
WireGuard. **Alternativas ao Tailscale**: [ZeroTier](https://www.zerotier.com/)
ou um WireGuard/OpenVPN próprio.

### Control Room hospedada (internet)

Se preferir expor a Control Room diretamente, faça **sempre** as três coisas
juntas: (1) `CONTROL_ROOM_TOKEN` forte, (2) TLS com certificado válido
(Let's Encrypt) e (3) um proxy reverso (Caddy/Nginx) na frente. Sem token +
TLS, qualquer um com a URL dispara jobs na sua rede.

## 5. Push em tempo real (SSE)

Os painéis usam **SSE (Server-Sent Events)** — sem dependências extras:

- Control Room: `GET /api/orq/eventos`
- Monitor: `GET /api/eventos`

O navegador recebe `data: {"rev": <n>}` sempre que algo muda (job, fila,
máquina, execução) e recarrega sozinho; se o SSE cair, o painel volta ao
auto-refresh por polling automaticamente.

## 6. Checklist rápido

- [ ] `CONTROL_ROOM_TOKEN` forte definido? (nunca comitar o `.env`)
- [ ] `HOST_CONTROL_ROOM=0.0.0.0` só quando precisar de outra máquina.
- [ ] TLS ligado (`--cert/--chave`) se o tráfego sai da LAN/VPN?
- [ ] Preferir Tailscale/overlay a abrir porta no roteador.
- [ ] Agente como serviço (`scripts/instalar_agente_mac.sh`, Atalho/Tarefa no
      Windows, ou o pacote instalável) para reconectar sozinho.
