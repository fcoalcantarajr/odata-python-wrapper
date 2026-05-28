# ado-odata-async

Cliente **Python assíncrono** para o **Azure DevOps Analytics OData** — focado em dados de Work Tracking (Boards).

---

## Sobre

O `ado-odata-async` é uma biblioteca que permite consultar dados do Azure Boards (work items, histórico, métricas de fluxo) usando a API Analytics OData do Azure DevOps. Ela é **async-first** (aiohttp, não bloqueia rede), **type-safe** (Pydantic frozen + strict), e **OData-aware** (8 gotchas do Azure Analytics resolvidas na biblioteca) — mesmo se você nunca ouviu falar de OData ou async/await.

Tudo o que você precisa:
- Um PAT (Personal Access Token) com permissão de leitura
- Python 3.12 ou superior
- Dois minutos para instalar e rodar

---

## Por que existe?

A Microsoft mantém o pacote [`azure-devops-python-api`](https://github.com/microsoft/azure-devops-python-api), que é completo mas:

| Problema | Como o ado-odata-async resolve |
|---|---|
| Usa `requests` (síncrono) | Totalmente `async` com `aiohttp` — não bloqueia enquanto espera a rede |
| Dados genéricos (`dict`) | Retorna modelos Pydantic congelados (`WorkItem`, `WorkItemRevisions`, etc.) com tipos estritos |
| Foco em REST API (Azure DevOps) | Foco exclusivo em **Analytics OData** — a fonte certa para métricas de fluxo |
| Query string montada na mão | QueryBuilder fluente com autocomplete e serialização garantida |
| Erros genéricos | Exceções tipadas: `AuthenticationError`, `BadRequestError`, `TransientError`, `RateLimitError` |

Se você precisa de **cycle time**, **throughput**, **WIP** ou qualquer métrica de fluxo a partir do Azure Boards, esta biblioteca é para você.

---

## Início rápido

> ⏱ **5 minutos** do clone ao primeiro resultado.

```python
"""Primeira consulta com ado-odata-async."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Carrega .env do diretório atual (não do diretório do script)
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Lê credenciais — suporta ADO_* e AZURE_DEVOPS_* como fallback
pat = os.environ.get("ADO_PAT") or os.environ.get("AZURE_DEVOPS_PAT") or ""
org = os.environ.get("ADO_ORG") or os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("ADO_PROJECT") or os.environ.get("AZURE_DEVOPS_PROJECT") or ""

if not pat or not org or not project:
    print("ERRO: defina ADO_PAT, ADO_ORG e ADO_PROJECT no .env")
    sys.exit(1)

print(f"Conectando em {org}/{project} ...")


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .select("WorkItemId", "Title", "State", "WorkItemType")
            .top(5)
            .get()
        )

    items = result.get("value", [])
    print(f"\nEncontrados {len(items)} work items:\n")
    for item in items:
        print(f"  #{item['WorkItemId']}  [{item['WorkItemType']}]  {item['State']:20s}  {item['Title']}")


asyncio.run(main())
```

> **Antes de rodar**: crie um arquivo `.env` na raiz do projeto com:
> ```
> ADO_ORG=sua-org
> ADO_PROJECT=seu-projeto
> ADO_PAT=seu-personal-access-token
> ```
> Veja o [guia de início rápido](docs/getting-started.md) para instruções passo a passo.

---

## Exemplos

A pasta [`demo_flow_metrics.py`](demo_flow_metrics.py) contém um script completo (109 linhas) que calcula:

- **Cycle time** — tempo médio que os items ficam em Active até Closed
- **Throughput semanal** — quantos items são fechados por semana
- **WIP diário** — quantos items estão em andamento a cada dia

```python
# Trecho: calculando cycle time com a API paginada
from ado_odata_async import AdoODataClient
from ado_odata_async.query import Filter

async with AdoODataClient(org=org, project=project, pat=pat) as client:
    async for page in client.paginate(
        "WorkItems",
        top=200,
        query={
            "$filter": "StateCategory eq 'Completed'",
            "$select": "WorkItemId,Title,State,CreatedDate,ActivatedDate,ClosedDate",
            "$orderby": "ClosedDate desc",
        },
    ):
        for item in page.get("value", []):
            print(item["WorkItemId"], item["Title"], item.get("ClosedDate"))
```

---

## Conceitos rápidos

| Conceito | Em uma frase |
|---|---|
| **OData** | É um padrão REST com uma linguagem de consulta poderosa — como SQL para URLs. Você usa `$filter`, `$select`, `$top` para buscar exatamente o que precisa. |
| **Flow metrics** | São métricas que medem o fluxo de trabalho: cycle time (tempo de entrega), throughput (quantidade entregue) e WIP (trabalho em andamento). |

Veja explicações completas em [`docs/concepts.md`](docs/concepts.md).

---

## Documentação completa

| Arquivo | O que contém |
|---|---|
| [`docs/getting-started.md`](docs/getting-started.md) | Instalação, criação de PAT, primeiro script passo a passo |
| [`docs/concepts.md`](docs/concepts.md) | OData, WorkItems vs Revisions vs Snapshot, flow metrics, async/await |
| [`docs/cookbook.md`](docs/cookbook.md) | 8 receitas práticas: filtrar, paginar, calcular cycle time, exportar CSV, tratar erros |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Erros comuns: 401, 400, 203, ValidationError — sintoma → causa → solução |
| [`docs/glossary.md`](docs/glossary.md) | Definições de todos os termos técnicos usados na biblioteca |

---

## Segurança do PAT

> ⚠️ **Contexto bancário**: seu PAT (Personal Access Token) é uma senha que dá acesso de leitura ao Azure DevOps da organização. Trate-o com o mesmo cuidado que sua senha do banco.

1. **Escopo mínimo**: ao criar o PAT, selecione exclusivamente as permissões:
   - `Work Items (Read)`
   - `Analytics (Read)`
   - Nada mais. Princípio do menor privilégio.

2. **Expiração curta**: defina expiração para **30 dias** (no máximo 90). Crie um lembrete na agenda para renovar antes de expirar.

3. **Nunca commitar**: o PAT nunca deve ser versionado no git. O arquivo `.env` já está no `.gitignore` do projeto — confirme antes de dar `git add`.

4. **Roteação periódica**: a cada novo projeto ou ao final do estágio, revogue o token antigo e gere um novo. Siga a política de segurança da sua instituição.

5. **Compartilhamento zero**: não compartilhe seu PAT por e-mail, chat ou código. Se precisar compartilhar acesso, peça para a pessoa gerar o próprio token.

6. **Roteação (rotate)**: inclua a rotação do PAT no seu calendário — crie um lembrete recorrente. Bancos geralmente exigem rotação a cada 30-60 dias.

---

## Glossário rápido

| Termo | Significado |
|---|---|
| **OData** | Open Data Protocol — protocolo REST para consulta de dados |
| **PAT** | Personal Access Token — token de acesso pessoal para autenticação |
| **ADO** | Azure DevOps — plataforma de desenvolvimento da Microsoft |
| **WIP** | Work In Progress — trabalho em andamento |
| **Cycle time** | Tempo entre o início e a conclusão de um work item |
| **Throughput** | Quantidade de work items concluídos em um período |
| **Pydantic** | Biblioteca Python para validação de dados com tipos |

Consulte o [glossário completo](docs/glossary.md) para todos os termos.

---

## Solução de problemas

| Situação | O que fazer |
|---|---|
| `401 Unauthorized` | Seu PAT expirou ou está com escopo insuficiente. Crie um novo. |
| `HTTP 203 + HTML no body` | PAT inválido ou nome da organização errado. |
| `ModuleNotFoundError` | Rodou `uv sync` sem a flag `--all-groups`? Tente com ela. |
| `400 Bad Request` | Verifique a sintaxe do filtro. Faltou `as <alias>` no aggregate? |
| URL muito longa | A biblioteca faz batch automático acima de 3000 caracteres (configurável). |
| Não entendeu um termo | Consulte o [glossário](docs/glossary.md) — todas as siglas estão definidas lá. |
| Ainda travado | Abra uma [issue no GitHub](https://github.com/ohmyopencode/odata-python-wrapper/issues). |

Veja [`docs/troubleshooting.md`](docs/troubleshooting.md) para diagnósticos detalhados.

---

## Licença

MIT &copy; OhMyOpenCode