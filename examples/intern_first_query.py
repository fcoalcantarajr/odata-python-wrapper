"""Primeiro consulta do estagiário: contar work items agrupados por StateCategory."""

import asyncio
import os
from pathlib import Path

# Carrega .env da raiz
env_path = Path(".env")
if env_path.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=env_path)
    except ImportError:
        # dotenv não disponível; analisa .env manualmente
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""

if not pat or not org or not project:
    print("ERRO: faltam AZURE_DEVOPS_ORG / AZURE_DEVOPS_PROJECT / AZURE_DEVOPS_PAT no .env")
    exit(1)


async def main() -> None:
    """Busca a contagem de work items agrupados por StateCategory."""
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Apply

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .apply(Apply().groupby("StateCategory").aggregate("$count", alias="Count"))
            .get()
        )

    rows = result.get("value", [])
    if not rows:
        print("Nenhum dado retornado")
        exit(1)

    print(f"\nContagem de work items por StateCategory ({len(rows)} categorias):\n")
    for row in rows:
        category = row.get("StateCategory") or "(nenhuma)"
        count = row.get("Count") or 0
        print(f"  {category!s:20s}  {count}")

    print(f"\nTotal de linhas: {len(rows)}")


asyncio.run(main())
