# Guia de início rápido

> Público: estagiário de primeiro ano, primeiro dia no banco, nunca usou Azure DevOps nem Python assíncrono.

Este guia mostra o passo a passo para fazer sua primeira consulta ao Azure Boards usando o `ado-odata-async`, do zero.

---

## Pré-requisitos

Antes de começar, você precisa de:

- **Python 3.12 ou superior** — confirme com `python --version` no terminal.
- **uv** — gerenciador de projetos Python (substituto do `pip`). Mais rápido e confiável.
- **Conta no Azure DevOps** com acesso a um projeto.
- **Permissão para criar PAT** (Personal Access Token) — fale com seu tech lead se não tiver.

---

## Instalando o uv

Se você ainda não tem o `uv` instalado, rode:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Depois, feche e abra o terminal (ou rode `source ~/.bashrc`) para carregar o comando.

Confirme que funcionou:

```bash
uv --version
```

> Se estiver em uma máquina do banco com restrições de instalação, peça ao time de infraestrutura para instalar o `uv` ou use `pip install uv` como fallback.

---

## Clonando o repositório

```bash
git clone https://github.com/ohmyopencode/odata-python-wrapper.git
cd odata-python-wrapper
```

Agora instale as dependências:

```bash
uv sync --all-groups
```

> A flag `--all-groups` instala também as dependências de teste (`aioresponses`, `pytest`, etc.). Sem ela, você não consegue rodar os testes ou os exemplos que usam essas bibliotecas.

---

## Criando seu PAT (Personal Access Token)

O PAT é a "senha" que seu script vai usar para acessar o Azure DevOps. Siga estes passos:

1. Acesse `https://dev.azure.com/{sua-organizacao}` e faça login.
2. No canto superior direito, clique no **avatar** (foto do perfil).
3. No menu, clique em **Personal access tokens**.
4. Clique em **+ New Token**.
5. Dê um nome como `ado-odata-async-estagio`.
6. Em **Organization**, selecione sua organização.
7. Em **Expiration**, escolha **30 dias** (nunca use "Never expiring" em ambiente bancário).
8. Em **Scopes**, clique em **Show all scopes** e selecione exclusivamente:
   - **Work Items** → **Read** (leitura de work items)
   - **Analytics** → **Read** (leitura de métricas)
9. Clique em **Create**.
10. **COPIE O TOKEN AGORA**. Após fechar a janela, você não poderá vê-lo novamente.

> ⚠️ **Regra de ouro**: este token dá acesso de leitura a dados do Azure DevOps. Nunca compartilhe, nunca commite no git, nunca envie por e-mail.

---

## Configurando o .env

Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo:

```bash
ADO_ORG=sua-organizacao
ADO_PROJECT=nome-do-seu-projeto
ADO_PAT=seu-token-aqui
```

A biblioteca também aceita as variáveis `AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT` e `AZURE_DEVOPS_PAT` como alternativa.

> **O arquivo `.env` já está no `.gitignore`** — isso significa que ele NÃO será versionado pelo git. Confirme com `git status` antes de commitar qualquer alteração.

---

## Seu primeiro script

Crie um arquivo chamado `meu_primeiro_script.py` com o código abaixo:

```python
"""Meu primeiro script com ado-odata-async."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Carrega as credenciais do arquivo .env
load_dotenv(".env")

pat = os.environ.get("ADO_PAT") or os.environ.get("AZURE_DEVOPS_PAT") or ""
org = os.environ.get("ADO_ORG") or os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("ADO_PROJECT") or os.environ.get("AZURE_DEVOPS_PROJECT") or ""

if not pat or not org or not project:
    print("ERRO: crie o arquivo .env com ADO_ORG, ADO_PROJECT e ADO_PAT")
    sys.exit(1)


async def main() -> None:
    """Busca os 5 work items mais recentes e imprime na tela."""
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    # O bloco 'async with' cria e fecha a conexão automaticamente
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .select("WorkItemId", "Title", "State", "WorkItemType")
            .top(5)
            .get()
        )

    items = result.get("value", [])
    print(f"Foram encontrados {len(items)} work items:\n")
    for item in items:
        wid = item["WorkItemId"]
        wtype = item["WorkItemType"]
        state = item["State"]
        title = item["Title"]
        print(f"  #{wid}  [{wtype}]  {state:20s}  {title}")


asyncio.run(main())
```

### Explicação linha a linha

| Linha | O que faz |
|---|---|
| `import asyncio` | Importa o módulo de programação assíncrona do Python (explicamos mais em [`docs/concepts.md`](concepts.md)). |
| `from dotenv import load_dotenv` | Carrega as variáveis do arquivo `.env` para as variáveis de ambiente. |
| `load_dotenv(".env")` | Executa o carregamento — sem isso, o Python não lê o `.env`. |
| `os.environ.get(...)` | Lê o valor da variável de ambiente (ou string vazia se não existir). |
| `AdoODataClient(org=..., project=..., pat=...)` | Cria o cliente de conexão com o Azure DevOps. |
| `async with ... as client:` | Abre a conexão (modo assíncrono) e garante que será fechada ao final. |
| `client.query("WorkItems")` | Cria um QueryBuilder apontando para a entidade "WorkItems". |
| `.select("WorkItemId", "Title", ...)` | Escolhe quais colunas trazer (menos colunas = resposta mais rápida). |
| `.top(5)` | Limita a 5 resultados. |
| `.get()` | Executa a consulta e aguarda a resposta. O `await` é essencial aqui. |
| `result["value"]` | A lista de work items vem dentro da chave `"value"` (padrão OData). |
| `asyncio.run(main())` | Ponto de entrada: roda a função `main()` de forma assíncrona. |

### Executando

```bash
uv run python meu_primeiro_script.py
```

Você deve ver algo como:

```
Foram encontrados 5 work items:

  #1234  [Tarefa]    Done                  Criar tela de login
  #1235  [Tarefa]    In Progress           Ajustar validação de CPF
  #1236  [Bug]       Concluído             Corrigir timeout na consulta
  #1237  [Tarefa]    Done                  Documentar endpoints
  #1238  [Tarefa]    To Do                 Configurar ambiente de staging
```

> Se aparecer `401 Unauthorized`, seu PAT pode ter expirado ou estar com escopo errado. Veja [`docs/troubleshooting.md`](troubleshooting.md).

---

## E agora?

| Próximo passo | Onde |
|---|---|
| Entender os conceitos por trás da biblioteca | [`docs/concepts.md`](concepts.md) |
| Ver receitas práticas (filtrar, paginar, calcular métricas) | [`docs/cookbook.md`](cookbook.md) |
| Consultar o glossário de termos técnicos | [`docs/glossary.md`](glossary.md) |
| Resolver erros comuns | [`docs/troubleshooting.md`](troubleshooting.md) |
