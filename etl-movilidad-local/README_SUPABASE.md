# Migración a Supabase - ETL Movilidad Medellín

## Resumen

El sistema ETL Movilidad Medellín ahora soporta **Supabase** como base de datos en la nube, además de SQLite local. Esto permite:

- ✅ **Base de datos accesible desde cualquier lugar**
- ✅ **API REST automática** para consultar datos
- ✅ **Dashboard web** para visualizar noticias
- ✅ **Compartir datos** con otras personas/aplicaciones
- ✅ **Backups automáticos** y alta disponibilidad
- ✅ **Gratis** hasta 500MB de datos

## Guía Rápida de Configuración

### 1. Crear Proyecto en Supabase

1. Ve a https://supabase.com y crea una cuenta
2. Crea un nuevo proyecto: `etl-movilidad-medellin`
3. Anota la contraseña de la base de datos

### 2. Obtener Credenciales

En el dashboard de Supabase:

1. Ve a **Settings** → **API**
2. Copia:
   - **Project URL**: `https://tuproyecto.supabase.co`
   - **anon public key**: Empieza con `eyJ...`

### 3. Configurar Variables de Entorno

Edita `.env`:

```bash
# Activar Supabase
USE_SUPABASE=true

# Credenciales (reemplaza con las tuyas)
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Crear el Schema

1. En Supabase, ve a **SQL Editor**
2. Copia el contenido de `sql/supabase_schema.sql`
3. Pégalo y ejecuta (Run)

### 5. Instalar Dependencias

```bash
pip install supabase
```

O con requirements:

```bash
pip install -r requirements.txt
```

### 6. Probar la Conexión

```bash
python scripts/test_supabase.py
```

Deberías ver:
```
✓ ALL TESTS PASSED
Supabase is configured correctly and ready to use!
```

### 7. Ejecutar el Pipeline

```bash
python src/main.py
```

El pipeline ahora guardará datos en Supabase automáticamente.

## Migrar Datos Existentes (Opcional)

Si ya tienes datos en SQLite:

```bash
python scripts/migrate_sqlite_to_supabase.py
```

Esto copiará todos los datos de `data/etl_movilidad.db` a Supabase.

## Consultar Datos

### Desde el Dashboard de Supabase

1. Ve a **Table Editor**
2. Selecciona `news_item`
3. Filtra, ordena y exporta datos

### Desde Python

```bash
python scripts/query_supabase.py
```

Interfaz interactiva para:
- Ver noticias recientes
- Filtrar por severidad
- Buscar por texto
- Ver estadísticas

### Desde la API REST

```bash
# Obtener últimas 10 noticias
curl "https://tuproyecto.supabase.co/rest/v1/news_item?select=*&limit=10&order=published_at.desc" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY"

# Noticias de alta severidad
curl "https://tuproyecto.supabase.co/rest/v1/news_item?severity=eq.high&select=*" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY"
```

### Desde JavaScript/Web

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// Obtener noticias
const { data, error } = await supabase
  .from('news_item')
  .select('*')
  .order('published_at', { ascending: false })
  .limit(10)
```

## Estructura de la Base de Datos

### Tabla `news_item`

Campos principales:
- `id`: ID único
- `source`: Fuente (Metro, Alcaldía, etc.)
- `url`: URL de la noticia
- `title`: Título
- `body`: Contenido
- `severity`: Severidad (low, medium, high, critical)
- `tags`: Etiquetas (JSONB)
- `area`: Área afectada
- `summary`: Resumen generado por ADK
- `relevance_score`: Puntaje de relevancia
- `published_at`: Fecha de publicación
- `created_at`: Fecha de inserción

### Tabla `execution_log`

Registra cada ejecución del pipeline:
- `execution_time`: Timestamp
- `news_extracted`: Noticias extraídas
- `news_scored`: Noticias calificadas
- `news_kept`: Noticias guardadas
- `duration_seconds`: Duración

## Archivos Importantes

```
etl-movilidad-local/
├── sql/
│   └── supabase_schema.sql          # Schema SQL para Supabase
├── src/
│   ├── db.py                        # SQLite (original)
│   ├── db_supabase.py               # Supabase (nuevo)
│   └── main.py                      # Pipeline (actualizado)
├── scripts/
│   ├── test_supabase.py             # Prueba de conexión
│   ├── query_supabase.py            # Consultar datos
│   └── migrate_sqlite_to_supabase.py # Migración
├── docs/
│   └── SUPABASE_SETUP.md            # Guía detallada
└── .env                             # Configuración
```

## Cambiar entre SQLite y Supabase

Para usar **SQLite** (local):
```bash
USE_SUPABASE=false
```

