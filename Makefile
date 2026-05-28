# Makefile for Shred-CLI
.PHONY: install install-dev test lint clean run run-fg stop status

# Default target
all: install

# Install the package
install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install -e .
	pip install pytest black flake8 mypy

# Run tests
test:
	python -m pytest tests/ -v

# Format code
format:
	black shredcli/

# Lint code
lint:
	flake8 shredcli/ --max-line-length=120
	mypy shredcli/

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the daemon in foreground (useful for debugging)
run:
	shred start --no-daemon

# Run the daemon in background
start:
	shred start

# Stop the daemon
stop:
	shred stop

# Check status
status:
	shred status

# View logs
logs:
	tail -f ~/.shredcli/shred.log

# Uninstall
uninstall:
	pip uninstall -y shred-cli
	rm -rf ~/.shredcli

# Help
help:
	@echo "Shred-CLI Makefile targets:"
	@echo "  install      - Install the package"
	@echo "  install-dev  - Install with dev dependencies"
	@echo "  run          - Run in foreground mode"
	@echo "  start        - Start background daemon"
	@echo "  stop         - Stop daemon"
	@echo "  status       - Check daemon status"
	@echo "  logs         - View daemon logs"
	@echo "  clean        - Clean build artifacts"
	@echo "  uninstall    - Uninstall completely"
