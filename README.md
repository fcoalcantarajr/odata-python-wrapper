# ado-odata-async

Client Python async para o **Azure DevOps Analytics OData** focado em **Work Tracking** (Boards).

- OData **v4.0-preview** (ADR-001)
- `aiohttp` + `pydantic` + `tenacity`
- SDLC **SDD + TDD** com agentes autônomos (opencode + omo)

## Setup

1. VS Code com extensão **Dev Containers**.
2. `cp .devcontainer/devcontainer.env.example .devcontainer/devcontainer.env` e preencha o PAT.
3. `Dev Containers: Reopen in Container`.
4. `opencode auth login` (free provider).

## Usage (preview — implementado em SPEC-001+)

    import asyncio
    from ado_odata_async import AdoODataClient

    async def main() -> None:
        async with AdoODataClient(org="myorg", project="myproject", pat="...") as c:
            # ... a definir nas próximas specs
            pass

    asyncio.run(main())

## Development

Ver `AGENTS.md` (HARD RULES) e `specs/000-TEMPLATE.md` (SDD).
Roda os 12 specs do backlog autonomamente com o handoff prompt do Step 9.