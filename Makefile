# This Makefile automates the build, test, and clean processes for the project.
# It provides a convenient way to run common tasks using the 'make' command.
# It is designed to work with the 'uv' tool for managing Python environments and dependencies.
# Run `make help` to see all available recipes.

.SILENT:
.ONESHELL:
.PHONY: setup_dev setup_claude_code setup_sandbox setup_project setup_devc_project setup_devc_template markdownlint ruff ruff_tests complexity test_all test_quick test_coverage type_check validate quick_validate ralph_userstory ralph_prd_md ralph_prd_json ralph_init ralph_run ralph_status ralph_clean ralph_reorganize help
.DEFAULT_GOAL := help


# MARK: setup


setup_dev:  ## Install uv and all dependencies (Python, dev tools, Claude Code)
	echo "Setting up dev environment ..."
	pip install uv -q
	uv sync --all-groups
	$(MAKE) -s setup_claude_code

setup_claude_code:  ## Setup claude code CLI
	echo "Setting up Claude Code CLI ..."
	curl -fsSL https://claude.ai/install.sh | bash
	echo "Claude Code CLI version: $$(claude --version)"

setup_sandbox:  ## Install sandbox deps (bubblewrap, socat) for Linux/WSL2
	# Required for Claude Code sandboxing on Linux/WSL2:
	# - bubblewrap: Provides filesystem and process isolation
	# - socat: Handles network socket communication for sandbox proxy
	# Without these, sandbox falls back to unsandboxed execution (security risk)
	# https://code.claude.com/docs/en/sandboxing
	# https://code.claude.com/docs/en/settings#sandbox-settings
	# https://code.claude.com/docs/en/security
	echo "Installing sandbox dependencies ..."
	if command -v apt-get > /dev/null; then \
		sudo apt-get update -qq && sudo apt-get install -y bubblewrap socat; \
	elif command -v dnf > /dev/null; then \
		sudo dnf install -y bubblewrap socat; \
	else \
		echo "Unsupported package manager. Install bubblewrap and socat manually."; \
		exit 1; \
	fi
	echo "Sandbox dependencies installed."

setup_project:  ## Customize template with your project details. Run with help: bash scripts/setup_project.sh help
	bash scripts/setup_project.sh || {
		echo "";
		echo "ERROR: Project setup failed. Please check the error messages above.";
		exit 1;
	}

setup_devc_project:  ## Devcontainer: Full project env (sandbox + Python/Node deps + project customization)
	cp -r .claude/.claude.json ~/.claude.json
	$(MAKE) -s setup_sandbox
	$(MAKE) -s setup_dev
	# $(MAKE) -s setup_project

setup_devc_template:  ## Devcontainer: Template editing env (sandbox + Claude Code)
	$(MAKE) -s setup_sandbox
	$(MAKE) -s setup_claude_code


# MARK: Sanity


ruff:  ## Lint: Format and check with ruff (src only)
	uv run ruff format --exclude tests
	uv run ruff check --fix --exclude tests

ruff_tests:  ## Lint: Format and fix tests with ruff
	uv run ruff format tests
	uv run ruff check tests --fix

complexity:  ## Check cognitive complexity with complexipy
	uv run complexipy

test_all:  ## Run all tests
	uv run pytest

test_quick:  ## Quick test - rerun only failed tests (use during fix iterations)
	uv run pytest --lf -x

test_coverage:  ## Run tests with coverage threshold (configured in pyproject.toml)
	echo "Running tests with coverage gate (fail_under=70% in pyproject.toml)..."
	uv run pytest --cov

type_check:  ## Check for static typing errors
	uv run pyright src

validate:  ## Complete pre-commit validation sequence
	set -e
	echo "Running complete validation sequence..."
	$(MAKE) -s ruff
	$(MAKE) -s ruff_tests
	$(MAKE) -s type_check
	$(MAKE) -s complexity
	$(MAKE) -s test_coverage
	echo "Validation completed successfully"

