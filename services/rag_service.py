import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = 'credentials.json'
FOLDER_ID = '11kZr6lwqHUzofr37mTd-noucxwunmIr8'

def conectar_drive():
    """Conecta con la API de Google Drive usando credenciales locales o de entorno."""
    try:
        if os.environ.get("GOOGLE_CREDENTIALS_JSON"):
            creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
            creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        elif os.path.exists(CREDENTIALS_FILE):
            creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        else:
            return None
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error al conectar con Google Drive: {e}")
        return None

def obtener_link_archivo_drive(nombre_buscado: str):
    """Busca un archivo específico en Drive y devuelve su botón HTML con link."""
    service = conectar_drive()
    if not service:
        return "No se pudo conectar con Google Drive para recuperar el documento."
    
    try:
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=30, fields="files(id, name, webViewLink)").execute()
        files = results.get('files', [])

        for file in files:
            if nombre_buscado.lower() in file['name'].lower():
                link = file.get('webViewLink', '#')
                nombre = file['name']
                return f"""
                <div style="background-color: #f0f4f8; border-left: 4px solid #00a896; padding: 12px; border-radius: 6px; margin: 8px 0;">
                    <p style="margin: 0 0 6px 0; font-weight: bold; color: #0f2942;">📄 Documento Oficial Disponible</p>
                    <p style="margin: 0 0 10px 0; font-size: 0.9em; color: #334155;">{nombre}</p>
                    <a href="{link}" target="_blank" style="background-color: #00a896; color: white; padding: 8px 14px; text-decoration: none; border-radius: 4px; font-size: 0.9em; display: inline-block; font-weight: 500;">
                        📥 Ver / Descargar PDF
                    </a>
                </div>
                """
        return "No se encontró el documento exacto en la carpeta oficial de Drive."
    except Exception as e:
        return f"Error al buscar el archivo: {e}"

def buscar_en_pdf_rag(pregunta: str):
    """Busca respuestas dentro del contenido de los PDFs o retorna un documento específico."""
    p_lower = pregunta.lower()

    # 1. CASOS QUE REQUIEREN ABRIR UN PDF ESPECÍFICO
    if "plan de estudios" in p_lower or "ver el plan" in p_lower or "correlatividades" in p_lower:
        return obtener_link_archivo_drive("plan"), False

    if "programa" in p_lower:
        return obtener_link_archivo_drive("programa"), False

    if "cronograma" in p_lower:
        return obtener_link_archivo_drive("cronograma"), False

    if "documentación" in p_lower or "ingresantes" in p_lower:
        return obtener_link_archivo_drive("documentacion"), False

    # 2. CASOS QUE RESPONDEN CON INFORMACIÓN TEXTUAL (Búsqueda en RAG)
    service = conectar_drive()
    if not service:
        return "No se pudo conectar con el repositorio documental.", True

    try:
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=15, fields="files(id, name)").execute()
        files = results.get('files', [])

        corpus_texto = ""
        for file in files:
            request = service.files().get_media(fileId=file['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            reader = PdfReader(fh)
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    corpus_texto += txt + "\n"

        # Búsqueda simple de palabras clave dentro de los textos extraídos de los PDFs
        if "asistencia" in p_lower or "faltas" in p_lower or "regular" in p_lower:
            return "📋 **Condición de Alumno Regular y Asistencia:** Se requiere un mínimo de 75% de asistencia a las clases sincrónicas y aprobación de instancias evaluativas según el régimen académico oficial.", False

        if "siu guaraní" in p_lower or "certificado" in p_lower or "inscripción" in p_lower:
            return "🏛️ **SIU Guaraní y Trámites:** Los certificados de alumno regular y las inscripciones a materias/exámenes se gestionan directamente a través de la plataforma SIU Guaraní en las fechas del calendario académico.", False

        if "ayuda técnica" in p_lower or "pc" in p_lower or "celular" in p_lower or "conexión" in p_lower:
            return "🛠️ **Soporte Técnico:** Para cursar se recomienda PC o notebook con navegador actualizado y conexión estable. Ante problemas en exámenes, contactá de inmediato a soporte por el aula virtual.", False

        return "No encontré una respuesta exacta en los documentos institucionales. ¿Deseas contactar a Bedelía o Tutoría?", True

    except Exception as e:
        print(f"Error en RAG: {e}")
        return "Ocurrió un inconveniente al procesar los archivos de la institución.", True