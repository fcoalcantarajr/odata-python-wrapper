<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-005: Filter DSL — builder composável de expressões $filter

- id: SPEC-005
- slug: filter-dsl
- status: DRAFT
- created: 2026-05-22
- owner: @opencode

## User Story

As a desenvolvedor que constrói queries OData, I want um builder composável de expressões `$filter` que trata escaping de aspa simples, formato datetime ISO 8601, null handling, e combinação lógica (and/or/not), so that eu possa montar filtros complexos sem manipular strings manualmente e sem tomar 400 do serviço ADO por escaping ou formato inválido.

## Use Cases

- UC1: `Filter.eq("Field", value)` → `$filter=Field eq 'value'` ou `Field eq 42` ou `Field eq null` conforme tipo.
- UC2: `Filter.and_(...)`, `Filter.or_(...)` → combinação lógica com parênteses aninhados.
- UC3: `Filter.not_(...)` → negação com prefixo `not (...)`.
- UC4: `Filter.contains("Field", "sub")` → `$filter=contains(Field, 'sub')`.
- UC5: Escape de aspa simples em valores string: `O'Keefe` → `O''Keefe` (HR-12 gotcha 6).
- UC6: Datetime ISO 8601 sem prefixo `datetime'`: `2025-01-15T00:00:00Z` (HR-11 gotcha 7).
- UC7: Comparadores: `eq`, `ne`, `gt`, `ge`, `lt`, `le` com tratamento de tipo (string, número, bool, null).
- UC8: Null handling: `Filter.eq("AssignedTo", None)` → `AssignedTo eq null`.

## Acceptance Criteria (Gherkin absoluto)

Cada AC tem Then **observável** (igualdade de string, ausência de substring, exceção nomeada). Nenhum Then não-observável como "funcionar bem" ou "ser correto".

### AC-1: eq com valor string produz Field eq 'value'

```
Given uma instância de Filter com `Filter.eq("Title", "Bug")`
When invoco `filter.build()`
Then o resultado é a string `"Title eq 'Bug'"`
```

### AC-2: aspa simples em valor string é escapada (HR-12 gotcha 6)

```
Given uma instância de Filter com `Filter.eq("AssignedTo/UserName", "O'Keefe")`
When invoco `filter.build()`
Then o resultado contém `"AssignedTo/UserName eq 'O''Keefe'"`
	And o resultado NÃO contém `"O'Keefe"` sem aspas duplicadas
```

### AC-3: and_ combina dois filtros com parênteses

```
Given `Filter.and_(Filter.eq("State", "Active"), Filter.eq("Priority", "1"))`
When invoco `filter.build()`
Then o resultado é `"(State eq 'Active' and Priority eq '1')"`
```

### AC-4: or_ combina com parênteses

```
Given `Filter.or_(Filter.eq("A", "1"), Filter.eq("B", "2"))`
When invoco `filter.build()`
Then o resultado é `"(A eq '1' or B eq '2')"`
```

### AC-5: not_ produz negação

```
Given `Filter.not_(Filter.eq("State", "Closed"))`
When invoco `filter.build()`
Then o resultado é `"not (State eq 'Closed')"`
```

### AC-6: contains gera função OData

```
Given `Filter.contains("Title", "security")`
When invoco `filter.build()`
Then o resultado é `"contains(Title, 'security')"`
	And o resultado tem formato `contains(FieldName, 'value')` sem parênteses extra
```

### AC-7: datetime em ISO 8601 SEM prefixo datetime' (HR-11 gotcha 7)

```
Given `Filter.gt("ChangedDate", "2025-01-15T00:00:00Z")`
When invoco `filter.build()`
Then o resultado é `"ChangedDate gt 2025-01-15T00:00:00Z"`
	And o resultado NÃO contém a substring `"datetime'"`
```

### AC-8: null handling — eq com None gera "Field eq null"

```
Given `Filter.eq("AssignedTo", None)`
When invoco `filter.build()`
Then o resultado é `"AssignedTo eq null"`
```

### AC-9: aninhamento profundo and/or preserva precedência

