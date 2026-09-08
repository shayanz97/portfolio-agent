# Portfolio Agent

## Milestone 10 — Production Hardening

Implemented:
- production configuration
- SQLAlchemy repositories for runtime position state and graph/run state
- startup recovery service
- broker reconciliation before graph start
- fail-closed startup behavior
- production circuit-breaker counters
- structured JSON audit logger
- in-memory metrics facade
- database healthcheck
- Alembic migration environment
- SQLite batch-migration support
- durable LangGraph checkpointer factory:
  - memory
  - SQLite
  - PostgreSQL
- Postgres checkpoint setup hook
- deployable CLI/service entrypoint
- `healthcheck`
- `init-db`
- `show-config`
- tests for repository roundtrip, startup recovery and circuit-breaker behavior

### Durable LangGraph persistence

Production target:
`PostgresSaver`

Local/dev option:
`SqliteSaver`

The application keeps LangGraph workflow checkpoints separate from domain
persistence. Strategy runs, positions, orders, fills, alerts and performance
remain ordinary domain database records.

### Startup sequence

1. load and validate configuration
2. check database connectivity
3. verify/apply migrations
4. restore runtime position state
5. restore alert/risk state
6. reconcile domain state against IBKR
7. fail closed on mismatch
8. create durable LangGraph checkpointer
9. compile graph
10. permit analysis/paper execution

### Database migrations

Alembic is configured against SQLAlchemy `Base.metadata`.

For SQLite, batch migration mode is enabled because SQLite has limited ALTER
TABLE support.

Typical commands:

```bash
alembic revision --autogenerate -m "schema update"
alembic upgrade head
```

### Service commands

```bash
portfolio-agent healthcheck
portfolio-agent init-db
portfolio-agent show-config
```

### Remaining work before real deployment

- wire real IBKR TWS facade callbacks
- wire real market/news providers
- replace in-memory alert registry with DB repository
- store fill/execution lifecycle persistently end-to-end
- configure PostgreSQL in deployment
- run real Alembic revisions instead of `create_all`
- add external metrics backend (Prometheus/OpenTelemetry)
- add secrets manager
- add container/systemd deployment files
- perform paper-account soak testing
- perform restart/recovery chaos tests

At this point the architecture is feature-complete enough to begin real provider
integration and long-running paper validation.
