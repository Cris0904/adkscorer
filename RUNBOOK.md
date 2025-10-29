# Runbook - ETL Movilidad Medellín

Guía operativa para administradores del sistema ETL.

## Tabla de Contenidos

1. [Inicio Rápido](#inicio-rápido)
2. [Operaciones Diarias](#operaciones-diarias)
3. [Troubleshooting](#troubleshooting)
4. [Mantenimiento](#mantenimiento)
5. [Incidentes Comunes](#incidentes-comunes)
6. [Contactos](#contactos)

---

## Inicio Rápido

### Accesos Necesarios

- **GCP Console**: https://console.cloud.google.com/
  - Proyecto: `etl-movilidad-mde`
  - Rol mínimo: Viewer (para métricas), Editor (para operaciones)

- **n8n UI**: [URL de tu instancia]
  - Usuario: `admin`
  - Password: [Ver Secret Manager: N8N_BASIC_AUTH_PASSWORD]

- **Base de Datos**:
  ```bash
  export DATABASE_URL="[Ver Secret Manager: DATABASE_URL]"
  psql $DATABASE_URL
  ```

- **Slack**:
  - Canal alertas: `#movilidad-alertas`
  - Canal errores: `#etl-errors`

### Verificación de Salud

```bash
# Script automático
./scripts/check-kpis.sh

# Manual: Health checks
curl https://adk-scorer-xxx.run.app/health
curl https://scraper-adv-xxx.run.app/health

# Database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM news_item WHERE created_at > NOW() - INTERVAL '1 hour';"
```

**Valores esperados**:
- Items última hora: > 5
- Servicios Cloud Run: 200 OK
- Error rate: < 2%

---

## Operaciones Diarias

### Monitoreo Matutino (9am)

1. **Verificar ejecuciones nocturnas**
   ```sql
   SELECT
     source,
     COUNT(*) as executions,
     SUM(items_kept) as kept,
     AVG(duration_seconds) as avg_duration,
     SUM(CASE WHEN errors::text != '[]' THEN 1 ELSE 0 END) as errors
   FROM etl_execution_log
   WHERE started_at > NOW() - INTERVAL '12 hours'
   GROUP BY source;
   ```

2. **Revisar alertas en Slack**
   - Canal `#etl-errors`: Deben ser 0 o < 3
   - Canal `#movilidad-alertas`: Revisar noticias críticas

3. **Verificar KPIs**
   ```bash
   ./scripts/check-kpis.sh | tee /tmp/kpis-$(date +%Y%m%d).log
   ```

### Monitoreo Continuo

**Dashboards**:
- [Cloud Run Dashboard](https://console.cloud.google.com/run)
- [Cloud SQL Dashboard](https://console.cloud.google.com/sql)
- [Logs Explorer](https://console.cloud.google.com/logs)

**Alertas Automáticas**:
- Email si error rate > 20% en 15 min
- Slack si ingesta < 5 items/hora
- Slack si servicio Cloud Run down

### Checklist Semanal

- [ ] Revisar costos en GCP Billing
- [ ] Verificar tamaño de DB (no exceder 80% del disco)
- [ ] Revisar logs de n8n (eliminar ejecuciones > 30 días)
- [ ] Verificar backups de DB exitosos
- [ ] Revisar distribución de severidad (ajustar prompts si necesario)

---

## Troubleshooting

### ETL No Ejecuta

**Síntoma**: No hay ejecuciones en última hora

**Diagnóstico**:
```bash
# 1. Verificar cron habilitado en n8n
# n8n UI → Workflows → ETL Movilidad Main → Check if Active

# 2. Ver última ejecución
# n8n UI → Executions → Sort by Date DESC

# 3. Verificar TZ
# n8n Settings → General → Timezone = America/Bogota
```

**Soluciones**:
- Cron deshabilitado → Activar workflow
- Error en última ejecución → Ver logs, corregir y re-ejecutar manualmente
- TZ incorrecta → Ajustar en env vars de n8n, reiniciar

---

### Items No Se Insertan en DB

**Síntoma**: Ejecuciones sin errores pero `items_kept = 0`

**Diagnóstico**:
```bash
# 1. Verificar scoring results
# n8n Execution Logs → Nodo "ADK Score" → Ver output

# 2. Check keep rate
psql $DATABASE_URL -c "
SELECT
  source,
  AVG(CASE WHEN scoring->'keep' = 'true' THEN 1 ELSE 0 END) as keep_rate
FROM (
  SELECT source, scoring::jsonb
  FROM etl_execution_log, jsonb_array_elements(errors) as scoring
  WHERE started_at > NOW() - INTERVAL '24 hours'
) t
GROUP BY source;
"
```

**Soluciones**:

1. **ADK descarta todo** (keep_rate < 0.1):
   - Problema: Prompts muy restrictivos
   - Solución: Ajustar `adk-scorer/app/prompts.py`
   - Ejemplo: Reducir threshold de relevancia, ampliar criterios

2. **Duplicados** (hash_url ya existe):
   - Problema: Fuente no tiene noticias nuevas
   - Solución: Normal si fuente lenta, monitorear 24h

3. **Error en DB insert**:
   - Verificar conexión: `psql $DATABASE_URL -c "SELECT 1;"`
   - Ver logs de n8n: Buscar errores de Postgres

---

### Alta Latencia (> 10s)

**Síntoma**: Ejecuciones demoran > 10 minutos

**Diagnóstico**:
```bash
# Ver duración por nodo
# n8n Execution Logs → Ver timeline de cada nodo

# Cloud Run metrics
gcloud run services describe adk-scorer --region=us-central1 --format=json | jq '.status.latestReadyRevision'

# DB slow queries
psql $DATABASE_URL -c "
SELECT
  query,
  mean_exec_time,
  calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;
"
```

**Soluciones**:

1. **Cold Start de Cloud Run**:
   - Problema: min_instances=0, primer request lento
   - Solución: Aumentar min_instances a 1 (incrementa costo)
   ```bash
   gcloud run services update adk-scorer --min-instances=1 --region=us-central1
   ```

2. **ADK Scoring lento**:
   - Problema: Prompts muy largos (> 2000 tokens)
   - Solución: Reducir body a 1000 chars en normalización
   - Alternativa: Usar Gemini Flash en vez de Pro

3. **Scraper timeout**:
   - Problema: Sitio externo lento (> 10s)
   - Solución: Aumentar timeout o skip esa fuente

4. **DB queries lentos**:
   - Problema: Falta índice o tabla muy grande
   - Solución: ANALYZE, VACUUM, crear índices
   ```sql
   VACUUM ANALYZE news_item;
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_missing ON news_item(campo);
   ```

---

### Scraper Bloqueado

**Síntoma**: Status 403/429 en scraper

**Diagnóstico**:
```bash
# Ver logs de scraper
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=scraper-adv" --limit 50 | grep -i "403\|429\|blocked"
```

**Soluciones**:

1. **Rate limit excedido**:
   - Problema: Demasiadas requests al mismo sitio
   - Solución: Aumentar delay entre requests en n8n (ej: Wait 5s)

2. **IP bloqueada**:
   - Problema: Sitio bloquea IPs de GCP
   - Solución: Rotar User-Agent, usar proxies (no implementado en MVP)

3. **robots.txt violation**:
   - Problema: Scrapeando URL prohibida
   - Solución: Verificar robots.txt, ajustar URLs

---

### Embeddings No Se Generan

**Síntoma**: `has_embedding = false` para items recientes

**Diagnóstico**:
```sql
SELECT
  COUNT(*) as total,
  COUNT(ne.id) as with_embeddings,
  ROUND(100.0 * COUNT(ne.id) / COUNT(*), 1) as percentage
FROM news_item ni
LEFT JOIN news_embedding ne ON ni.id = ne.news_id
WHERE ni.created_at > NOW() - INTERVAL '24 hours';
```

**Soluciones**:

1. **OpenAI API down/quota**:
   - Verificar: Logs de n8n → Nodo "Generate Embedding"
   - Solución: Esperar o aumentar quota

2. **Nodo deshabilitado**:
   - Verificar: n8n workflow → Nodo embeddings activo
   - Solución: Activar nodo

3. **Error en insert**:
   - Verificar: Logs SQL → Constraint violations
   - Solución: Revisar schema, corregir tipos de datos

---

### Alertas No Llegan

**Síntoma**: Noticia con severity=critical pero sin alerta en Slack

**Diagnóstico**:
```bash
# 1. Verificar items con alta severidad sin alertar
psql $DATABASE_URL -c "
SELECT id, title, severity, created_at
FROM news_item
WHERE severity IN ('high', 'critical')
  AND created_at > NOW() - INTERVAL '1 hour'
LIMIT 10;
"

# 2. Ver logs de nodo Slack
# n8n Execution → Nodo "Slack - Send Alert" → Check output/errors

# 3. Test webhook
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"🧪 Test desde ETL"}'
```

**Soluciones**:

1. **Webhook inválido**:
   - Verificar: Slack webhook URL actualizada
   - Solución: Rotar en Secret Manager, actualizar n8n credentials

2. **Condición IF incorrecta**:
   - Verificar: n8n workflow → Nodo IF "High Severity" → Condition
   - Esperado: `{{$json.severity}} in ['high', 'critical']`

3. **Nodo deshabilitado**:
   - Verificar: Nodo de alerta habilitado en workflow

---

## Mantenimiento

### Rotación de Secrets (cada 90 días)

```bash
# 1. Generar nuevos valores
NEW_SLACK_WEBHOOK="https://hooks.slack.com/services/NEW/..."
NEW_TELEGRAM_TOKEN="1234567890:NEW..."

# 2. Actualizar en Secret Manager
echo -n "$NEW_SLACK_WEBHOOK" | gcloud secrets versions add SLACK_WEBHOOK --data-file=-
echo -n "$NEW_TELEGRAM_TOKEN" | gcloud secrets versions add TELEGRAM_TOKEN --data-file=-

# 3. Actualizar en n8n credentials
# n8n UI → Credentials → Edit → Save

# 4. Verificar funcionamiento
# Forzar ejecución manual y verificar alertas

# 5. Eliminar versiones antiguas (después de 7 días)
gcloud secrets versions destroy VERSION_ID --secret=SLACK_WEBHOOK
```

### Limpieza de Base de Datos

**Automático**: Workflow `etl-movilidad-maintenance` (diario 3am)

**Manual** (si necesario):
```sql
-- Archivar noticias > 90 días
UPDATE news_item
SET status = 'archived'
WHERE status = 'active'
  AND published_at < NOW() - INTERVAL '90 days';

-- Limpiar logs > 30 días
DELETE FROM etl_execution_log
WHERE started_at < NOW() - INTERVAL '30 days';

-- Vacuum
VACUUM ANALYZE news_item;
VACUUM ANALYZE news_embedding;
VACUUM ANALYZE etl_execution_log;
```

### Actualización de Servicios

**ADK Scorer**:
```bash
cd adk-scorer

# 1. Hacer cambios en código
# 2. Build y deploy
gcloud builds submit --config=cloudbuild.yaml

# 3. Verificar
gcloud run revisions list --service=adk-scorer --region=us-central1

# 4. Test
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://adk-scorer-xxx.run.app/health

# 5. Rollback si necesario
gcloud run services update-traffic adk-scorer \
  --to-revisions=adk-scorer-PREVIOUS_REVISION=100 \
  --region=us-central1
```

**Scraper** (similar):
```bash
cd scraper-adv
npm run build
gcloud builds submit --config=cloudbuild.yaml
```

**n8n Workflows**:
```bash
# 1. Export workflow actual (backup)
# n8n UI → Workflow → Download

# 2. Hacer cambios
# 3. Activar nueva versión
# 4. Monitorear ejecuciones (1h)
# 5. Rollback si errores:
#    - Desactivar workflow
#    - Import versión anterior
#    - Activar
```

### Escalado de Recursos

**Cloud Run** (si latencia alta):
```bash
# Aumentar CPU/memoria
gcloud run services update adk-scorer \
  --cpu=2 \
  --memory=2Gi \
  --region=us-central1

# Aumentar max instances
gcloud run services update adk-scorer \
  --max-instances=20 \
  --region=us-central1
```

**Cloud SQL** (si DB lenta):
```bash
# Upgrade tier
gcloud sql instances patch etl-movilidad-db \
  --tier=db-g1-small

# Aumentar storage
gcloud sql instances patch etl-movilidad-db \
  --storage-size=20GB
```

---

## Incidentes Comunes

### INCIDENTE: Cloud Run Down

**Severidad**: Crítica
**Impacto**: ETL no procesa nuevas noticias

**Acciones**:
1. Verificar status en Cloud Console
2. Ver logs de error en Logging
3. Si error de deployment → Rollback a revisión anterior
4. Si cuota excedida → Aumentar cuota o esperar reset
5. Notificar a equipo en Slack
6. Documentar en postmortem

**Postmortem Template**:
```markdown
## Incident: Cloud Run adk-scorer Down

**Date**: YYYY-MM-DD HH:MM
**Duration**: X hours
**Root Cause**: [Descripción]
**Impact**: X ejecuciones fallidas, Y noticias no procesadas
**Resolution**: [Acciones tomadas]
**Prevention**: [Cambios para evitar recurrencia]
```

---

### INCIDENTE: Database Full

**Severidad**: Alta
**Impacto**: Inserts fallan, ejecuciones con error

**Acciones**:
1. Verificar espacio:
   ```sql
   SELECT pg_size_pretty(pg_database_size('etl_movilidad'));
   ```
2. Limpieza urgente:
   ```sql
   DELETE FROM etl_execution_log WHERE started_at < NOW() - INTERVAL '7 days';
   UPDATE news_item SET status = 'archived' WHERE published_at < NOW() - INTERVAL '30 days';
   VACUUM FULL;
   ```
3. Aumentar storage en Cloud SQL
4. Revisar retention policies

---

### INCIDENTE: Alta Error Rate (> 20%)

**Severidad**: Media
**Impacto**: Calidad de datos degradada

**Acciones**:
1. Identificar fuente problemática:
   ```sql
   SELECT source, COUNT(*) as errors
   FROM etl_execution_log
   WHERE errors::text != '[]'
     AND started_at > NOW() - INTERVAL '1 hour'
   GROUP BY source
   ORDER BY errors DESC;
   ```
2. Deshabilitar fuente temporalmente si > 50% error rate
3. Investigar root cause (API down, cambio de schema, etc.)
4. Ajustar extractor o skip fuente
5. Re-habilitar después de fix

---

## Contactos

### Equipo

- **Tech Lead**: [Nombre] - [email] - Slack: @user
- **DevOps**: [Nombre] - [email] - Slack: @user
- **On-Call**: Ver rotación en [URL]

### Escalación

1. **Incidente Menor** (< 1h impacto):
   - Notificar en Slack `#etl-errors`
   - Investigar y resolver
   - Documentar en JIRA

2. **Incidente Mayor** (> 1h impacto):
   - Notificar Tech Lead
   - Crear incident en [Sistema]
   - Página a On-Call si fuera de horario
   - War room en Slack `#incident-etl`

3. **Incidente Crítico** (servicio completamente down):
   - Página inmediata a Tech Lead y On-Call
   - Activar incident response plan
   - Comunicar a stakeholders

### Recursos

- **Documentación**: Este repo `/docs`
- **Runbooks**: Este archivo
- **Dashboards**: [URL Metabase/Grafana]
- **Alertas**: Slack `#movilidad-alertas`, `#etl-errors`
- **Logs**: [GCP Logging URL]
- **Métricas**: [GCP Monitoring URL]

---

**Última actualización**: 2024-01-15
**Versión**: 1.0.0
**Dueño**: [Equipo ETL]
