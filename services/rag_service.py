import os
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account

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
    """Busca un archivo específico (programas, cronogramas, plan) y devuelve su botón HTML."""
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
    """Maneja la entrega de archivos oficiales y base de conocimiento institucional."""
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

    # --- 2. BASE DE CONOCIMIENTO INSTITUCIONAL (Respuestas limpias y directas) ---
    base_conocimiento = {
        "curso de ingreso": "El curso de ingreso y ambientación es un espacio obligatorio de carácter sincrónico y asincrónico diseñado para que los ingresantes conozcan las herramientas digitales del campus, los cronogramas de cursada y las pautas generales de la tecnicatura a distancia.",
        "familiarización": "El curso de ingreso y ambientación es un espacio obligatorio de carácter sincrónico y asincrónico diseñado para que los ingresantes conozcan las herramientas digitales del campus, los cronogramas de cursada y las pautas generales de la tecnicatura a distancia.",
        "campus": "En la plataforma Moodle encontrarás el aula principal asignada a tu comisión. Cada semana se habilitan los módulos correspondientes con materiales de lectura obligatoria, foros de intercambio académico y actividades evaluables.",
        "moodle": "En la plataforma Moodle encontrarás el aula principal asignada a tu comisión. Cada semana se habilitan los módulos correspondientes con materiales de lectura obligatoria, foros de intercambio académico y actividades evaluables.",
        "materiales": "Disponés de guías de lectura rápida, tutoriales de acceso y el programa introductorio en la sección del 'Curso de Familiarización y Primeros Pasos' dentro de tu aula virtual.",
        "docentes": "Podés establecer contacto con el equipo docente a través de la mensajería interna del campus Moodle o utilizando los foros de consultas generales habilitados en cada materia.",
        "comisión": "Para conocer tu comisión, ingresá a la sección de tu perfil en el campus Moodle o consultá el padrón oficial de ingresantes publicado en la cartelera digital institucional.",
        "asistencia": "La tecnicatura a distancia exige un mínimo del 75% de participación y asistencia a las actividades sincrónicas obligatorias y la aprobación de las entregas de trabajos prácticos.",
        "faltas": "Las inasistencias a instancias obligatorias deben justificarse formalmente presentando certificado médico o laboral ante Bedelía dentro de las 48 horas hábiles posteriores al hecho.",
        "actividades pendientes": "Las entregas fuera de término deben coordinarse directamente con el docente a cargo de la comisión y están sujetas al régimen de evaluación y plazos establecidos en la materia.",
        "alumno regular": "Se mantiene cumpliendo con el porcentaje mínimo de asistencia, aprobando los trabajos prácticos obligatorios y rindiendo las instancias parciales o coloquios en las fechas del calendario académico.",
        "correlatividades": "Para cursar las asignaturas de segundo año es requisito obligatorio haber regularizado las correlativas de primer año; y para rendir los exámenes finales, se debe tener la materia aprobada según el plan de estudios vigente.",
        "certificado": "El certificado se solicita de manera digital ingresando a la plataforma SIU Guaraní en la sección 'Trámites > Certificados', el cual se emite automáticamente con firma digital válida.",
        "inscripción": "Todas las inscripciones a materias, promociones y mesas de exámenes finales se gestionan exclusivamente a través del sistema SIU Guaraní dentro de los plazos del calendario académico.",
        "datos personales": "La modificación de datos de contacto se realiza ingresando a la configuración de tu perfil en SIU Guaraní o enviando una solicitud formal al área de Bedelía.",
        "calendario": "El cronograma completo con fechas de inicio de cuatrimestre, periodos de inscripción, recesos y mesas de exámenes está publicado en la sección de normativas de la web institucional.",
        "requisitos": "Se recomienda contar con una computadora (PC o notebook) con sistema operativo actualizado, navegador web moderno y una conexión a internet estable. Para las prácticas de programación se indicarán los entornos específicos en cada materia.",
        "problemas de conexión": "Si experimentás inconvenientes técnicos durante una evaluación sincrónica, debés tomar una captura de pantalla como evidencia (con fecha y hora) y reportarlo de inmediato a soporte técnico y a tu docente por correo.",
        "diferencia": "Las consultas académicas (contenidos, bibliografía, notas) se resuelven con profesores o tutores. Las cuestiones administrativas (certificados, pases, analíticos, SIU Guaraní) se canalizan exclusivamente con Bedelía."
    }

    # Buscamos coincidencias directas en las palabras clave
    for clave, respuesta in base_conocimiento.items():
        if clave in p_lower:
            return respuesta, False

    # --- 3. DERIVACIÓN FINAL SI NO SE ENCUENTRA NADA ---
    return "No encontré una respuesta exacta en los documentos institucionales. ¿Deseas contactar a Bedelía o Tutoría?", True