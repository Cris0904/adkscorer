# ETL Movilidad Medellín

Sistema de extracción, procesamiento y alertas de noticias de movilidad urbana en Medellín usando ADK de Google (Gemini) como componente central de clasificación inteligente.

## ⚡ Quick Start

**¿Nuevo en el proyecto? Elige tu camino:**

### 🚀 Opción 1: MVP Local (Recomendado - 3-5 días)
Validación rápida y económica con script Python local.
- ⏱️ **Tiempo:** 3-5 días
- 💰 **Costo:** $0-5/mes
- 📖 **Seguir:** [RESUMEN_ANALISIS_MVP.md](./RESUMEN_ANALISIS_MVP.md) → [PLAN_MVP_LOCAL.md](./PLAN_MVP_LOCAL.md)

### ☁️ Opción 2: Cloud Completo (Producción - 25 días)
Sistema cloud-native escalable y robusto.
- ⏱️ **Tiempo:** 25 días
- 💰 **Costo:** $125-185/mes
- 📖 **Seguir:** [PLAN_IMPLEMENTACION.md](./PLAN_IMPLEMENTACION.md)

**¿No estás seguro?** Lee [COMPARATIVA_FINAL.md](./COMPARATIVA_FINAL.md) para decidir.

---

## Resumen del Sistema

- **Frecuencia**: Cada 5 minutos (cron: `*/5 * * * *`)
- **Fuentes**: Twitter/X, Metro Medellín, medios locales
- **Procesamiento**: Normalización → Deduplicación → Scoring ADK → Persistencia → Embeddings
- **Alertas**: Slack/Telegram para severidad alta/crítica
- **Stack Cloud**: n8n + Python (FastAPI) + Node.js (Express/Playwright) + Postgres + pgvector
- **Stack Local**: Python script + SQLite + Google Vertex AI (Gemini)

## Arquitectura

### Cloud (Opción 2)
```
Fuentes → n8n → [ADK Scorer | Scraper] → Postgres+pgvector → Alertas
```

### Local (Opción 1)
```
Fuentes → Python Script (ADK integrado) → SQLite → Alertas
```

Ver [ARQUITECTURA.md](./ARQUITECTURA.md) o [ANALISIS_MVP_LOCAL.md](./ANALISIS_MVP_LOCAL.md) para detalles.

## Documentación

### Análisis y Decisión
- [RESUMEN_ANALISIS_MVP.md](./RESUMEN_ANALISIS_MVP.md) - **EMPEZAR AQUÍ** - Resumen ejecutivo
- [COMPARATIVA_FINAL.md](./COMPARATIVA_FINAL.md) - Comparación Cloud vs Local
- [ANALISIS_MVP_LOCAL.md](./ANALISIS_MVP_LOCAL.md) - Análisis detallado de viabilidad

### Planes de Implementación
- [PLAN_MVP_LOCAL.md](./PLAN_MVP_LOCAL.md) - Plan día a día (3-5 días) - **Recomendado**
- [PLAN_IMPLEMENTACION.md](./PLAN_IMPLEMENTACION.md) - Plan cloud (25 días)

### Referencia Técnica
- [ARQUITECTURA.md](./ARQUITECTURA.md) - Arquitectura cloud detallada
- [RUNBOOK.md](./RUNBOOK.md) - Guía operativa
- [INDEX.md](./INDEX.md) - Índice completo de archivos

## Estructura del Proyecto

```
.
├── README.md                        # Este archivo
│
├── # Documentación (7 archivos)
├── RESUMEN_ANALISIS_MVP.md          # 🎯 Empezar aquí
├── PLAN_MVP_LOCAL.md                # Plan local (3-5 días)
├── COMPARATIVA_FINAL.md             # Decisión Cloud vs Local
├── ANALISIS_MVP_LOCAL.md            # Análisis de viabilidad
├── PLAN_IMPLEMENTACION.md           # Plan cloud (25 días)
├── ARQUITECTURA.md                  # Arquitectura detallada
├── RUNBOOK.md                       # Guía operativa
│
├── terraform/                  # Infraestructura como código
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── database/
│       ├── cloud-run/
│       └── secrets/
│
├── db-migrations/              # SQL schema y migraciones
│   ├── 001_initial_schema.sql
│   ├── functions/
│   ├── views/
│   └── maintenance/
│
├── adk-scorer/                 # Microservicio de scoring (Python)
│   ├── app/
│   │   ├── main.py
│   │   ├── scorer.py
│   │   ├── models.py
│   │   └── prompts.py
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── scraper-adv/                # Microservicio de scraping (Node.js)
│   ├── src/
│   │   ├── index.ts
│   │   ├── scraper.ts
│   │   └── config.ts
│   ├── tests/
│   ├── Dockerfile
│   ├── package.json
│   └── README.md
│
├── n8n-workflows/              # Workflows exportados (JSON)
│   ├── etl-movilidad-main.json
│   ├── etl-movilidad-health.json
│   ├── etl-movilidad-maintenance.json
│   └── README.md
│
└── scripts/                    # Utilidades y scripts de ops
    ├── check-kpis.sh
    ├── rotate-secrets.sh
    ├── test-e2e.sh
    └── dashboard.py
```

## Quick Start

### Pre-requisitos

- GCP project con billing habilitado
- n8n desplegado (Railway/Render/GCP VM)
- Postgres 15+ con pgvector
- Credenciales: Twitter API, Slack, Telegram

### Despliegue (Orden)

1. **Infraestructura Base**
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

2. **Base de Datos**
   ```bash
   psql $DATABASE_URL -f db-migrations/001_initial_schema.sql
   ```

