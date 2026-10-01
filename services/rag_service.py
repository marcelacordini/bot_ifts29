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
    """Conecta con la API de Google Drive."""
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
    """Busca un archivo específico en Drive y devuelve su botón HTML."""
    service = conectar_drive()
    if not service:
        return "No se pudo conectar con Google Drive para recuperar el documento."
    
    try:
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=50, fields="files(id, name, webViewLink)").execute()
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
        return f"No se encontró el documento oficial ({nombre_buscado}) en la carpeta de Drive."
    except Exception as e:
        return f"Error al buscar el archivo: {e}"

def buscar_en_pdf_rag(pregunta: str):
    """Gestiona la entrega de archivos oficiales y la búsqueda limpia por RAG."""
    p_lower = pregunta.lower()

    # --- 1. DETECCIÓN DE MATERIAS Y DOCUMENTOS ESPECÍFICOS (Códigos 111 a 114) ---
    codigos_materias = {
        "técnicas de programación": "111", "programacion": "111",
        "administración de base de datos": "112", "base de datos": "112",
        "elementos de análisis matemático": "113", "matemático": "113",
        "lógica computacional": "114", "lógica": "114"
    }

    codigo_detectado = None
    for nombre_mat, codigo in codigos_materias.items():
        if nombre_mat in p_lower:
            codigo_detectado = codigo
            break

    if codigo_detectado:
        if "programa" in p_lower:
            return obtener_link_archivo_drive(f"{codigo_detectado}_Programa"), False
        if "cronograma" in p_lower or "horarios" in p_lower or "días" in p_lower:
            return obtener_link_archivo_drive(f"{codigo_detectado}_Cronograma"), False

    # Plan de estudios y carrera
    if "plan de estudios" in p_lower or "ver el plan" in p_lower or "duración" in p_lower or "validez" in p_lower:
        return obtener_link_archivo_drive("plan"), False

    # --- 2. BÚSQUEDA RAG LIMPIA EN ARCHIVOS DE DRIVE ---
    service = conectar_drive()
    if not service:
        return "No se pudo conectar con el repositorio documental. ¿Deseas contactar a Bedelía o Tutoría?", True

    try:
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=30, fields="files(id, name)").execute()
        files = results.get('files', [])

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
                    lineas = txt.split('\n')
                    for i, linea in enumerate(lineas):
                        # Si encuentra una coincidencia relevante con la pregunta ingresada
                        if any(p in linea.lower() for p in p_lower.split() if len(p) > 3):
                            # Tomamos exclusivamente el bloque de texto limpio de la respuesta
                            bloque_respuesta = " ".join([l.strip() for l in lineas[max(0, i):min(len(lineas), i+3)] if l.strip()])
                            if len(bloque_respuesta) > 20:
                                return f"📖 {bloque_respuesta}", False

        # --- 3. DERIVACIÓN FINAL SI NO SE ENCUENTRA NADA ---
        return "No encontré una respuesta exacta en los documentos institucionales. ¿Deseas contactar a Bedelía o Tutoría?", True

    except Exception as e:
        print(f"Error en RAG: {e}")
        return "Ocurrió un inconveniente al procesar los archivos institucionales. ¿Deseas contactar a Bedelía o Tutoría?", True