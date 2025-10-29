"""
Script de Verificación Completa del Sistema ADK
Verifica que todo esté configurado correctamente antes de ejecutar
"""
import sys
import os
import subprocess

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_section(title):
    """Imprime una sección visual"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def check_command(command, description):
    """Verifica que un comando existe"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return True, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_python_version():
    """Verifica la versión de Python"""
    print("\n[1/8] Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"    ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"    ❌ Python {version.major}.{version.minor}.{version.micro} (Se requiere 3.11+)")
        return False

def check_directory():
    """Verifica que estamos en el directorio correcto"""
    print("\n[2/8] Verificando directorio del proyecto...")
    current_dir = os.getcwd()
    if 'etl-movilidad-local' in current_dir:
        print(f"    ✅ Directorio correcto: {current_dir}")
        return True
    else:
        print(f"    ❌ Directorio incorrecto: {current_dir}")
        print("    💡 Navega a: etl-movilidad-local/")
        return False

def check_env_file():
    """Verifica que existe el archivo .env"""
    print("\n[3/8] Verificando archivo .env...")
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        print("    ✅ Archivo .env existe")

        # Leer y verificar contenido
        with open(env_path, 'r') as f:
            content = f.read()

        has_project = 'GOOGLE_CLOUD_PROJECT=' in content
        has_vertexai = 'GOOGLE_GENAI_USE_VERTEXAI=true' in content
        has_location = 'GOOGLE_CLOUD_LOCATION=' in content

        if has_project:
            # Extraer project ID
            for line in content.split('\n'):
                if line.startswith('GOOGLE_CLOUD_PROJECT='):
                    project_id = line.split('=')[1].strip()
                    print(f"    ✅ GOOGLE_CLOUD_PROJECT: {project_id}")
        else:
            print("    ❌ Falta GOOGLE_CLOUD_PROJECT")

        if has_vertexai:
            print("    ✅ GOOGLE_GENAI_USE_VERTEXAI configurado")
        else:
            print("    ⚠️  Falta GOOGLE_GENAI_USE_VERTEXAI=true")

        if has_location:
            print("    ✅ GOOGLE_CLOUD_LOCATION configurado")
        else:
            print("    ⚠️  Falta GOOGLE_CLOUD_LOCATION")

        return has_project
    else:
        print("    ❌ Archivo .env no existe")
        print("    💡 Crea el archivo .env desde .env.example")
        return False

def check_gcloud_auth():
    """Verifica autenticación de gcloud"""
    print("\n[4/8] Verificando autenticación de Google Cloud...")
    success, output = check_command(
        'gcloud auth application-default print-access-token',
        'Google Cloud Auth'
    )

    if success and output.startswith('ya29.'):
        print("    ✅ Autenticado correctamente")
        print(f"    🔑 Token: {output[:50]}...")
        return True
    else:
        print("    ❌ No autenticado")
        print("    💡 Ejecuta: gcloud auth application-default login")
        return False

def check_package(package_name):
    """Verifica que un paquete Python está instalado"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Extraer versión
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':')[1].strip()
                    return True, version
        return False, None
    except Exception as e:
        return False, None

def check_dependencies():
    """Verifica dependencias Python"""
    print("\n[5/8] Verificando dependencias de Python...")

    packages = [
        ('google-adk', '0.2.0'),
        ('pydantic', '2.0.0'),
        ('google-genai', None),
        ('python-dotenv', None)
    ]

    all_ok = True
    for package, min_version in packages:
        installed, version = check_package(package)
        if installed:
            print(f"    ✅ {package} v{version}")
        else:
            print(f"    ❌ {package} no instalado")
            all_ok = False

    if not all_ok:
        print("\n    💡 Instala dependencias: pip install --user -r requirements.txt")

    return all_ok

def check_source_files():
    """Verifica que existen los archivos fuente necesarios"""
    print("\n[6/8] Verificando archivos fuente...")

    files_to_check = [
        'src/adk_scorer_v3.py',
        'src/schemas/scoring_schema.py',
        'src/prompts/system_prompt.py',
        'scripts/test_gemini_v3.py',
        'scripts/generate_test_news.py'
    ]

    all_ok = True
    for file_path in files_to_check:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            print(f"    ✅ {file_path}")
        else:
            print(f"    ❌ {file_path} no encontrado")
            all_ok = False

    return all_ok

def check_vertex_ai_api():
    """Verifica que Vertex AI API está habilitada"""
    print("\n[7/8] Verificando Vertex AI API...")

    # Obtener project ID del .env
    env_path = os.path.join(os.getcwd(), '.env')
    project_id = None

    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_CLOUD_PROJECT='):
                    project_id = line.split('=')[1].strip()
                    break

    if not project_id:
        print("    ⚠️  No se pudo determinar el project ID")
        return False

    # Verificar si la API está habilitada
    success, output = check_command(
        f'gcloud services list --enabled --project={project_id} --filter="aiplatform.googleapis.com" --format="value(name)"',
        'Vertex AI API'
    )

    if success and 'aiplatform.googleapis.com' in output:
        print("    ✅ Vertex AI API habilitada")
        return True
    else:
        print("    ❌ Vertex AI API no habilitada")
        print(f"    💡 Habilita con: gcloud services enable aiplatform.googleapis.com --project={project_id}")
        return False

def test_import():
    """Intenta importar el módulo principal"""
    print("\n[8/8] Probando importación del módulo...")

    try:
        # Agregar src al path
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

        from adk_scorer_v3 import ADKScorerV3
        print("    ✅ ADKScorerV3 se puede importar correctamente")

        from schemas.scoring_schema import ScoringResponse
        print("    ✅ ScoringResponse se puede importar correctamente")

        return True
    except ImportError as e:
        print(f"    ❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

def main():
    """Función principal de verificación"""
    print_section("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA GOOGLE ADK")

    results = []

    # Ejecutar todas las verificaciones
    results.append(('Python 3.11+', check_python_version()))
    results.append(('Directorio correcto', check_directory()))
    results.append(('Archivo .env', check_env_file()))
    results.append(('Google Cloud Auth', check_gcloud_auth()))
    results.append(('Dependencias Python', check_dependencies()))
    results.append(('Archivos fuente', check_source_files()))
    results.append(('Vertex AI API', check_vertex_ai_api()))
    results.append(('Importación de módulos', test_import()))

    # Resumen
    print_section("📊 RESUMEN DE VERIFICACIÓN")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅" if result else "❌"
        print(f"    {status} {check_name}")

    print(f"\n    Total: {passed}/{total} verificaciones pasadas")

    # Conclusión
    print_section("🎯 CONCLUSIÓN")

    if passed == total:
        print("\n    ✅ ¡SISTEMA COMPLETAMENTE CONFIGURADO!")
        print("\n    🚀 Puedes ejecutar el test:")
        print("       python scripts/test_gemini_v3.py")
    else:
        print("\n    ⚠️  CONFIGURACIÓN INCOMPLETA")
        print(f"\n    Faltan {total - passed} verificaciones por completar.")
        print("\n    📖 Consulta GUIA_COMPLETA_ADK.md para instrucciones detalladas")

    print("\n" + "="*70 + "\n")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