3. **Microservicios**
   ```bash
   # ADK Scorer
   cd adk-scorer
   gcloud builds submit --config=cloudbuild.yaml

   # Scraper
   cd scraper-adv
   npm run build
   gcloud builds submit --config=cloudbuild.yaml
   ```

4. **n8n**
   - Importar workflows desde `n8n-workflows/`
   - Configurar credenciales (Postgres, Cloud Run, Slack, Telegram)
   - Activar cron triggers

5. **Validación**
   ```bash
   ./scripts/test-e2e.sh
   ```

Ver [PLAN_IMPLEMENTACION.md](./PLAN_IMPLEMENTACION.md) sección "Guía de Despliegue" para detalles completos.

## Componentes

### n8n Orquestador
- Cron cada 5 min (TZ: America/Bogota)
- Extracción multi-fuente
- Normalización y deduplicación
- Coordinación de microservicios
- Persistencia y alertas

### ADK Scorer (Cloud Run)
- Clasificación con Gemini 1.5 Flash
- Scoring: keep/discard, relevance, severity
- Tagging y extracción de entidades
- API REST: `POST /score`

### Scraper Avanzado (Cloud Run)
- Playwright para rendering JS
- Fallback cuando HTTP normal falla
- Rate limiting: 30 req/min
- API REST: `POST /fetch`

### Postgres + pgvector
- Tablas: `news_item`, `news_embedding`, `etl_execution_log`
- Búsqueda semántica con cosine similarity
- Vistas de KPIs y métricas
- Backups automáticos diarios

## Observabilidad

### Logs
```bash
# Ver logs de ADK Scorer
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adk-scorer" --limit 50

# Ver logs de Scraper
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=scraper-adv" --limit 50
```

### Métricas
```bash
# KPIs rápidos
./scripts/check-kpis.sh

# Consulta SQL directa
psql $DATABASE_URL -c "SELECT * FROM v_kpi_dashboard LIMIT 20;"
```

### Alertas
- **Slack**: `#movilidad-alertas` (noticias severidad high/critical)
- **Slack**: `#etl-errors` (errores de ejecución)
- **Telegram**: Grupo configurado (alertas duplicadas)

## Testing

### Tests Unitarios
```bash
# ADK Scorer
cd adk-scorer
pytest tests/ -v --cov=app

# Scraper
cd scraper-adv
npm test
```

### Tests E2E
```bash
./scripts/test-e2e.sh
```

### Smoke Test
```bash
# Forzar ejecución manual en n8n
# Verificar:
# - Items insertados en DB
# - Embeddings generados
# - Alertas enviadas (si severity=high)
# - Logs sin errores
```

## Costos Estimados

| Servicio | Costo/mes |
|----------|-----------|
| GCP (Cloud Run + SQL + Storage) | $15-50 |
| n8n (hosting) | $5-20 |
| Twitter API (opcional) | $100 |
| OpenAI Embeddings | $5-15 |
| **TOTAL** | **$125-185** |

Ver sección "Costos" en [PLAN_IMPLEMENTACION.md](./PLAN_IMPLEMENTACION.md) para detalles.

## Mantenimiento

### Tareas Automáticas
- **Diario (3am)**: Archivar noticias > 90 días, limpiar logs > 30 días
- **Cada hora**: Health check (ingesta, error rate, latencia)
- **Cada 5 min**: ETL principal

### Rotación de Secrets
```bash
./scripts/rotate-secrets.sh
```
Calendario: cada 90 días

### Backup y Restore
```bash
# Restore desde backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=etl-movilidad-db \
  --backup-instance=etl-movilidad-db

# Export manual
gcloud sql export sql etl-movilidad-db \
  gs://etl-movilidad-backups/manual-$(date +%Y%m%d).sql \
  --database=etl_movilidad
```

## Troubleshooting

### ETL no ejecuta
1. Verificar cron habilitado en n8n
2. Revisar TZ configurada: `America/Bogota`
3. Logs: n8n → Executions → Ver errores

### ADK Scorer retorna keep=false para todo
1. Verificar prompts en `adk-scorer/app/prompts.py`
2. Ajustar criterios de relevancia
3. Revisar logs: `reasoning` field

### Alta latencia (> 10s)
1. Verificar Cold Start en Cloud Run (min instances=0)
2. Optimizar prompts ADK (reducir tokens)
3. Revisar queries DB (EXPLAIN ANALYZE)
4. Considerar batching más agresivo

### Duplicados en DB
1. Verificar función `generate_hash_url()` idempotente
2. Check constraints: `UNIQUE (hash_url)`
3. Revisar logs de dedup step

## Seguridad

- ✅ Secrets en GCP Secret Manager (no en código)
- ✅ Cloud Run con OIDC (no público)
- ✅ Postgres con SSL requerido
- ✅ Rate limiting en Scraper
- ✅ Validación de input (Pydantic, Zod)
- ✅ Logs estructurados (no PII)

## Roadmap

- [ ] Dashboard visual (Metabase/Grafana)
- [ ] API pública para consultas
- [ ] ML para predicción de eventos
- [ ] App móvil con notificaciones push
- [ ] Integración con Waze/Google Maps
- [ ] Análisis de sentimiento
- [ ] Detección de tendencias

## Soporte

- **Documentación**: [PLAN_IMPLEMENTACION.md](./PLAN_IMPLEMENTACION.md), [ARQUITECTURA.md](./ARQUITECTURA.md)
- **Issues**: GitHub Issues
- **Slack**: `#etl-movilidad`
- **Email**: ops@example.com

## Licencia

MIT

---

**Versión**: 1.0.0
**Estado**: En desarrollo
**Última actualización**: 2024-01-15
