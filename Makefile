.PHONY: sync bootstrap

sync:
	uv sync

bootstrap:
	./scripts/bootstrap_repo.sh
