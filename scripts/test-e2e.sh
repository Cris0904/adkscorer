#!/bin/bash

# Test End-to-End del Sistema ETL Movilidad
# Uso: ./test-e2e.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== ETL Movilidad - Test E2E ===${NC}\n"

# Variables
PROJECT_ID=${GCP_PROJECT_ID:-"etl-movilidad-mde"}
REGION=${GCP_REGION:-"us-central1"}

# Verificar pre-requisitos
if [ -z "$DATABASE_URL" ]; then
  echo -e "${RED}ERROR: DATABASE_URL no está configurada${NC}"
  exit 1
fi

echo -e "${YELLOW}[1/7] Verificando servicios GCP...${NC}"
gcloud config set project "$PROJECT_ID" 2>/dev/null || {
  echo -e "${RED}ERROR: No se puede configurar el proyecto GCP${NC}"
  exit 1
}

# Obtener URLs de servicios
SCORER_URL=$(gcloud run services describe adk-scorer --region="$REGION" --format='value(status.url)' 2>/dev/null)
SCRAPER_URL=$(gcloud run services describe scraper-adv --region="$REGION" --format='value(status.url)' 2>/dev/null)

if [ -z "$SCORER_URL" ] || [ -z "$SCRAPER_URL" ]; then
  echo -e "${RED}ERROR: No se pudieron obtener URLs de servicios Cloud Run${NC}"
  exit 1
fi

echo -e "  - ADK Scorer: $SCORER_URL"
echo -e "  - Scraper: $SCRAPER_URL"
echo -e "${GREEN}  ✓ Servicios encontrados${NC}\n"

# Obtener token de autenticación
echo -e "${YELLOW}[2/7] Generando token de autenticación...${NC}"
TOKEN=$(gcloud auth print-identity-token)
echo -e "${GREEN}  ✓ Token obtenido${NC}\n"

# Test Health Checks
echo -e "${YELLOW}[3/7] Testing health checks...${NC}"

SCORER_HEALTH=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$SCORER_URL/health")
SCORER_STATUS=$(echo "$SCORER_HEALTH" | tail -n 1)

SCRAPER_HEALTH=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$SCRAPER_URL/health")
SCRAPER_STATUS=$(echo "$SCRAPER_HEALTH" | tail -n 1)

if [ "$SCORER_STATUS" != "200" ]; then
  echo -e "${RED}  ✗ ADK Scorer health check failed (status: $SCORER_STATUS)${NC}"
  exit 1
fi

if [ "$SCRAPER_STATUS" != "200" ]; then
  echo -e "${RED}  ✗ Scraper health check failed (status: $SCRAPER_STATUS)${NC}"
  exit 1
fi

echo -e "${GREEN}  ✓ ADK Scorer: OK${NC}"
echo -e "${GREEN}  ✓ Scraper: OK${NC}\n"

# Test ADK Scorer
echo -e "${YELLOW}[4/7] Testing ADK Scorer con noticia de prueba...${NC}"

TEST_NEWS=$(cat <<EOF
{
  "source": "test",
  "url": "https://test.com/e2e-$(date +%s)",
  "title": "Cierre total en Avenida El Poblado por manifestación",
  "body": "La Alcaldía de Medellín informó que la Avenida El Poblado estará cerrada desde las 2pm hasta las 8pm debido a una manifestación pacífica. Se recomienda tomar vías alternas.",
  "published_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
)

SCORE_RESULT=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$TEST_NEWS" \
  "$SCORER_URL/score")

KEEP=$(echo "$SCORE_RESULT" | jq -r '.keep')
SEVERITY=$(echo "$SCORE_RESULT" | jq -r '.severity')
SCORE=$(echo "$SCORE_RESULT" | jq -r '.relevance_score')

if [ "$KEEP" != "true" ]; then
  echo -e "${RED}  ✗ Expected keep=true for test news (got: $KEEP)${NC}"
  echo "  Response: $SCORE_RESULT"
  exit 1
fi

echo -e "${GREEN}  ✓ Keep: $KEEP${NC}"
echo -e "${GREEN}  ✓ Severity: $SEVERITY${NC}"
echo -e "${GREEN}  ✓ Score: $SCORE${NC}\n"

# Test Database Connection
echo -e "${YELLOW}[5/7] Testing database connection...${NC}"

DB_TEST=$(psql "$DATABASE_URL" -t -c "SELECT 1;" 2>&1)
if [ $? -ne 0 ]; then
  echo -e "${RED}  ✗ Database connection failed${NC}"
  echo "  Error: $DB_TEST"
  exit 1
fi

echo -e "${GREEN}  ✓ Database connection OK${NC}\n"

# Insert Test Data
echo -e "${YELLOW}[6/7] Testing data insertion...${NC}"

HASH_URL=$(echo -n "https://test.com/e2e-$(date +%s)" | sha256sum | cut -d' ' -f1)

INSERT_RESULT=$(psql "$DATABASE_URL" -t -c "
INSERT INTO news_item (
  source, url, hash_url, title, body, published_at,
  severity, relevance_score, area, tags, summary, status
)
VALUES (
  'test',
  'https://test.com/e2e-$(date +%s)',
  '$HASH_URL',
  'Test E2E News',
  'This is a test news item for E2E validation',
  NOW(),
  '$SEVERITY',
  $SCORE,
  'Test Area',
  ARRAY['test', 'e2e'],
  'Test summary',
  'active'
)
ON CONFLICT (hash_url) DO UPDATE SET updated_at = NOW()
RETURNING id;
" 2>&1)

if [ $? -ne 0 ]; then
  echo -e "${RED}  ✗ Data insertion failed${NC}"
  echo "  Error: $INSERT_RESULT"
  exit 1
fi

NEWS_ID=$(echo "$INSERT_RESULT" | xargs)
echo -e "${GREEN}  ✓ News item inserted (ID: $NEWS_ID)${NC}\n"

# Cleanup Test Data
echo -e "${YELLOW}[7/7] Cleaning up test data...${NC}"

psql "$DATABASE_URL" -c "DELETE FROM news_item WHERE source = 'test' AND status = 'active';" > /dev/null
echo -e "${GREEN}  ✓ Test data cleaned${NC}\n"

# Summary
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   E2E TEST PASSED SUCCESSFULLY ✓       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"

echo "Summary:"
echo "  - ADK Scorer: PASS"
echo "  - Scraper: PASS"
echo "  - Database: PASS"
echo "  - Data Flow: PASS"

echo ""
echo "Next steps:"
echo "  1. Import n8n workflows from n8n-workflows/"
echo "  2. Configure n8n credentials"
echo "  3. Enable cron triggers"
echo "  4. Monitor first executions"
