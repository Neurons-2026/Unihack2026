SHELL := /bin/sh

.PHONY: help build up down logs api-shell

help:
	@echo "Common commands:"
	@echo "  make build   Build all images"
	@echo "  make up      Start stack (detached)"
	@echo "  make down    Stop stack and remove containers"
	@echo "  make logs    Tail logs across services"
	@echo "  make api-shell Open a shell in the API container"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

api-shell:
	docker compose exec api /bin/sh
