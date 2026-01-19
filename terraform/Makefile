# Makefile for Terraform operations

.PHONY: help init plan apply destroy validate format lint clean

# Default environment
ENV ?= dev

# Help target
help:
	@echo "Available targets:"
	@echo "  init      - Initialize Terraform for specified environment"
	@echo "  plan      - Plan Terraform changes for specified environment"
	@echo "  apply     - Apply Terraform changes for specified environment"
	@echo "  destroy   - Destroy Terraform resources for specified environment"
	@echo "  validate  - Validate Terraform configuration"
	@echo "  format    - Format Terraform files"
	@echo "  lint      - Lint Terraform files with tflint"
	@echo "  clean     - Clean Terraform cache and state files"
	@echo ""
	@echo "Usage: make <target> ENV=<environment>"
	@echo "Environments: dev, prod"
	@echo ""
	@echo "Examples:"
	@echo "  make init ENV=dev"
	@echo "  make plan ENV=prod"
	@echo "  make apply ENV=dev"

# Initialize Terraform
init:
	@echo "Initializing Terraform for $(ENV) environment..."
	cd environments/$(ENV) && terraform init

# Plan Terraform changes
plan:
	@echo "Planning Terraform changes for $(ENV) environment..."
	cd environments/$(ENV) && terraform plan

# Apply Terraform changes
apply:
	@echo "Applying Terraform changes for $(ENV) environment..."
	cd environments/$(ENV) && terraform apply

# Destroy Terraform resources
destroy:
	@echo "Destroying Terraform resources for $(ENV) environment..."
	cd environments/$(ENV) && terraform destroy

# Validate Terraform configuration
validate:
	@echo "Validating Terraform configuration..."
	@for dir in environments/*/; do \
		echo "Validating $$dir..."; \
		cd $$dir && terraform validate && cd ../..; \
	done
	@for dir in modules/*/; do \
		echo "Validating $$dir..."; \
		cd $$dir && terraform validate && cd ../..; \
	done

# Format Terraform files
format:
	@echo "Formatting Terraform files..."
	terraform fmt -recursive .

# Lint Terraform files (requires tflint)
lint:
	@echo "Linting Terraform files..."
	@if command -v tflint >/dev/null 2>&1; then \
		tflint --recursive .; \
	else \
		echo "tflint not found. Install it with: curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash"; \
	fi

# Clean Terraform cache and state files
clean:
	@echo "Cleaning Terraform cache and state files..."
	find . -type d -name ".terraform" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.tfstate*" -delete 2>/dev/null || true
	find . -name ".terraform.lock.hcl" -delete 2>/dev/null || true

# Development shortcuts
dev-init: ENV=dev
dev-init: init

dev-plan: ENV=dev
dev-plan: plan

dev-apply: ENV=dev
dev-apply: apply

dev-destroy: ENV=dev
dev-destroy: destroy

# Production shortcuts
prod-init: ENV=prod
prod-init: init

prod-plan: ENV=prod
prod-plan: plan

prod-apply: ENV=prod
prod-apply: apply

prod-destroy: ENV=prod
prod-destroy: destroy