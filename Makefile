# AI Script Studio - Makefile
# Common tasks for development and deployment

.PHONY: help install test run clean lint format init-db deploy

# Default target
help:
	@echo "AI Script Studio - Available Commands:"
	@echo ""
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  run         - Start the application"
	@echo "  init-db     - Initialize database"
	@echo "  clean       - Clean temporary files"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  deploy      - Deploy to production"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	python -m pytest tests/ -v

# Start the application
run:
	python main.py run

# Initialize database
init-db:
	python main.py init-db

# Clean temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf logs/*.log

# Run linting
lint:
	flake8 src/ tests/
	black --check src/ tests/

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Deploy to production
deploy:
	@echo "Deploying to production..."
	# Add your deployment commands here
	@echo "Deployment complete!"

# Development setup
dev-setup: install init-db
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the application"
