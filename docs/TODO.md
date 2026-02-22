# TODO

## Docker Compose Local (`docker-compose-local.yml`)

Discovered during `docker compose -f docker-compose-local.yml up --build`:

- [ ] Green Agent: pass `OPENAI_API_KEY` env var (required by `settings.py`)
  - Add to `docker-compose-local.yml` green service environment, e.g.
    `OPENAI_API_KEY=${OPENAI_API_KEY}` or use an `.env` file
- [ ] Green Agent: `data/tasks/` directory is empty in the image
  - Task data must be generated first via `data_prep/` scripts
  - Either run data prep as a build step or mount `data/` as a volume
- [ ] Green Agent: Docker image used stale `tomli` (third-party) instead of
  `tomllib` (stdlib Python 3.13) — fixed, needs rebuild with `--no-cache`
- [ ] Purple Agent: `server.py` was empty (no `create_app`) — fixed with
  minimal stub (health + agent-card), full impl deferred to Purple Sprint 1
- [ ] Add Compose Watch (`develop.watch`) for live-reload during development
  - Docs: https://docs.docker.com/compose/file-watch/
  - Use `action: sync` for `src/` to hot-reload Python source into containers
  - Use `action: rebuild` for `pyproject.toml` / `uv.lock` (dependency changes)
  - Use `action: sync+restart` for `scenario.toml` (config reload needs restart)
  - Run with `docker compose -f docker-compose-local.yml up --watch`
  - Example for green service:
    ```yaml
    develop:
      watch:
        - action: sync
          path: ./src/green
          target: /app/src/green
        - action: sync+restart
          path: ./scenario.toml
          target: /app/scenario.toml
        - action: rebuild
          path: ./pyproject.toml
    ```
