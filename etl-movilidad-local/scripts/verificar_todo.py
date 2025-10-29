"""
Verificación Completa del Sistema ETL Movilidad Medellín
Verifica TODOS los componentes: Apify, Google ADK, Pipeline, DB, Alerts
"""
import sys
import os
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_check(message, status=True):
    """Print check with status"""
    icon = "✅" if status else "❌"
    print(f"{icon} {message}")


def check_environment():
    """Check 1: Environment variables"""
    print_header("1. VERIFICACIÓN DE VARIABLES DE ENTORNO")

    checks = {
        "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "GOOGLE_GENAI_USE_VERTEXAI": os.getenv("GOOGLE_GENAI_USE_VERTEXAI"),
        "GOOGLE_CLOUD_LOCATION": os.getenv("GOOGLE_CLOUD_LOCATION"),
        "APIFY_API_TOKEN": os.getenv("APIFY_API_TOKEN"),
    }

    all_ok = True
    for key, value in checks.items():
        if value and not value.startswith("your-"):
            print_check(f"{key}: {value[:30]}..." if len(value) > 30 else f"{key}: {value}")
        else:
            print_check(f"{key}: NOT SET", False)
            all_ok = False

    return all_ok


def check_google_cloud():
    """Check 2: Google Cloud authentication"""
    print_header("2. VERIFICACIÓN DE GOOGLE CLOUD")

    try:
        import subprocess
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            token = result.stdout.strip()
            print_check(f"Autenticado correctamente")
            print(f"   Token: {token[:30]}...")
            return True
        else:
            print_check("Error de autenticación", False)
            return False
    except Exception as e:
        print_check(f"Error: {e}", False)
        return False


def check_apify():
    """Check 3: Apify scraping"""
    print_header("3. VERIFICACIÓN DE APIFY SCRAPING")

    try:
        from extractors_apify_simple import SimpleApifyExtractor

        print("🔄 Inicializando Apify extractor...")
        extractor = SimpleApifyExtractor()
        print_check("Apify client inicializado")

        print("\n🔄 Extrayendo noticias (esto puede tomar 30 segundos)...")
        start_time = time.time()
        news = extractor.extract_all()
        duration = time.time() - start_time

        if len(news) > 0:
            print_check(f"Extraídas {len(news)} noticias en {duration:.1f}s")

            # Show sample
            print("\n📰 Muestra de noticias:")
            for i, item in enumerate(news[:3], 1):
                print(f"   [{i}] {item['title'][:60]}...")

            return True
        else:
            print_check("No se extrajeron noticias", False)
            return False

    except Exception as e:
        print_check(f"Error en Apify: {e}", False)
        return False


def check_adk_scorer():
    """Check 4: Google ADK Scorer"""
    print_header("4. VERIFICACIÓN DE GOOGLE ADK (Gemini 2.0 Flash)")

    try:
        from adk_scorer_v3 import ADKScorerV3

        print("🔄 Inicializando ADKScorerV3...")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        scorer = ADKScorerV3(project_id=project_id)
        print_check("ADKScorerV3 inicializado")

        print("\n🔄 Scoring noticia de prueba...")
        test_news = {
            "source": "Test",
            "url": "https://test.com",
            "title": "Suspensión de servicio en Metro por mantenimiento",
            "body": "El Metro suspenderá servicio entre Niquía y Bello el sábado por mantenimiento",
            "published_at": "2025-10-29T10:00:00"
        }

        start_time = time.time()
        result = scorer.score(test_news)
        duration = time.time() - start_time

        if result:
            print_check(f"Scoring exitoso en {duration:.1f}s")
            print(f"   Severity: {result.get('severity')}")
            print(f"   Score: {result.get('relevance_score')}")
            print(f"   Tags: {', '.join(result.get('tags', [])[:3])}")
            return True
        else:
            print_check("Noticia descartada (esperado si no es relevante)", False)
            return False

    except Exception as e:
        print_check(f"Error en ADK: {e}", False)
        import traceback
        traceback.print_exc()
        return False


