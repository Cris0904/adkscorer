# ETL Movilidad Medellín - MVP Local

Sistema de extracción, clasificación y alertas de noticias de movilidad en Medellín, Colombia.

## Características

- **Extracción multi-fuente**: Metro de Medellín, Alcaldía, AMVA
- **Clasificación inteligente**: Google ADK (Gemini 1.5 Flash) para scoring y etiquetado
- **Deduplicación**: Basada en hash SHA256 de URLs
- **Alertas automáticas**: Consola, archivo JSON, y email (opcional)
- **Scheduler**: Ejecución automática cada N minutos
- **Base de datos local**: SQLite, sin dependencias externas
- **Costo**: $0-5/mes (solo API calls de Vertex AI)

## Requisitos

- Python 3.9+
- Google Cloud Project con Vertex AI habilitado
- gcloud CLI instalado y autenticado

## Instalación Rápida

### 1. Clonar y preparar entorno

```bash
cd etl-movilidad-local

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Google Cloud

```bash
# Instalar gcloud CLI si no lo tienes
# https://cloud.google.com/sdk/docs/install

# Autenticar
gcloud auth application-default login

# Configurar proyecto
gcloud config set project YOUR_PROJECT_ID

# Habilitar Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

### 3. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus valores
# IMPORTANTE: Cambiar GOOGLE_CLOUD_PROJECT por tu project ID
```

Ejemplo de `.env` mínimo:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
USE_MOCK_ADK=false
SCHEDULE_INTERVAL_MINUTES=5
```

### 4. Probar instalación

```bash
# Ir al directorio src
cd src

# Modo de prueba (sin Google Cloud, usando mock)
# Editar .env: USE_MOCK_ADK=true
python main.py

# Modo real (con Google Cloud)
# Editar .env: USE_MOCK_ADK=false
python main.py
```

## Uso

### Ejecución manual única

```bash
cd src
python main.py
```

Esto ejecutará:
1. Extracción de noticias de todas las fuentes
2. Deduplicación
3. Scoring con ADK (Gemini)
4. Filtrado de relevantes
5. Guardado en base de datos
6. Alertas de alta severidad

### Ejecución automática con scheduler

```bash
cd src
python scheduler.py
```

El scheduler:
- Ejecuta el pipeline inmediatamente al iniciar
- Luego ejecuta cada N minutos (configurable en `.env`)
- Logs en `logs/scheduler.log`
- Detener con `Ctrl+C`

### Scripts de utilidad

```bash
# Probar extracción (sin ADK, sin guardar)
cd scripts
python test_extraction.py

# Ver estadísticas de la base de datos
python db_stats.py

# Ver alertas recientes
python view_alerts.py
```

## Estructura del proyecto

```
etl-movilidad-local/
├── src/
│   ├── main.py              # Pipeline principal
│   ├── scheduler.py         # Scheduler automático
│   ├── db.py               # Base de datos SQLite
│   ├── extractors.py       # Extractores multi-fuente
│   ├── adk_scorer.py       # Scorer con Google Gemini
│   ├── alert_manager.py    # Gestor de alertas
│   └── prompts/
│       └── system_prompt.py # Prompts optimizados para Medellín
├── scripts/
│   ├── test_extraction.py  # Prueba de extractores
│   ├── db_stats.py         # Ver estadísticas DB
│   └── view_alerts.py      # Ver alertas recientes
├── data/
│   └── etl_movilidad.db    # Base de datos SQLite (auto-creada)
├── logs/
│   ├── etl_pipeline.log    # Logs del pipeline
│   ├── scheduler.log       # Logs del scheduler
│   └── alerts.json         # Alertas en JSON
├── requirements.txt
├── .env.example
└── README.md
```

## Configuración avanzada

### Email Alerts

Para habilitar alertas por email, editar `.env`:

```env
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

**Nota para Gmail:**
1. Habilitar autenticación de 2 factores
2. Crear App Password: https://myaccount.google.com/apppasswords
3. Usar el App Password (no tu contraseña regular)

### Cambiar intervalo de ejecución

En `.env`:

```env
# Cada 5 minutos (default)
SCHEDULE_INTERVAL_MINUTES=5