quick_validate:  ## Fast development cycle validation
	echo "Running quick validation ..."
	$(MAKE) -s ruff
	$(MAKE) -s type_check
	echo "Quick validation completed (check output for any failures)"

markdownlint:  ## Fix markdown files. Usage: make run_markdownlint [INPUT_FILES="docs/**/*.md"] (default: docs/)
	INPUT=$${INPUT_FILES:-docs/}
	echo "Running markdownlint on $$INPUT ..."
	uv run pymarkdown fix --recurse $$INPUT
	uv run pymarkdown scan --recurse $$INPUT


# MARK: ralph


ralph_userstory:  ## [Optional] Create UserStory.md interactively. Usage: make ralph_userstory
	echo "Creating UserStory.md through interactive Q&A ..."
	claude -p "/generating-interactive-userstory-md"

ralph_prd_md:  ## [Optional] Generate PRD.md from UserStory.md
	echo "Generating PRD.md from UserStory.md ..."
	claude -p "/generating-prd-md-from-userstory-md"

ralph_prd_json:  ## [Optional] Generate PRD.json from PRD.md
	echo "Generating PRD.json from PRD.md ..."
	claude -p "/generating-prd-json-from-prd-md"

ralph_init:  ## Initialize Ralph loop environment
	echo "Initializing Ralph loop environment ..."
	bash ralph/scripts/init.sh

ralph_run:  ## Run Ralph autonomous development loop (MAX_ITERATIONS=N, MODEL=sonnet|opus|haiku)
	echo "Starting Ralph loop ..."
	RALPH_MODEL=$(MODEL) MAX_ITERATIONS=$(MAX_ITERATIONS) bash ralph/scripts/ralph.sh

ralph_status:  ## Show Ralph loop progress and status
	echo "Ralph Loop Status"
	echo "================="
	if [ -f ralph/docs/prd.json ]; then
		total=$$(jq '.stories | length' ralph/docs/prd.json)
		passing=$$(jq '[.stories[] | select(.passes == true)] | length' ralph/docs/prd.json)
		echo "Stories: $$passing/$$total completed"
		echo ""
		echo "Incomplete stories:"
		jq -r '.stories[] | select(.passes == false) | "  - [\(.id)] \(.title)"' ralph/docs/prd.json
	else
		echo "prd.json not found. Run 'make ralph_init' first."
	fi

ralph_clean:  ## Reset Ralph state (WARNING: removes prd.json and progress.txt)
	echo "WARNING: This will reset Ralph loop state!"
	echo "Press Ctrl+C to cancel, Enter to continue..."
	read
	rm -f ralph/docs/prd.json ralph/docs/progress.txt
	echo "Ralph state cleaned. Run 'make ralph_init' to reinitialize."

ralph_reorganize:  ## Archive current PRD and start new iteration. Usage: make ralph_reorganize NEW_PRD=path/to/new.md [VERSION=2]
	if [ -z "$(NEW_PRD)" ]; then
		echo "Error: NEW_PRD parameter required"
		echo "Usage: make ralph_reorganize NEW_PRD=docs/PRD-New.md [VERSION=2]"
		exit 1
	fi
	VERSION_ARG=""
	if [ -n "$(VERSION)" ]; then
		VERSION_ARG="-v $(VERSION)"
	fi
	bash ralph/scripts/reorganize_prd.sh $$VERSION_ARG $(NEW_PRD)


# MARK: help


help:  ## Displays this message with available recipes
	# TODO add stackoverflow source
	echo "Usage: make [recipe]"
	echo "Recipes:"
	awk '/^[a-zA-Z0-9_-]+:.*?##/ {
		helpMessage = match($$0, /## (.*)/)
		if (helpMessage) {
			recipe = $$1
			sub(/:/, "", recipe)
			printf "  \033[36m%-20s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH)
		}
	}' $(MAKEFILE_LIST)
