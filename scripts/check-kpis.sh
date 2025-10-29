#!/bin/bash

# Script para consultar KPIs del ETL
# Uso: ./check-kpis.sh

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ETL Movilidad - KPI Dashboard ===${NC}\n"

if [ -z "$DATABASE_URL" ]; then
  echo -e "${RED}ERROR: DATABASE_URL no está configurada${NC}"
  echo "Configura: export DATABASE_URL='postgresql://user:pass@host:5432/etl_movilidad'"
  exit 1
fi

# KPIs Últimas 24h
echo -e "${YELLOW}[1] KPIs Últimas 24 horas por Fuente${NC}"
psql "$DATABASE_URL" -c "
SELECT
  hour,
  source,
  extracted,
  kept,
  discarded,
  keep_rate || '%' as keep_rate,
  avg_duration || 's' as avg_duration,
  error_count,
  error_rate || '%' as error_rate
FROM v_kpi_dashboard
WHERE hour > NOW() - INTERVAL '24 hours'
ORDER BY hour DESC, source
LIMIT 25;
"

echo ""

# Distribución de Severidad (7 días)
echo -e "${YELLOW}[2] Distribución por Severidad (últimos 7 días)${NC}"
psql "$DATABASE_URL" -c "
SELECT
  severity,
  count,
  percentage || '%' as percentage
FROM v_severity_distribution;
"

echo ""

# Top Áreas Afectadas
echo -e "${YELLOW}[3] Top 10 Áreas con Más Incidentes (últimos 7 días)${NC}"
psql "$DATABASE_URL" -c "
SELECT
  area,
  incident_count as total,
  high_severity_count as high_critical,
  TO_CHAR(last_incident, 'YYYY-MM-DD HH24:MI') as last_incident
FROM v_top_areas
LIMIT 10;
"

echo ""

# Resumen de Embeddings
echo -e "${YELLOW}[4] Estado de Embeddings${NC}"
psql "$DATABASE_URL" -c "
SELECT
  COUNT(*) as total_embeddings,
  COUNT(DISTINCT news_id) as news_with_embeddings,
  model,
  DATE(created_at) as date,
  COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h
FROM news_embedding
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY model, DATE(created_at)
ORDER BY date DESC
LIMIT 10;
"

echo ""

# Resumen General
echo -e "${YELLOW}[5] Resumen General${NC}"
psql "$DATABASE_URL" -c "
SELECT
  'Total Items Activos' as metric,
  COUNT(*)::TEXT as value
FROM news_item
WHERE status = 'active'
UNION ALL
SELECT
  'Items Últimas 24h',
  COUNT(*)::TEXT
FROM news_item
WHERE created_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
  'Items con Alta Severidad (7d)',
  COUNT(*)::TEXT
FROM news_item
WHERE severity IN ('high', 'critical')
  AND created_at > NOW() - INTERVAL '7 days'
  AND status = 'active'
UNION ALL
SELECT
  'Ejecuciones Últimas 24h',
  COUNT(*)::TEXT
FROM etl_execution_log
WHERE started_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
  'Tasa de Error (24h)',
  ROUND(100.0 * SUM(CASE WHEN errors::text != '[]' THEN 1 ELSE 0 END) / COUNT(*), 2)::TEXT || '%'
FROM etl_execution_log
WHERE started_at > NOW() - INTERVAL '24 hours';
"

echo ""
echo -e "${GREEN}=== Fin del Reporte ===${NC}"