# Cada 15 minutos (recomendado para bajo volumen)
SCHEDULE_INTERVAL_MINUTES=15

# Cada hora
SCHEDULE_INTERVAL_MINUTES=60
```

### Agregar fuentes de noticias

Editar `src/extractors.py`:

1. Crear método `extract_nueva_fuente()`
2. Agregar llamada en `extract_all()`
3. Retornar lista de dicts con estructura:

```python
{
    'source': 'Nombre de la fuente',
    'url': 'https://...',
    'title': 'Título de la noticia',
    'body': 'Contenido o resumen',
    'published_at': '2025-01-15T10:30:00'  # ISO format
}
```

## Costos estimados

### Google Cloud (Vertex AI)

Usando **Gemini 1.5 Flash** (más económico):

- **Input**: $0.075 / 1M tokens
- **Output**: $0.30 / 1M tokens

**Estimación mensual:**
- 50 noticias/día × 500 tokens/noticia = 25,000 tokens/día
- 750,000 tokens/mes input
- 75,000 tokens/mes output (resumen)
- **Costo: ~$0.08/mes input + $0.02/mes output = $0.10/mes**

Con margen de seguridad: **$0.50 - $2/mes**

### Infraestructura

- **Servidor local**: $0 (tu computadora)
- **SQLite**: $0
- **Total**: **$0.50 - $2/mes** (solo API calls)

## Modo de prueba (sin Google Cloud)

Para probar sin credenciales de Google Cloud:

1. Editar `.env`:
```env
USE_MOCK_ADK=true
```

2. Ejecutar:
```bash
cd src
python main.py
```

El **MockADKScorer** usa clasificación simple basada en keywords. Solo para testing.

## Troubleshooting

### Error: "GOOGLE_CLOUD_PROJECT environment variable required"

Solución:
1. Verificar que `.env` existe y tiene `GOOGLE_CLOUD_PROJECT=your-project-id`
2. O usar modo mock: `USE_MOCK_ADK=true`

### Error: "DefaultCredentialsError"

Solución:
```bash
gcloud auth application-default login
```

### Error: "API not enabled"

Solución:
```bash
gcloud services enable aiplatform.googleapis.com
```

### No se extraen noticias

Posibles causas:
1. URLs de las fuentes cambiaron (verificar en navegador)
2. Selectores CSS cambiaron (actualizar en `extractors.py`)
3. Problemas de conectividad

Verificar con:
```bash
cd scripts
python test_extraction.py
```

### Pipeline muy lento

Soluciones:
1. Reducir límite de noticias por fuente en `extractors.py` (línea ~69: `[:20]` → `[:10]`)
2. Aumentar intervalo de scheduler (`.env`: `SCHEDULE_INTERVAL_MINUTES=15`)

## Monitoreo

### Ver logs en tiempo real

```bash
# Pipeline
tail -f logs/etl_pipeline.log

# Scheduler
tail -f logs/scheduler.log
```

### Ver estadísticas de base de datos

```bash
cd scripts
python db_stats.py
```

Muestra:
- Total de noticias
- Por severidad
- Por fuente
- Últimas ejecuciones

### Ver alertas recientes

```bash
cd scripts
python view_alerts.py
```

O ver directamente:
```bash
cat logs/alerts.json
```

## Migración a producción cloud

Cuando el volumen crezca (>500 noticias/día), considera migrar a la versión cloud completa.

Ver documentación en el directorio raíz:
- `PLAN_IMPLEMENTACION.md`: Plan completo cloud
- `COMPARATIVA_FINAL.md`: Comparación detallada

Estrategia recomendada:
1. **Semana 1-2**: MVP Local (actual)
2. **Semana 3-4**: Optimización y validación
3. **Decision**: Si volumen > 500/día → migrar a cloud
4. **Mes 2-3**: Implementación cloud

## Soporte

Para problemas o dudas:
1. Verificar logs: `logs/etl_pipeline.log`
2. Verificar configuración: `.env`
3. Probar con mock: `USE_MOCK_ADK=true`
4. Revisar documentación de análisis: `../RESUMEN_ANALISIS_MVP.md`

## Licencia

MIT License - Ver archivo LICENSE
