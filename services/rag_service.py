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
    """Busca un archivo específico en Drive de forma flexible y devuelve su botón HTML."""
    service = conectar_drive()
    if not service:
        return "No se pudo conectar con Google Drive para recuperar el documento."
    
    try:
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=50, fields="files(id, name, webViewLink)").execute()
        files = results.get('files', [])

        partes_busqueda = nombre_buscado.lower().split("_")

        for file in files:
            nombre_archivo = file['name'].lower()
            if all(parte in nombre_archivo for parte in partes_busqueda):
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
    """Maneja la entrega de archivos oficiales y responde consultas escritas por teclado."""
    p_lower = pregunta.lower()

    # --- 1. DETECTAR PROGRAMAS Y CRONOGRAMAS ---
    codigo_detectado = None
    if "base de datos" in p_lower or "112" in p_lower or "administración" in p_lower:
        codigo_detectado = "112"
    elif "programación" in p_lower or "111" in p_lower or "técnicas" in p_lower:
        codigo_detectado = "111"
    elif "matemático" in p_lower or "113" in p_lower or "análisis" in p_lower:
        codigo_detectado = "113"
    elif "lógica" in p_lower or "114" in p_lower:
        codigo_detectado = "114"

    if "programa" in p_lower or "cronograma" in p_lower or "horarios" in p_lower or "días" in p_lower:
        tipo_doc = "Programa" if "programa" in p_lower else "Cronograma"
        if codigo_detectado:
            return obtener_link_archivo_drive(f"{codigo_detectado}_{tipo_doc}"), False

    # Plan de estudios y carrera
    if "plan de estudios" in p_lower or "ver el plan" in p_lower or "duración" in p_lower or "validez" in p_lower or "titulo" in p_lower:
        return obtener_link_archivo_drive("plan"), False

    # --- 2. BASE DE CONOCIMIENTO AMPLIADA (Cubre todos los temas y sinónimos) ---
    base_conocimiento = {
        # Materias y Plan
        "materia": "Las materias de primer año de la tecnicatura son: Administración de Base de Datos (1.1.2), Técnicas de Programación (1.1.1), Elementos de Análisis Matemático (1.1.3) y Lógica Computacional (1.1.4). Podés consultar el detalle completo desde la opción 'Plan de estudios y carrera'.",
        "materias": "Las materias de primer año de la tecnicatura son: Administración de Base de Datos (1.1.2), Técnicas de Programación (1.1.1), Elementos de Análisis Matemático (1.1.3) y Lógica Computacional (1.1.4). Podés consultar el detalle completo desde la opción 'Plan de estudios y carrera'.",
        "asignaturas": "Las materias de primer año de la tecnicatura son: Administración de Base de Datos (1.1.2), Técnicas de Programación (1.1.1), Elementos de Análisis Matemático (1.1.3) y Lógica Computacional (1.1.4). Podés consultar el detalle completo desde la opción 'Plan de estudios y carrera'.",
        "correlatividades": "Para cursar las asignaturas de segundo año es requisito obligatorio haber regularizado las correlativas de primer año; y para rendir los exámenes finales, se debe tener la materia aprobada según el plan de estudios vigente.",
        
        # Horarios y Cursada
        "horario": "Las actividades sincrónicas de primer año se desarrollan habitualmente de lunes a jueves en el turno noche (de 19:00 a 21:00 hs), según la comisión y materia asignada. Podés descargar el cronograma detallado desde el menú de tu cursada.",
        "horarios": "Las actividades sincrónicas de primer año se desarrollan habitualmente de lunes a jueves en el turno noche (de 19:00 a 21:00 hs), según la comisión y materia asignada. Podés descargar el cronograma detallado desde el menú de tu cursada.",
        "días": "Las actividades sincrónicas de primer año se desarrollan habitualmente de lunes a jueves en el turno noche (de 19:00 a 21:00 hs), según la comisión y materia asignada.",
        "clases": "Los enlaces de acceso a las clases en vivo y las grabaciones oficiales quedan alojados de manera permanente en la sección de avisos y clases sincrónicas de cada aula virtual en Moodle.",

        # Primeros pasos y Moodle
        "curso de ingreso": "El curso de ingreso y ambientación es un espacio obligatorio de carácter sincrónico y asincrónico diseñado para que los ingresantes conozcan las herramientas digitales del campus, los cronogramas de cursada y las pautas generales.",
        "familiarización": "El curso de ingreso y ambientación es un espacio obligatorio de carácter sincrónico y asincrónico diseñado para que los ingresantes conozcan las herramientas digitales del campus y los cronogramas de cursada.",
        "campus": "En la plataforma Moodle encontrarás el aula principal asignada a tu comisión. Cada semana se habilitan los módulos correspondientes con materiales de lectura obligatoria, foros de intercambio y actividades evaluables.",
        "moodle": "En la plataforma Moodle encontrarás el aula principal asignada a tu comisión. Cada semana se habilitan los módulos correspondientes con materiales de lectura obligatoria, foros de intercambio y actividades evaluables.",
        "materiales": "Disponés de guías de lectura rápida, tutoriales de acceso y el programa introductorio en la sección del 'Curso de Familiarización y Primeros Pasos' dentro de tu aula virtual.",
        "arrancar": "Disponés de guías de lectura rápida, tutoriales de acceso y el programa introductorio en la sección del 'Curso de Familiarización y Primeros Pasos' dentro de tu aula virtual.",
        
        # Docentes y Comisiones
        "docentes": "Podés establecer contacto con el equipo docente a través de la mensajería interna del campus Moodle o utilizando los foros de consultas generales habilitados en cada materia.",
        "profesores": "Podés establecer contacto con el equipo docente a través de la mensajería interna del campus Moodle o utilizando los foros de consultas generales habilitados en cada materia.",
        "comisión": "Para conocer tu comisión, ingresá a la sección de tu perfil en el campus Moodle o consultá el padrón oficial de ingresantes publicado en la cartelera digital institucional.",
        "comisiones": "Para conocer tu comisión, ingresá a la sección de tu perfil en el campus Moodle o consultá el padrón oficial de ingresantes publicado en la cartelera digital institucional.",
        
        # Asistencia y Entregas
        "asistencia": "La tecnicatura a distancia exige un mínimo del 75% de participación y asistencia a las actividades sincrónicas obligatorias y la aprobación de las entregas de trabajos prácticos.",
        "faltas": "Las inasistencias a instancias obligatorias deben justificarse formalmente presentando certificado médico o laboral ante Bedelía dentro de las 48 horas hábiles posteriores al hecho.",
        "inasistencias": "Las inasistencias a instancias obligatorias deben justificarse formalmente presentando certificado médico o laboral ante Bedelía dentro de las 48 horas hábiles posteriores al hecho.",
        "trabajos prácticos": "Las entregas fuera de término deben coordinarse directamente con el docente a cargo de la comisión y están sujetas al régimen de evaluación y plazos establecidos en la materia.",
        "entregas": "Las entregas fuera de término deben coordinarse directamente con el docente a cargo de la comisión y están sujetas al régimen de evaluación y plazos establecidos en la materia.",
        "alumno regular": "Se mantiene cumpliendo con el porcentaje mínimo de asistencia, aprobando los trabajos prácticos obligatorios y rindiendo las instancias parciales o coloquios en las fechas del calendario académico.",
        "regularidad": "Se mantiene cumpliendo con el porcentaje mínimo de asistencia, aprobando los trabajos prácticos obligatorios y rindiendo las instancias parciales o coloquios en las fechas del calendario académico.",
        
        # Trámites y SIU Guaraní
        "certificado": "El certificado de alumno regular se solicita de manera digital ingresando a la plataforma SIU Guaraní en la sección 'Trámites > Certificados', el cual se emite automáticamente con firma digital válida.",
        "inscripción": "Todas las inscripciones a materias, promociones y mesas de exámenes finales se gestionan exclusivamente a través del sistema SIU Guaraní dentro de los plazos del calendario académico.",
        "inscribirme": "Todas las inscripciones a materias, promociones y mesas de exámenes finales se gestionan exclusivamente a través del sistema SIU Guaraní dentro de los plazos del calendario académico.",
        "datos personales": "La modificación de datos de contacto o correo electrónico se realiza ingresando a la configuración de tu perfil en SIU Guaraní o enviando una solicitud formal al área de Bedelía.",
        "mail": "La modificación de datos de contacto o correo electrónico se realiza ingresando a la configuración de tu perfil en SIU Guaraní o enviando una solicitud formal al área de Bedelía.",
        "calendario": "El cronograma completo con fechas de inicio de cuatrimestre, periodos de inscripción, recesos y mesas de exámenes está publicado en la sección de normativas de la web institucional.",
        
        # Ayuda técnica
        "requisitos": "Se recomienda contar con una computadora (PC o notebook) con sistema operativo actualizado, navegador web moderno y una conexión a internet estable. Para las prácticas de programación se indicarán los entornos específicos en cada materia.",
        "pc": "Se recomienda contar con una computadora (PC o notebook) con sistema operativo actualizado, navegador web moderno y una conexión a internet estable.",
        "celular": "Se recomienda contar con una computadora (PC o notebook) para seguir las clases y realizar las prácticas de programación de forma óptima.",
        "problemas de conexión": "Si experimentás inconvenientes técnicos durante una evaluación sincrónica, debés tomar una captura de pantalla como evidencia (con fecha y hora) y reportarlo de inmediato a soporte técnico y a tu docente por correo.",
        "examen": "Si experimentás inconvenientes técnicos durante una evaluación sincrónica, debés tomar una captura de pantalla como evidencia y reportarlo de inmediato a soporte técnico y a tu docente.",
        "diferencia": "Las consultas académicas (contenidos, bibliografía, notas) se resuelven con profesores o tutores. Las cuestiones administrativas (certificados, pases, analíticos, SIU Guaraní) se canalizan exclusivamente con Bedelía."
    }

    # Recorremos el diccionario para hacer match con cualquier tema ingresado
    for clave, respuesta in base_conocimiento.items():
        if clave in p_lower:
            return respuesta, False

    # --- 3. DERIVACIÓN FINAL SI NINGUNA CONDICIÓN COINCIDE ---
    return "No encontré una respuesta exacta en los documentos institucionales. ¿Deseas contactar a Bedelía o Tutoría?", True