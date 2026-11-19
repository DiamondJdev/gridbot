.DEFAULT_GOAL := help
.PHONY: help verify verify-ros verify-all

help:
	@printf '%s\n' \
	  'make help        List available targets' \
	  'make verify      Run Python, docs and TypeScript checks' \
	  'make verify-ros  Build and test the ROS 2 workspace in Docker' \
	  'make verify-all  Run all checks and the Compose smoke test'

verify:
	@scripts/step.sh "python lint" sh -c 'uv run ruff check . && uv run ruff format --check .'
	@scripts/step.sh "python types" uv run pyright
	@scripts/step.sh "python boundaries" uv run lint-imports
	@scripts/step.sh "python tests" uv run pytest
	@scripts/step.sh "scenarios (runner)" sh -c 'for scenario in scenarios/*.json; do uv run gridbot-run "$$scenario" || exit 1; done'
	@scripts/step.sh docs uv run python scripts/check_docs.py
	@scripts/step.sh "ts lint" sh -c 'pnpm exec eslint . && pnpm exec prettier --check .'
	@scripts/step.sh "ts types" pnpm -r typecheck
	@scripts/step.sh "ts tests" pnpm -r test
	@scripts/step.sh build pnpm -r build

verify-ros:
	@scripts/step.sh "ros tests" sh -c 'docker compose -f docker/compose.yaml --profile ros build ros && docker compose -f docker/compose.yaml --profile ros run --rm -T ros bash -c "colcon test && colcon test-result --verbose"'

verify-all:
	@$(MAKE) verify
	@$(MAKE) verify-ros
	@scripts/step.sh "compose smoke" bash scripts/e2e_compose.sh
