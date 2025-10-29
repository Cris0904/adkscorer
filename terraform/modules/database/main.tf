# Database Module - Cloud SQL Postgres with pgvector

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "authorized_networks" {
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

# Cloud SQL Instance
resource "google_sql_database_instance" "etl_postgres" {
  name             = "etl-movilidad-db"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = true

    # Enable pgvector extension
    database_flags {
      name  = "cloudsql.enable_pgvector"
      value = "on"
    }

    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
      }
    }

    # Maintenance window
    maintenance_window {
      day          = 7 # Sunday
      hour         = 3
      update_track = "stable"
    }

    # IP configuration
    ip_configuration {
      ipv4_enabled    = true
      require_ssl     = true

      dynamic "authorized_networks" {
        for_each = var.authorized_networks
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.value
        }
      }
    }

    # Insights
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
    }
  }

  deletion_protection = true

  lifecycle {
    prevent_destroy = true
  }
}

# Database
resource "google_sql_database" "etl_db" {
  name     = var.db_name
  instance = google_sql_database_instance.etl_postgres.name
  project  = var.project_id
}

# User
resource "google_sql_user" "etl_user" {
  name     = var.db_user
  instance = google_sql_database_instance.etl_postgres.name
  password = var.db_password
  project  = var.project_id
}

# Outputs
output "connection_name" {
  value       = google_sql_database_instance.etl_postgres.connection_name
  description = "Connection name for Cloud SQL Proxy"
}

output "connection_string" {
  value       = "postgresql://${var.db_user}:${var.db_password}@/${var.db_name}?host=/cloudsql/${google_sql_database_instance.etl_postgres.connection_name}"
  description = "Connection string for applications"
  sensitive   = true
}

output "public_ip" {
  value       = google_sql_database_instance.etl_postgres.public_ip_address
  description = "Public IP address"
}

output "private_ip" {
  value       = google_sql_database_instance.etl_postgres.private_ip_address
  description = "Private IP address"
}
