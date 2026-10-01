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

def buscar_en_pdf_oficial(pregunta: str):
    """Busca específicamente dentro de Informacion_Oficial_IFTS29.pdf usando RAG."""
    service = conectar_drive()
    if not service:
        return None

    try:
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=40, fields="files(id, name, webViewLink)").execute()
        files = results.get('files', [])

        archivo_objetivo = None
        for file in files:
            if "informacion_oficial" in file['name'].lower() or "ifts29" in file['name'].lower():
                archivo_objetivo = file
                break

        if not archivo_objetivo:
            return None

        # Descargar y leer el PDF oficial
        request = service.files().get_media(fileId=archivo_objetivo['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)

        reader = PdfReader(fh)
        p_lower = pregunta.lower()
        palabras_clave = [p for p in p_lower.split() if len(p) > 3]

        for page in reader.pages:
            texto = page.extract_text()
            if texto:
                texto_lower = texto.lower()
                # Coincidencia si contiene palabras clave importantes de la pregunta manual
                if any(palabra in texto_lower for palabra in palabras_clave):
                    # Extraer un fragmento relevante alrededor de la coincidencia
                    return f"📖 **Información encontrada en el documento oficial:**\n\n<em>{texto[:400]}...</em>", False

        return None
    except Exception as e:
        print(f"Error buscando en PDF oficial: {e}")
        return None

def obtener_link_archivo_drive(nombre_buscado: str):
    """Busca un archivo específico (programas, cronogramas, plan) y devuelve su botón HTML."""
    service = conectar_drive()
    if not service:
        return "No se pudo conectar con Google Drive para recuperar el documento."
    
    try:
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=40, fields="files(id, name, webViewLink)").execute()
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