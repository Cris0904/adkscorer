# Configuración de Supabase para ETL Movilidad Medellín

Esta guía te ayudará a configurar Supabase como base de datos en la nube para el proyecto ETL Movilidad Medellín.

## ¿Por qué Supabase?

- **Gratis**: Hasta 500MB de base de datos PostgreSQL
- **API REST automática**: Acceso instantáneo vía HTTP
- **Tiempo real**: Suscripciones a cambios en la base de datos
- **Dashboard**: Interfaz web para ver y consultar datos
- **Row Level Security**: Seguridad a nivel de fila
- **Público**: Puedes compartir la URL y hacer queries desde cualquier lugar

## Paso 1: Crear Cuenta y Proyecto

1. Ve a [https://supabase.com](https://supabase.com)
2. Crea una cuenta gratuita (puedes usar GitHub, Google, etc.)
3. Haz clic en "New Project"
4. Completa:
   - **Name**: `etl-movilidad-medellin`
   - **Database Password**: (guarda esta contraseña en un lugar seguro)
   - **Region**: Selecciona la más cercana a tu ubicación
   - **Pricing Plan**: Free (incluye 500MB DB + 2GB storage)
5. Haz clic en "Create new project" (tarda 1-2 minutos)

## Paso 2: Obtener Credenciales

Una vez creado el proyecto:

1. Ve a **Project Settings** (ícono de engranaje en la barra lateral)
2. Selecciona **API** en el menú
3. Copia los siguientes valores:

   - **Project URL**: `https://tuproyecto.supabase.co`
   - **anon public key**: Una clave larga que empieza con `eyJ...`

**IMPORTANTE**: Usa la `anon public` key (no la `service_role` key) para empezar. La `service_role` key se usa solo si necesitas permisos de administrador.

## Paso 3: Configurar Variables de Entorno

Edita el archivo `.env` en la raíz del proyecto:

```bash
# Supabase Configuration
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR1cHJveWVjdG8iLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYyMzg5MDAwMCwiZXhwIjoxOTM5NDY2MDAwfQ.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Reemplaza con tus valores reales.

## Paso 4: Crear el Schema de Base de Datos

1. En el dashboard de Supabase, ve a **SQL Editor** (ícono de base de datos en la barra lateral)
2. Haz clic en **+ New query**
3. Copia TODO el contenido del archivo `sql/supabase_schema.sql`
4. Pégalo en el editor
5. Haz clic en **Run** (o presiona Ctrl+Enter)

Deberías ver un mensaje de éxito: "Success. No rows returned"

## Paso 5: Verificar las Tablas

1. Ve a **Table Editor** en la barra lateral
2. Deberías ver dos tablas:
   - `news_item`: Para almacenar noticias
   - `execution_log`: Para registrar ejecuciones del pipeline

## Paso 6: Instalar Dependencias

```bash
pip install supabase
```

O si usas el `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Paso 7: Probar la Conexión

Ejecuta el script de prueba:

```bash
python scripts/test_supabase.py
```

Deberías ver:
```
✓ Supabase conectado correctamente
✓ Base de datos inicializada
```

## Configuración de Seguridad (Opcional pero Recomendado)

### Row Level Security (RLS)

El schema ya incluye políticas de seguridad:

- **Lectura pública**: Cualquiera puede leer las noticias (útil para APIs públicas)
- **Escritura restringida**: Solo el `service_role` puede insertar/actualizar

Si quieres **más seguridad**:

1. Ve a **Authentication** → **Policies** en Supabase
2. Modifica las políticas según tus necesidades
3. Para escritura privada, usa la `service_role` key en `.env`

### Configurar para Producción

Si vas a usar en producción:

1. **Usa service_role key** para el ETL pipeline:
   ```bash
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.service_role_key_here...
   ```

2. **Crea una API key de solo lectura** para consumidores externos:
   - Usa la `anon public` key
   - Configura RLS para permitir solo SELECT

## Uso en el Pipeline

El código del pipeline ya está actualizado para usar Supabase. Solo necesitas:

1. Configurar las variables de entorno (Paso 3)
2. Ejecutar el pipeline normalmente:

```bash
python src/main.py
```

El pipeline automáticamente:
- Se conectará a Supabase
- Guardará las noticias en la nube
- Registrará cada ejecución

## Consultar Datos desde Supabase

### Desde el Dashboard

1. Ve a **Table Editor**
2. Selecciona `news_item`
3. Puedes filtrar, ordenar y exportar datos

### Desde la API REST

Supabase genera automáticamente una API REST:

```bash
# Obtener todas las noticias
curl "https://tuproyecto.supabase.co/rest/v1/news_item?select=*" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY"

# Obtener noticias de alta severidad
curl "https://tuproyecto.supabase.co/rest/v1/news_item?severity=eq.high&select=*" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY"

# Buscar noticias por texto
curl "https://tuproyecto.supabase.co/rest/v1/news_item?title=ilike.*metro*&select=*" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY"
```

### Desde Python

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Obtener últimas 10 noticias
response = supabase.table('news_item').select('*').limit(10).execute()
print(response.data)

# Filtrar por severidad
response = supabase.table('news_item').select('*').eq('severity', 'high').execute()
print(response.data)
```

### Desde JavaScript/Web

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Obtener noticias
const { data, error } = await supabase
  .from('news_item')
  .select('*')
  .order('published_at', { ascending: false })
  .limit(10)

console.log(data)
```

## Migrar Datos Existentes (Opcional)

Si ya tienes datos en SQLite y quieres migrarlos a Supabase:

```bash
python scripts/migrate_sqlite_to_supabase.py
```

Este script:
1. Lee todos los datos de `data/etl_movilidad.db`
2. Los inserta en Supabase
3. Muestra un resumen de la migración

## Monitoreo y Límites

### Plan Gratuito Incluye:
- 500 MB de base de datos PostgreSQL
- 1 GB de almacenamiento de archivos
- 2 GB de ancho de banda
- 50,000 usuarios activos mensuales
- Row Level Security
- Backups automáticos (7 días de retención)

### Verificar Uso:
1. Ve a **Project Settings** → **Usage**
2. Revisa el uso de base de datos y ancho de banda

### Alertas:
Configura alertas en **Project Settings** → **Notifications** para recibir avisos cuando te acerques a los límites.

## Solución de Problemas

### Error: "relation 'news_item' does not exist"
**Solución**: Ejecuta el schema SQL (Paso 4)

### Error: "Invalid API key"
**Solución**: Verifica que `SUPABASE_KEY` en `.env` sea correcto

### Error: "Row Level Security policy violation"
**Solución**: Usa la `service_role` key para operaciones de escritura, o ajusta las políticas RLS

### Las consultas son lentas
**Solución**: Los índices ya están creados en el schema. Si tienes muchos datos (>10,000 filas), considera añadir más índices.

## Recursos Adicionales

- [Documentación de Supabase](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [API Reference](https://supabase.com/docs/reference/python/introduction)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

## Soporte

Si tienes problemas:
1. Revisa los logs en Supabase: **Logs** → **API Logs**
2. Consulta la documentación oficial
3. Pregunta en el [Discord de Supabase](https://discord.supabase.com)