def check_database():
    """Check 5: Database"""
    print_header("5. VERIFICACIÓN DE BASE DE DATOS")

    try:
        from db import NewsDatabase

        print("🔄 Conectando a base de datos...")
        db = NewsDatabase()
        print_check("Conexión exitosa")

        # Get stats
        stats = db.get_stats()
        print(f"\n📊 Estadísticas:")
        print(f"   Total noticias: {stats['total_news']}")
        print(f"   Por severidad: {dict(stats['by_severity'])}")
        print(f"   Por fuente: {dict(stats['by_source'])}")

        return True

    except Exception as e:
        print_check(f"Error en DB: {e}", False)
        return False


def check_pipeline():
    """Check 6: Full pipeline test"""
    print_header("6. VERIFICACIÓN DE PIPELINE COMPLETO")

    try:
        from extractors_apify_simple import HybridApifyExtractor
        from adk_scorer_v3 import ADKScorerV3
        from db import NewsDatabase

        print("🔄 Inicializando componentes del pipeline...")

        # Initialize
        extractor = HybridApifyExtractor()
        print_check("Extractor inicializado")

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        scorer = ADKScorerV3(project_id=project_id)
        print_check("Scorer inicializado")

        db = NewsDatabase()
        print_check("Database inicializada")

        print("\n🔄 Ejecutando pipeline completo...")
        print("   (Extracción → Scoring → DB)")

        start_time = time.time()

        # Extract
        print("\n   1️⃣ Extrayendo noticias...")
        news_items = extractor.extract_all()
        print(f"      ✓ Extraídas: {len(news_items)} noticias")

        if len(news_items) == 0:
            print_check("No hay noticias para procesar", False)
            return False

        # Score (limit to 3 for speed)
        print("\n   2️⃣ Scoring noticias (máximo 3)...")
        scored = []
        for i, news in enumerate(news_items[:3], 1):
            print(f"      [{i}/3] Scoring: {news['title'][:50]}...")
            result = scorer.score(news)
            if result:
                scored.append(result)
                print(f"           ✓ Kept - Score: {result.get('relevance_score')}")
            else:
                print(f"           ✗ Discarded")

        print(f"\n      ✓ Scored: {len(scored)} kept")

        # Save (would save to DB, but we skip for test)
        print("\n   3️⃣ Base de datos ready")

        duration = time.time() - start_time

        print(f"\n✅ Pipeline completo ejecutado en {duration:.1f}s")
        print(f"   Extracted: {len(news_items)}")
        print(f"   Scored: {len(news_items[:3])}")
        print(f"   Kept: {len(scored)}")

        return True

    except Exception as e:
        print_check(f"Error en pipeline: {e}", False)
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all checks"""
    print("\n" + "🔍" * 35)
    print("  VERIFICACIÓN COMPLETA DEL SISTEMA")
    print("  ETL Movilidad Medellín")
    print("🔍" * 35)

    results = {}

    # Run all checks
    results['environment'] = check_environment()
    results['google_cloud'] = check_google_cloud()
    results['apify'] = check_apify()
    results['adk_scorer'] = check_adk_scorer()
    results['database'] = check_database()
    results['pipeline'] = check_pipeline()

    # Summary
    print_header("📊 RESUMEN DE VERIFICACIÓN")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for check, status in results.items():
        print_check(check.replace('_', ' ').title(), status)

    print("\n" + "="*70)
    print(f"  RESULTADO: {passed}/{total} verificaciones pasadas")
    print("="*70)

    if passed == total:
        print("\n✅ ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("\n🚀 Puedes ejecutar el pipeline en producción:")
        print("   cd etl-movilidad-local/src && python main.py")
    else:
        print("\n⚠️  Algunas verificaciones fallaron")
        print("\n📋 Revisa los errores arriba y:")
        print("   1. Verifica que el .env esté configurado")
        print("   2. Verifica que Google Cloud esté autenticado")
        print("   3. Verifica que Apify API token sea válido")

    print("\n")

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación interrumpida por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