```
Given `Filter.or_(Filter.and_(Filter.eq("A", "1"), Filter.eq("B", "2")), Filter.eq("C", "3"))`
When invoco `filter.build()`
Then o resultado é `"((A eq '1' and B eq '2') or C eq '3')"`
```

### AC-10: comparador ne (not equal)

```
Given `Filter.ne("State", "Deleted")`
When invoco `filter.build()`
Then o resultado é `"State ne 'Deleted'"`
```

## NFRs

- **Performance:** `Filter.build()` executa em tempo linear O(n) no número de nós da árvore. Deve completar em < 1ms para expressões de até 10 nós (não faz IO, sem alocações pesadas).
- **Security:** Nenhum valor de filtro com conteúdo sensível vaza em logs de nível INFO ou superior. Em DEBUG, valores completos podem ser logados com PAT mascarado separadamente (não compete a este módulo).
- **Observability:** A classe Filter é puramente funcional/stateless. Nenhum efeito colateral. Qualquer logging futuro deve ser `logging.getLogger(__name__).debug(...)`.

## INVEST self-score

- **I**ndependent: 10/10 — zero dependências externas; não precisa de network nem de outras specs.
- **N**egotiable:  8/10 — nome dos métodos (eq, and_) e API interna (ExactValue vs FilterNode) podem mudar; o comportamento observável não.
- **V**aluable:    9/10 — sem o builder, cada query precisaria de string concat manual, fonte certa de 400 por escaping errado.
- **E**stimable:   9/10 — árvore de expressões em Python é padrão (~20 classes, ~150 linhas em `query/_filter.py`).
- **S**mall:       9/10 — cabe em 1 sessão de impl (~2h). Um arquivo `_filter.py` + um teste.
- **T**estable:    10/10 — 10 AC todos observáveis por `assert` de igualdade string ou `not in`.

Média: 9.2/10 → APPROVED-elegible.

## Out-of-scope

- Parsing reverso de string `$filter` para árvore Filter (parser OData).
- Validação de nomes de campo contra schema OData do ADO.
- Suporte a funções OData adicionais (`startswith`, `endswith`, `substringof`, `length`, etc.) — futuras specs.
- `$apply` expressions com `filter()` aninhado (→ SPEC-010).
- Serialização da query option completa como URL (→ SPEC-009, `query/_serialize.py`).
- POST `$batch` (→ SPEC-008).
- Suporte a propriedades de navegação (ex: `$filter=AssignedTo/UserName eq ...`) exceto via string literal no field name.

## Test plan

- AC-1 → `tests/unit/test_filter_dsl.py::test_ac1_eq_string_value`
- AC-2 → `tests/unit/test_filter_dsl.py::test_ac2_single_quote_escaping`
- AC-3 → `tests/unit/test_filter_dsl.py::test_ac3_and_combination`
- AC-4 → `tests/unit/test_filter_dsl.py::test_ac4_or_combination`
- AC-5 → `tests/unit/test_filter_dsl.py::test_ac5_not_negation`
- AC-6 → `tests/unit/test_filter_dsl.py::test_ac6_contains_function`
- AC-7 → `tests/unit/test_filter_dsl.py::test_ac7_datetime_no_prefix`
- AC-8 → `tests/unit/test_filter_dsl.py::test_ac8_null_handling`
- AC-9 → `tests/unit/test_filter_dsl.py::test_ac9_nested_and_or_precedence`
- AC-10 → `tests/unit/test_filter_dsl.py::test_ac10_ne_comparator`

## DoD

- [ ] 10 testes RED escritos por `atlas` via `/test-first`
- [ ] `test-first-guard` retorna CONTINUE
- [ ] `hephaestus` implementa Filter builder em `src/ado_odata_async/query/_filter.py`
- [ ] 10 testes GREEN em `uv run pytest -q tests/unit/test_filter_dsl.py`
- [ ] Coverage do módulo `query/_filter.py` ≥ 85%
- [ ] `uv run ruff check .` exit 0
- [ ] `uv run mypy src/` strict exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES respeitadas: HR-11 (datetime sem prefixo), HR-12 (escape aspa simples)
- [ ] Conventional Commit emitido por `git-keeper` referenciando `(SPEC-005)`
