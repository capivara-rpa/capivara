# Landing page — Capivara 🦫

Página estática (HTML + CSS + JS puro, sem build) para publicar no cPanel da Hostinger,
no mesmo esquema das outras páginas do portfólio (ex.: `/dashboards/vendas-bi/`).

```
capivara/
├── index.html
└── assets/
    ├── styles.css      tokens de design (cores, raios, sombras) no topo
    ├── app.js          tema claro/escuro, menu mobile, abas, copiar, animações
    └── img/
        ├── capivara.svg   mascote (placeholder até a ilustração oficial)
        ├── favicon.svg
        └── cr_light.jpg · cr_dark.jpg · agenda.jpg   prints reais da Control Room
```

## Publicar no cPanel

1. Compacte a pasta: `cd landing && zip -r capivara.zip capivara`
2. cPanel → **Gerenciador de Arquivos** → `public_html/`
3. **Carregar** o `capivara.zip` → botão direito → **Extract**
4. Acesse `https://arthurfaria.tech/capivara/`
5. No construtor do site, adicione um item de menu/botão com o link `/capivara/`
   (igual ao "Dashboards e relatórios").

> Quer embutir dentro de uma página do construtor? Use um bloco **Embed/HTML** com
> `<iframe src="/capivara/" style="width:100%;height:100vh;border:0"></iframe>`.
> O link direto costuma ficar melhor (SEO, rolagem e prévia no WhatsApp).

## Onde trocar o quê

| O quê | Onde |
|---|---|
| Número/texto do WhatsApp | `index.html` → links `wa.me/...` (plano Empresas e CTA final) |
| Link do repositório | `index.html` → `github.com/arthurfs11/Template_Python_RPA_Brasil` |
| Cores / raios / sombras | `assets/styles.css` → bloco `:root` e `[data-tema="escuro"]` |
| Mascote | substitua `assets/img/capivara.svg` pela ilustração oficial (mesmo nome) |
| Prints | regenere com a Control Room em `?sem-sse&tema=light` / `tema=dark` |

Easter egg: clique 3× na capivara do topo. 🦆
