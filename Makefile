# Perintah operasional SILATARA. Hanya butuh Docker + Git (+ make, opsional; semua target = perintah docker compose).
.DEFAULT_GOAL := help
DC := docker compose

help: ## Tampilkan perintah
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

setup: ## Buat .env dari .env.example (sandi acak, UID/GID host)
	@./scripts/setup.sh

up: ## Build + jalankan semua service (foreground)
	$(DC) up --build
start: ## Build + jalankan di background
	$(DC) up --build -d
stop: ## Hentikan container (data TETAP)
	$(DC) stop
down: ## Hapus container & network (volume/data TETAP)
	$(DC) down
restart: ## Restart semua service (atau: make restart s=backend)
	$(DC) restart $(s)
rebuild: ## Build ulang image tanpa cache lalu jalankan
	$(DC) build --no-cache && $(DC) up -d
logs: ## Ikuti log (make logs s=backend)
	$(DC) logs -f --tail=100 $(s)
ps: ## Status & health
	$(DC) ps

shell-backend: ## Masuk container backend
	$(DC) exec backend bash
shell-frontend: ## Masuk container frontend
	$(DC) exec frontend bash
psql: ## Masuk psql
	$(DC) exec db sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB'

migrate: ## Terapkan migrasi (alembic upgrade head)
	$(DC) exec backend alembic upgrade head
migration: ## Buat migrasi baru: make migration m="tambah tabel x"
	$(DC) exec backend alembic revision --autogenerate -m "$(m)"
seed: ## Muat seed DEMO (fiktif)
	$(DC) exec backend python -m app.cli seed-demo
create-admin: ## Buat admin lokal: make create-admin email=a@b.test
	@test -n "$(email)" || (echo "Gunakan: make create-admin email=anda@contoh.test"; exit 1)
	$(DC) exec backend python -m app.cli create-admin --email $(email)

test: test-backend test-frontend ## Semua tes + lint + typecheck
test-backend:
	$(DC) exec backend ruff check .
	$(DC) exec backend pytest
test-frontend:
	$(DC) exec frontend npm run lint
	$(DC) exec frontend npm run typecheck
	$(DC) exec frontend npm test
smoke: ## Smoke test infrastruktur (stack harus berjalan)
	./scripts/smoke-test.sh
e2e: ## E2E TERISOLASI (stack terpisah, DB tmpfs): API+SSR lalu browser Playwright. Tidak menyentuh DB dev
	./scripts/e2e.sh all
e2e-api: ## Hanya E2E API+SSR terisolasi
	./scripts/e2e.sh api
e2e-browser: ## Hanya E2E browser terisolasi (Chromium: kamera palsu, visual, axe+kontras, auth)
	./scripts/e2e.sh browser
bench: ## Benchmark A/B terisolasi: main-thread (lama) vs Web Worker, kamera PALSU (±6 menit). Hasil: artifacts/benchmark.json
	RUN_BENCH=1 PW_ARGS="--project=camera-fake tests/camera-benchmark.spec.ts" ./scripts/e2e.sh browser
trivy: ## Pindai image prod (Trivy ter-pin): gagal bila ada HIGH/CRITICAL yang DAPAT diperbaiki
	./scripts/trivy-scan.sh
e2e-down: ## Matikan stack E2E terisolasi (hanya project silatara-e2e; tidak menyentuh stack dev)
	docker compose -f docker-compose.e2e.yml --profile browser down --remove-orphans
test-data-list: ## Tampilkan data uji yang ada di DB dev (tidak menghapus apa pun)
	./scripts/test-data.sh list
test-data-clean: ## Hapus data uji dari DB dev SETELAH backup + konfirmasi eksplisit
	./scripts/test-data.sh clean
a11y: ## Pemeriksaan aksesibilitas statis (axe-core) pada halaman live
	$(DC) exec -T frontend node a11y-check.mjs
mediapipe-assets: ## Unduh model MediaPipe (verifikasi SHA-256) ke frontend/public
	./scripts/fetch-mediapipe-assets.sh

backup: ## Cadangkan database ke ./backups
	./scripts/db-backup.sh
restore: ## Pulihkan: make restore f=backups/xxx.sql.gz
	./scripts/db-restore.sh $(f)

clean: ## Hapus container+network+image lokal; DATA DATABASE TETAP
	$(DC) down --remove-orphans --rmi local
reset-db: ## DESTRUKTIF: hapus SEMUA volume termasuk database (minta konfirmasi)
	./scripts/reset-all.sh
