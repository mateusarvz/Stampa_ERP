.PHONY: help build up down logs shell db-sync cleanup test dev prod

help:
	@echo "Stampa SaaS - Docker Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  build         - Build Docker image"
	@echo "  up            - Start container (default config)"
	@echo "  dev           - Start dev container (hot-reload code)"
	@echo "  prod          - Start prod container (optimized)"
	@echo "  down          - Stop containers"
	@echo "  logs          - View container logs"
	@echo "  shell         - Open bash shell in container"
	@echo "  gui           - Run GUI"
	@echo "  cli           - Run CLI setup"
	@echo "  db-sync       - Sync CSV to SQLite"
	@echo "  cleanup       - Run cleanup script"
	@echo "  test          - Run tests"
	@echo "  clean-all     - Remove containers, volumes, images"

build:
	@echo "Building image..."
	docker build -t stampa-saas:latest .
	@echo "✅ Done"

up:
	docker-compose up -d
	@echo "✅ Container running. Logs: make logs"

dev:
	docker-compose -f docker-compose.dev.yml up

prod:
	docker-compose -f docker-compose.prod.yml up -d

down:
	docker-compose down

logs:
	docker-compose logs -f stampa-saas

shell:
	docker-compose run --rm stampa-saas shell

gui:
	docker-compose run --rm stampa-saas gui

cli:
	docker-compose run --rm stampa-saas cli

db-sync:
	docker-compose run --rm stampa-saas db

cleanup:
	docker-compose run --rm stampa-saas cleanup

test:
	docker-compose run --rm stampa-saas test

clean-all:
	docker-compose down -v
	docker image rm stampa-saas:latest 2>/dev/null || true
	docker system prune -f
	@echo "✅ Cleaned up"

# Advanced
ps:
	docker-compose ps

volume-inspect:
	docker volume inspect stampa-data

volume-backup:
	@echo "Backing up data..."
	docker run --rm -v stampa-data:/data -v $$(pwd):/backup \
		ubuntu tar czf /backup/stampa-data-$$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "✅ Backup complete"

volume-restore:
	@echo "Restoring data..."
	docker run --rm -v stampa-data:/data -v $$(pwd):/backup \
		ubuntu tar xzf /backup/$$(ls -t backup/*.tar.gz | head -1) -C /data
	@echo "✅ Restored"
