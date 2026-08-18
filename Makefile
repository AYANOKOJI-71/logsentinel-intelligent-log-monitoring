.PHONY: api web test lint compose-up compose-down

api:
	uvicorn apps.api.main:app --host 127.0.0.1 --port $${LOGWATCH_API_PORT:-4300}

web:
	cd apps/web && npx --yes pnpm@10.6.3 run dev

test:
	pytest -q && cd apps/web && npx --yes pnpm@10.6.3 run test

lint:
	ruff check apps tests && cd apps/web && npx --yes pnpm@10.6.3 run lint

compose-up:
	docker compose up --build

compose-down:
	docker compose down --volumes
