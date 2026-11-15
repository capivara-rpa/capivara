# Como contribuir com o Capivara 🦫

Obrigado pelo interesse em ajudar! O Capivara é feito pela e para a comunidade
**Python Brasil**, e toda contribuição conta: correção de bug, nova função
utilitária, teste, exemplo ou melhoria na documentação.

## Onde cada coisa acontece

| Quero... | Onde |
|---|---|
| Reportar um bug | [Issues deste repositório](https://github.com/capivara-rpa/capivara/issues) |
| Sugerir uma ideia, abrir uma RFC ou compartilhar um exemplo | [`capivara-rpa/capivara-community`](https://github.com/capivara-rpa/capivara-community) |
| Enviar código ou documentação | Pull request para a branch **`next`** |

> A `main` é a versão **estável**. As propostas aceitas entram na `next` e
> chegam à `main` no próximo release. Por isso, abra seus PRs contra a `next`.

Para mudanças grandes (um módulo novo, uma alteração na Control Room ou algo que
quebre compatibilidade), abra antes uma discussão ou RFC no repositório da
comunidade. Assim ninguém perde tempo com um PR que vai na direção errada.

## Preparando o ambiente

Pré-requisito: **Python 3.11+**.

```bash
# 1. Faça um fork no GitHub e clone o seu fork
git clone https://github.com/<seu-usuario>/capivara.git
cd capivara

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Instale o projeto em modo editável com as ferramentas de dev (pytest + ruff)
pip install -e ".[dev]"

# 4. (Opcional) crie seu .env a partir do modelo
cp .env.example .env
```

Depois crie uma branch a partir da `next`:

```bash
git remote add upstream https://github.com/capivara-rpa/capivara.git
git fetch upstream
git switch -c minha-melhoria upstream/next
```

## Antes de abrir o PR

Rode as mesmas verificações do [GUIA.md](GUIA.md#13-verificações-de-qualidade-para-contribuir):

```bash
pytest
ruff check app core settings tests bot_test
python -m compileall -q app core settings bot_test
```

Os testes usam um diretório temporário para os bancos e **nunca tocam** em
`data/*.db`. Se o seu teste precisar de banco, siga o padrão de
[`tests/conftest.py`](tests/conftest.py).

## Padrões do projeto

### Tudo em português

Nomes de funções, parâmetros, mensagens de log, docstrings e exceções ficam em
português. É a proposta do projeto: quem está começando em RPA deve conseguir
ler o código sem tropeçar no inglês.

```python
def extrair_emails(texto: str) -> list[str]:
    """Devolve todos os e-mails encontrados no texto."""
```

### Estilo de código

- O `ruff` é a referência (linha de até 100 caracteres, alvo Python 3.11). A
  configuração está no [`pyproject.toml`](pyproject.toml).
- O [`.editorconfig`](.editorconfig) define UTF-8, 4 espaços e fim de linha LF.
  Use um editor que respeite esse arquivo.
- Use *type hints* e uma docstring curta em toda função pública.

### Onde colocar o código

- **`core/`** é o motor reutilizável. Funções utilitárias novas vão no módulo
  certo de [`core/rpa/`](core/rpa/) (`texto`, `validacao`, `dados`, `arquivo`...).
- **`app/`** é o robô de exemplo. Mude-o só para melhorar o exemplo.
- Veja [`data/docs/ARQUITETURA.md`](data/docs/ARQUITETURA.md) para entender
  como os módulos se relacionam.

### Adicionando uma função utilitária

1. Implemente no módulo de [`core/rpa/`](core/rpa/), seguindo o estilo dos vizinhos:
   - registre o que aconteceu com `logger` (Loguru);
   - em caso de erro esperado, lance `ErroRPA` (de `core.tratador`) com uma
     mensagem clara em português;
   - não adicione dependências novas sem discutir antes.
2. Escreva testes em `tests/test_<modulo>.py`.
3. Documente a função no
   [catálogo de funções](data/docs/CATALOGO_FUNCOES.md), com a assinatura e um exemplo.

## Commits

Use mensagens no formato [Conventional Commits](https://www.conventionalcommits.org/pt-br/),
com a descrição em português:

```text
feat: adiciona validar_pis em validacao
fix: corrige slug com caracteres especiais
docs: explica o token do dispositivo no GUIA
test: cobre rotação de assets no vault
refactor: simplifica claim de jobs na fila
```

Prefira commits pequenos e com um propósito só.

## Abrindo o pull request

- Aponte o PR para a branch **`next`**.
- Descreva **o que** mudou e **por quê**. Se fechar uma issue, escreva
  `Closes #123`.
- Se mexer em algo visual (Control Room, Monitor, TrackTab), inclua um print.
- Confirme que `pytest` e `ruff` passam.
- Atualize a documentação afetada (README, GUIA ou catálogo).

Um mantenedor vai revisar e pode pedir ajustes. Isso é normal e faz parte do
processo.

## Reportando bugs

Uma boa issue inclui:

- versão do Capivara (`pyproject.toml`), do Python e o sistema operacional;
- os passos para reproduzir o problema;
- o que você esperava e o que aconteceu;
- o trecho relevante do log em `data/logs/`, **sem senhas, tokens ou dados pessoais**.

> Encontrou uma falha de segurança (no vault, nos tokens de dispositivo ou na
> autenticação, por exemplo)? **Não abra uma issue pública.** Fale diretamente
> com os mantenedores pelo e-mail listado no [`pyproject.toml`](pyproject.toml).

## Licença

Ao contribuir, você concorda que a sua contribuição será distribuída sob a
[licença MIT](LICENSE) do projeto.
