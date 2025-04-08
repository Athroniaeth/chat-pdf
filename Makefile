# Makefile for production deployment

# Load environment variables from .env (not preprod)
include .env

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  update-prod  - Update production server with latest code"

# Update production server
.PHONY: update-prod
update-prod:
	@echo "Updating production server..."
	@echo "Using SSH_USER: $(SSH_USER)"
	@echo "Using SSH_HOST: $(SSH_HOST)"
	@echo "Using PROJECT_DIR: $(PROJECT_DIR)"

	@ssh $(SSH_USER)@$(SSH_HOST) "\
		echo 'Connected to production server...' && \
		cd $(PROJECT_DIR) && \
		echo 'Stopping Docker Compose services...' && \
		sudo docker compose down && \
		echo 'Pulling latest code from main branch...' && \
		git reset --hard HEAD~2 && \
		git pull origin main && \
		echo 'Rebuilding and starting Docker Compose services...' && \
		sudo docker compose -f compose.prod.yml up -d --build && \
		echo 'Deployment completed successfully!'"

# Check deployment status
.PHONY: check-prod
check-prod:
	@ssh $(SSH_USER)@$(SSH_HOST) "cd $(PROJECT_DIR) && sudo docker compose ps"
