import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://owdpwpuswoslesqidhqt.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93ZHB3cHVzd29zbGVzcWlkaHF0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA1NDkxNDAsImV4cCI6MjEwNjEyNTE0MH0.xaORDKxrHK8L0mAD-TWmA9GCrIHtnSQr0KgIhKVQ_Bs")

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Aviso: No se pudo conectar a Supabase: {e}")

def registrar_consulta_anonima(texto_sanitizado: str, resultado: str, confianza: float = 0.0):
    """
    Registra de forma anónima las consultas procesadas para las métricas institucionales (RF09).
    """
    if not supabase:
        return  # Modo local sin conexión activa a base de datos

    try:
        data = {
            "texto_sanitizado": texto_sanitizado,
            "resultado": resultado,
            "confianza": confianza
        }
        supabase.table("consulta").insert(data).execute()
    except Exception as e:
        print(f"Error al guardar métrica en Supabase: {e}")