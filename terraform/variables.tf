# Terraform Variables - ETL Movilidad

variable "project_id" {
  type        = string
  description = "GCP Project ID"
  default     = "etl-movilidad-mde"
}

variable "region" {
  type        = string
  description = "GCP Region"
  default     = "us-central1"
}

# Database Variables
variable "db_name" {
  type        = string
  description = "Database name"
  default     = "etl_movilidad"
}

variable "db_user" {
  type        = string
  description = "Database user"
  default     = "etl_app"
}

variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}

variable "authorized_networks" {
  type = list(object({
    name  = string
    value = string
  }))
  description = "Authorized networks for Cloud SQL"
  default     = []
}

# Cloud Run Images
variable "adk_scorer_image" {
  type        = string
  description = "Container image for ADK Scorer"
  default     = "gcr.io/etl-movilidad-mde/adk-scorer:latest"
}

variable "scraper_image" {
  type        = string
  description = "Container image for Scraper"
  default     = "gcr.io/etl-movilidad-mde/scraper-adv:latest"
}

# External Secrets (injected via env or tfvars)
variable "slack_webhook_url" {
  type        = string
  description = "Slack webhook URL for alerts"
  sensitive   = true
}

variable "telegram_bot_token" {
  type        = string
  description = "Telegram bot token"
  sensitive   = true
}

variable "twitter_bearer_token" {
  type        = string
  description = "Twitter API bearer token"
  sensitive   = true
}

variable "openai_api_key" {
  type        = string
  description = "OpenAI API key for embeddings"
  sensitive   = true
}