Para usar **Supabase** (nube):
```bash
USE_SUPABASE=true
```

El código soporta ambas opciones sin cambios adicionales.

## Ventajas de Supabase

### Para Desarrollo
- Dashboard visual para explorar datos
- API REST sin código adicional
- SQL Editor para queries avanzadas
- Logs de todas las operaciones

### Para Producción
- Alta disponibilidad (99.9% uptime)
- Backups automáticos diarios
- Escalamiento automático
- Row Level Security (RLS)

### Para Compartir
- URLs públicas para APIs
- Fácil integración con aplicaciones web
- Tiempo real (suscripciones a cambios)
- Múltiples clientes (Python, JS, Go, etc.)

## Plan Gratuito de Supabase

Incluye:
- ✅ 500 MB de base de datos PostgreSQL
- ✅ 1 GB de almacenamiento de archivos
- ✅ 2 GB de ancho de banda
- ✅ 50,000 usuarios activos mensuales
- ✅ Row Level Security
- ✅ Backups (7 días de retención)
- ✅ API REST automática
- ✅ Realtime subscriptions

Suficiente para:
- Miles de noticias
- Múltiples consultas diarias
- Varios usuarios consultando datos

## Ejemplos de Uso

### Dashboard Público

Puedes crear un dashboard web simple:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Noticias Movilidad Medellín</title>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
</head>
<body>
    <h1>Últimas Noticias de Movilidad</h1>
    <div id="news-list"></div>

    <script>
        const supabase = window.supabase.createClient(
            'TU_SUPABASE_URL',
            'TU_ANON_KEY'
        );

        async function loadNews() {
            const { data, error } = await supabase
                .from('news_item')
                .select('*')
                .order('published_at', { ascending: false })
                .limit(20);

            const list = document.getElementById('news-list');
            data.forEach(news => {
                list.innerHTML += `
                    <div class="news-item">
                        <h3>${news.title}</h3>
                        <p><strong>Severidad:</strong> ${news.severity}</p>
                        <p>${news.summary}</p>
                        <a href="${news.url}">Leer más</a>
                    </div>
                `;
            });
        }

        loadNews();
    </script>
</body>
</html>
```

### Webhook/Notificaciones

Configura webhooks en Supabase para recibir notificaciones cuando se insertan noticias de alta severidad.

### Integración con BI Tools

Conecta Supabase directamente con herramientas como:
- Metabase
- Tableau
- Power BI
- Google Data Studio

## Seguridad

### Row Level Security (RLS)

El schema incluye políticas:
- **Lectura pública**: Cualquiera puede leer (útil para APIs públicas)
- **Escritura privada**: Solo el service_role puede escribir

Para más privacidad:
1. Modifica las políticas en **Authentication** → **Policies**
2. Usa autenticación de Supabase
3. Usa la `service_role` key (solo en servidor)

### Mejores Prácticas

- ✅ Usa `anon public` key para acceso público de lectura
- ✅ Usa `service_role` key solo en el servidor (nunca en frontend)
- ✅ Habilita RLS para todas las tablas
- ✅ Crea políticas específicas según necesidades
- ✅ Monitorea el uso en el dashboard

## Troubleshooting

### "relation 'news_item' does not exist"
**Solución**: Ejecuta `sql/supabase_schema.sql` en SQL Editor

### "Invalid API key"
**Solución**: Verifica `SUPABASE_KEY` en `.env`

### "Row Level Security policy violation"
**Solución**: Usa `service_role` key o ajusta políticas RLS

### Queries lentas
**Solución**: Los índices ya están creados. Para optimizar más:
- Revisa el Query Planner en Supabase
- Añade índices específicos según tus consultas
- Usa paginación con `limit` y `offset`

## Próximos Pasos

1. ✅ Configurar Supabase
2. ✅ Migrar datos existentes
3. ✅ Ejecutar pipeline con Supabase
4. 🔜 Crear dashboard web para visualizar noticias
5. 🔜 Configurar alertas en tiempo real
6. 🔜 Integrar con aplicaciones móviles
7. 🔜 Crear API pública documentada

## Documentación Completa

Para más detalles, consulta:
- `docs/SUPABASE_SETUP.md` - Guía completa de configuración
- [Documentación de Supabase](https://supabase.com/docs)
- [Python Client Reference](https://supabase.com/docs/reference/python/introduction)

## Soporte

¿Preguntas o problemas?
1. Revisa los logs: `logs/etl_pipeline.log`
2. Consulta logs en Supabase: **Logs** → **API Logs**
3. Lee la documentación oficial
4. Pregunta en [Discord de Supabase](https://discord.supabase.com)
