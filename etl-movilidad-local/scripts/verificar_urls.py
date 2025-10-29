"""
Verificar URLs de las fuentes de noticias
Muestra qué URLs están configuradas y si funcionan
"""
import sys
import os
import io
import requests

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def check_url(url: str, name: str) -> bool:
    """
    Check if a URL is accessible

    Args:
        url: URL to check
        name: Name of the source

    Returns:
        True if accessible, False otherwise
    """
    try:
        print(f"\n🔍 Verificando: {name}")
        print(f"   URL: {url}")

        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            print(f"   ✅ FUNCIONA - HTTP {response.status_code}")
            print(f"   Tamaño: {len(response.content)} bytes")
            return True
        else:
            print(f"   ❌ ERROR - HTTP {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT - La página tardó demasiado en responder")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ ERROR DE CONEXIÓN - No se puede conectar")
        return False
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False


def main():
    """Main verification function"""
    print("="*70)
    print("  VERIFICACIÓN DE URLs DE FUENTES")
    print("="*70)

    # URLs configuradas actualmente en extractors_apify_simple.py
    sources = [
        {
            "name": "Metro de Medellín",
            "url": "https://www.metrodemedellin.gov.co/al-dia/noticias",
            "status": "ACTIVA"
        },
        {
            "name": "Alcaldía de Medellín",
            "url": "https://www.medellin.gov.co/es/sala-de-prensa/noticias/",
            "status": "ACTIVA"
        },
    ]

    # URLs adicionales sugeridas (no configuradas)
    suggested_sources = [
        {
            "name": "AMVA (Área Metropolitana)",
            "url": "https://www.metropol.gov.co/Paginas/Noticias.aspx",
            "status": "SUGERIDA"
        },
        {
            "name": "El Colombiano - Movilidad",
            "url": "https://www.elcolombiano.com/antioquia/movilidad",
            "status": "SUGERIDA"
        },
        {
            "name": "Minuto30 - Medellín",
            "url": "https://www.minuto30.com/categoria/medellin/",
            "status": "SUGERIDA"
        }
    ]

    print("\n📋 FUENTES ACTIVAS EN EL SISTEMA:")
    print("-" * 70)

    active_results = []
    for source in sources:
        result = check_url(source['url'], source['name'])
        active_results.append((source['name'], result))

    print("\n" + "="*70)
    print("📋 FUENTES SUGERIDAS (NO CONFIGURADAS):")
    print("-" * 70)

    suggested_results = []
    for source in suggested_sources:
        result = check_url(source['url'], source['name'])
        suggested_results.append((source['name'], result))

    # Summary
    print("\n" + "="*70)
    print("  RESUMEN")
    print("="*70)

    print("\n✅ Fuentes Activas:")
    for name, status in active_results:
        icon = "✅" if status else "❌"
        print(f"   {icon} {name}")

    print("\n💡 Fuentes Sugeridas (para agregar):")
    for name, status in suggested_results:
        icon = "✅" if status else "❌"
        estado = "Disponible" if status else "No disponible"
        print(f"   {icon} {name} - {estado}")

    # Instructions
    print("\n" + "="*70)
    print("  📝 CÓMO AGREGAR O MODIFICAR FUENTES")
    print("="*70)
    print("\n1. Editar el archivo:")
    print("   src/extractors_apify_simple.py")
    print("\n2. Buscar la sección 'sources = [' (línea ~37)")
    print("\n3. Agregar una nueva fuente:")
    print("""
    {
        "name": "Nombre de la Fuente",
        "url": "https://ejemplo.com/noticias",
        "selectors": {
            "article": "article, .noticia",
            "title": "h2, h3",
            "link": "a",
            "summary": "p",
            "date": "time, .date"
        }
    },
    """)
    print("\n4. Guardar y ejecutar:")
    print("   python scripts/test_apify_simple.py")

    print("\n" + "="*70)

    # Statistics
    active_working = sum(1 for _, status in active_results if status)
    suggested_working = sum(1 for _, status in suggested_results if status)

    print(f"\n📊 Estadísticas:")
    print(f"   Fuentes activas funcionando: {active_working}/{len(active_results)}")
    print(f"   Fuentes sugeridas disponibles: {suggested_working}/{len(suggested_results)}")

    if active_working == len(active_results):
        print("\n✅ ¡Todas las fuentes activas están funcionando!")
    else:
        print("\n⚠️  Algunas fuentes activas tienen problemas")

    print("\n")


if __name__ == "__main__":
    main()
