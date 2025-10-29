# ETL Movilidad Medellín - Terraform Main Configuration

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "etl-movilidad-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Database Module
module "database" {
  source = "./modules/database"

  project_id       = var.project_id
  region           = var.region
  db_name          = var.db_name
  db_user          = var.db_user
  db_password      = var.db_password
  authorized_networks = var.authorized_networks
}

# Secret Manager Module
module "secrets" {
  source = "./modules/secrets"

  project_id = var.project_id
  secrets = {
    database_url      = module.database.connection_string
    slack_webhook     = var.slack_webhook_url
    telegram_token    = var.telegram_bot_token
    twitter_token     = var.twitter_bearer_token
    openai_api_key    = var.openai_api_key
  }
}

# Cloud Run - ADK Scorer
module "adk_scorer" {
  source = "./modules/cloud-run"

  project_id           = var.project_id
  region               = var.region
  service_name         = "adk-scorer"
  image                = var.adk_scorer_image
  service_account      = google_service_account.etl_runner.email
  memory               = "1Gi"
  cpu                  = "1"
  max_instances        = 10
  min_instances        = 0
  timeout              = 60
  allow_unauthenticated = false

  env_vars = {
    GCP_PROJECT_ID = var.project_id
    LOG_LEVEL      = "info"
  }

  secret_env_vars = {
    DATABASE_URL = module.secrets.secret_ids["database_url"]
  }
}

# Cloud Run - Scraper Advanced
module "scraper" {
  source = "./modules/cloud-run"

  project_id           = var.project_id
  region               = var.region
  service_name         = "scraper-adv"
  image                = var.scraper_image
  service_account      = google_service_account.etl_runner.email
  memory               = "2Gi"
  cpu                  = "1"
  max_instances        = 5
  min_instances        = 0
  timeout              = 60
  allow_unauthenticated = false

  env_vars = {
    NODE_ENV  = "production"
    LOG_LEVEL = "info"
  }
}

# Service Account for Cloud Run services
resource "google_service_account" "etl_runner" {
  account_id   = "etl-runner"
  display_name = "ETL Services Runner"
  description  = "Service account for ETL Cloud Run services"
}

# IAM: Cloud SQL Client
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.etl_runner.email}"
}

# IAM: Secret Manager Accessor
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.etl_runner.email}"
}

# IAM: Logs Writer
resource "google_project_iam_member" "logs_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.etl_runner.email}"
}

# Outputs
output "database_connection_name" {
  value       = module.database.connection_name
  description = "Cloud SQL connection name"
}

output "adk_scorer_url" {
  value       = module.adk_scorer.service_url
  description = "ADK Scorer service URL"
}

output "scraper_url" {
  value       = module.scraper.service_url
  description = "Scraper service URL"
}

output "service_account_email" {
  value       = google_service_account.etl_runner.email
  description = "Service account email for n8n authentication"
}
