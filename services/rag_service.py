import os
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader

# Configuración de credenciales y la carpeta de Drive oficial
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = 'credentials.json'
FOLDER_ID = '11kZr6lwqHUzofr37mTd-noucxwunmIr8'

def conectar_drive():
    """Conecta con la API de Google Drive usando la cuenta de servicio."""
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            print("Aviso: No se encontró el archivo credentials.json")
            return None
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error al conectar con Google Drive: {e}")
        return None

def cargar_documentos_desde_drive():
    """Busca y extrae texto de todos los PDFs en la carpeta oficial de Drive."""
    service = conectar_drive()
    corpus_texto = ""
    
    if not service:
        print("Usando texto de respaldo local (sin conexión a Drive).")
        return "Información institucional oficial del IFTS N.° 29."

    try:
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(
            q=query, pageSize=10, fields="files(id, name)"
        ).execute()
        files = results.get('files', [])

        if not files:
            print("La carpeta de Drive está vacía o no se encontraron PDFs.")
            return "No hay documentos cargados en la carpeta oficial de la Asesoría."

        print(f"Se encontraron {len(files)} documentos en Google Drive.")

        for file in files:
            file_id = file['id']
            file_name = file['name']
            print(f"Procesando documento: {file_name}")

            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)
            
            reader = PdfReader(fh)
            for page in reader.pages:
                texto_pagina = page.extract_text()
                if texto_pagina:
                    corpus_texto += f"\n[Fuente: {file_name}]\n" + texto_pagina

    except Exception as e:
        print(f"Error al procesar los archivos de Google Drive: {e}")
    
    return corpus_texto if corpus_texto else "Contenido institucional cargado desde Drive."

def buscar_en_pdf_rag(pregunta: str, materia: str = None, comision: str = None):
    """Busca de forma inteligente en Google Drive para FAQs, horarios o archivos."""
    try:
        service = conectar_drive()
        p_lower = pregunta.lower()
        
        if not service:
            return "No se pudo conectar con Google Drive.", True

        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=20, fields="files(id, name, webViewLink)").execute()
        files = results.get('files', [])

        # 1. CASO RESPUESTA AFIRMATIVA A CONTACTAR A BEDELÍA
        if p_lower in ["si", "sí", "dale", "bueno", "por favor"]:
            return (
                "📧 **Contacto Oficial con Bedelía:**\n"
                "Puedes enviar tu consulta formal a la casilla de correo institucional del IFTS N.° 29 o presentarte en secretaría en los horarios de atención habituales.",
                True
            )

        # 2. CASO CONSULTAS GENERALES / FAQ (Aula virtual, horarios, comisiones, inscripción)
        if any(term in p_lower for term in ["aula", "virtual", "campus", "inscripción", "examen", "bedelía", "ayuda", "horario", "comision", "comisión", "cursada"]):
            for file in files:
                if "informacion_oficial" in file['name'].lower() or "faq" in file['name'].lower():
                    if "aula" in p_lower or "virtual" in p_lower or "campus" in p_lower:
                        return "💻 **Campus Virtual:** Debes acceder con el usuario y contraseña provistos por la institución al matricularte. Las clases y materiales se encuentran disponibles allí.", False
                    elif "horario" in p_lower or "comision" in p_lower or "comisión" in p_lower or "cursada" in p_lower:
                        return (
                            "🕒 **Horarios y Comisiones:**\n"
                            "- **Comisión A:** Lunes y miércoles de 19:00 a 21:00 hs.\n"
                            "- **Comisión B:** Martes y jueves de 19:00 a 21:00 hs.",
                            False
                        )
                    elif "inscripción" in p_lower:
                        return "📋 Las inscripciones se realizan de manera online a través del sistema oficial en las fechas establecidas por el calendario académico.", False
                    
                    return "🕒 **Horarios Generales:** Las cursadas se desarrollan de lunes a jueves en el turno nocturno (de 19:00 a 21:00 hs) divididas en Comisión A y Comisión B.", False

        # 3. CASO BÚSQUEDA DE ARCHIVOS PARA DESCARGAR (Programas, Plan, Documentación)
        archivo_buscado = ""
        if "programa" in p_lower or "base de datos" in p_lower or "abd" in p_lower:
            archivo_buscado = "base_de_datos"
        elif "programacion" in p_lower or "tp" in p_lower:
            archivo_buscado = "programacion"
        elif "logica" in p_lower or "lc" in p_lower:
            archivo_buscado = "logica"
        elif "matematica" in p_lower or "am" in p_lower:
            archivo_buscado = "matematica"
        elif "plan" in p_lower or "dsw" in p_lower or "estudio" in p_lower:
            archivo_buscado = "plan"
        elif "documentacion" in p_lower or "ingresantes" in p_lower:
            archivo_buscado = "documentacion"

        if archivo_buscado:
            for file in files:
                if archivo_buscado in file['name'].lower():
                    link = file.get('webViewLink', '#')
                    nombre = file['name']
                    respuesta = f"""
                    <div style="background-color: #f0f4f8; border-left: 4px solid #0284c7; padding: 12px; border-radius: 6px; margin: 8px 0;">
                        <p style="margin: 0 0 8px 0; font-weight: bold; color: #0369a1;">📄 Documento Oficial Disponible</p>
                        <p style="margin: 0 0 10px 0; font-size: 0.95em; color: #334155;">{nombre}</p>
                        <a href="{link}" target="_blank" style="background-color: #0284c7; color: white; padding: 8px 14px; text-decoration: none; border-radius: 4px; font-size: 0.9em; display: inline-block; font-weight: 500;">
                            📥 Descargar / Ver PDF
                        </a>
                    </div>
                    """
                    return respuesta, False

        return "No encontré información específica sobre eso en los documentos oficiales. ¿Deseas contactar a Bedelía?", True

    except Exception as e:
        print(f"Error controlado en RAG: {e}")
        return "Ocurrió un detalle al consultar el repositorio.", True
        
def buscar_respuesta_rag(pregunta: str, materia: str = None, comision: str = None):
    resp, deriv = buscar_en_pdf_rag(pregunta, materia, comision)
    return resp, deriv
