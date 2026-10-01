from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os

from services.rag_service import buscar_en_pdf_rag
from services.safety import enmascarar_datos_personales
from services.db_service import registrar_consulta_anonima

app = FastAPI(
    title="AppMinds API",
    description="Backend del Asistente Virtual para Ingresantes del IFTS N.° 29",
    version="3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConsultaRequest(BaseModel):
    mensaje: str
    comision: str = "General"

@app.get("/", response_class=HTMLResponse)
def home():
    """Sirve la interfaz gráfica del chat leyendo el index.html de forma segura."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "index.html")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"""
        <html>
            <body style="font-family: Arial; padding: 20px;">
                <h3>⚠️ Error cargando la interfaz gráfica</h3>
                <p>Detalle: {str(e)}</p>
            </body>
        </html>
        """

@app.post("/api/chat")
def procesar_chat(request: ConsultaRequest):
    mensaje_original = request.mensaje.strip()
    if not mensaje_original:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    mensaje_sanitizado = enmascarar_datos_personales(mensaje_original)
    mensaje_lower = mensaje_sanitizado.lower()

    # ==========================================
    # 0. MENÚ PRINCIPAL / INICIO / VOLVER
    # ==========================================
    if any(k in mensaje_lower for k in ["menú principal", "menu principal", "inicio", "hola", "volver", "comenzar"]):
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": "¡Hola! Soy el asistente virtual del IFTS N.° 29. Elegí sobre qué tema necesitás ayuda:",
            "opciones": [
                "1. Primeros pasos y Moodle",
                "2. Mi cursada (Horarios y clases)",
                "3. Asistencia y entregas",
                "4. Plan de estudios y carrera",
                "5. Trámites y SIU Guaraní",
                "6. Ayuda técnica"
            ],
            "derivacion": False
        }

    # ==========================================
    # OPCIÓN 1: Primeros pasos y Moodle
    # ==========================================
    if "1. primeros pasos" in mensaje_lower or "primeros pasos" in mensaje_lower or "moodle" in mensaje_lower:
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": "📚 **Primeros pasos y Moodle:** Seleccioná qué querés consultar:",
            "opciones": [
                "Curso de ingreso y familiarización",
                "Cómo usar el campus Moodle",
                "Materiales para arrancar",
                "Menú Principal"
            ],
            "derivacion": False
        }

    if "curso de ingreso" in mensaje_lower or "familiarización" in mensaje_lower:
        return {
            "respuesta": "El curso de ingreso y ambientación está disponible en el campus para que conozcas las herramientas y cronogramas iniciales.",
            "opciones": ["1. Primeros pasos y Moodle", "Menú Principal"],
            "derivacion": False
        }
    if "cómo usar el campus" in mensaje_lower or "campus moodle" in mensaje_lower:
        return {
            "respuesta": "💻 **Uso de Moodle:** Debes ingresar con tu usuario provisto al matricularte. En el área personal verás tus aulas asignadas y recursos de ayuda.",
            "opciones": ["1. Primeros pasos y Moodle", "Menú Principal"],
            "derivacion": False
        }

    # ==========================================
    # OPCIÓN 2: Mi cursada (Embudo: Materia -> Comisión -> Detalle)
    # ==========================================
    if "2. mi cursada" in mensaje_lower or "mi cursada" in mensaje_lower or "horarios y clases" in mensaje_lower or "materias 1° año" in mensaje_lower:
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": "📖 **Paso A:** ¿De qué materia necesitás información?",
            "opciones": [
                "Administración de Base de Datos",
                "Técnicas de Programación",
                "Lógica Computacional",
                "Elementos de Análisis Matemático",
                "Menú Principal"
            ],
            "derivacion": False
        }

    # Filtro de Materias (Paso B: Selección de Comisión)
    if any(m in mensaje_lower for m in ["base de datos", "programación", "lógica", "matemático"]):
        return {
            "respuesta": "👥 **Paso B:** ¿En qué comisión estás?",
            "opciones": ["Comisión A", "Comisión B", "Comisión C", "Comisión D", "Comisión E", "Comisión F", "No sé mi comisión", "Menú Principal"],
            "derivacion": False
        }

    # Manejo de Comisiones (Paso C: Tipo de consulta)
    if "comisión" in mensaje_lower or "comision" in mensaje_lower or "no sé mi comisión" in mensaje_lower:
        if "no sé" in mensaje_lower:
            return {
                "respuesta": "🔍 Para ver tu comisión asignada, ingresá al perfil de tu campus Moodle o consultá el listado oficial de ingresantes publicado en la cartelera digital.",
                "opciones": ["Comisión A", "Comisión B", "Menú Principal"],
                "derivacion": False
            }
        return {
            "respuesta": "⚙️ **Paso C:** ¿Qué querés consultar sobre esta materia y comisión?",
            "opciones": [
                "Días y horarios",
                "Enlaces de clases y grabaciones",
                "Contactar a los docentes",
                "Descargar el cronograma",
                "Descargar el programa",
                "Menú Principal"
            ],
            "derivacion": False
        }

    # Respuestas específicas del Paso C
    if "días y horarios" in mensaje_lower or "horarios" in mensaje_lower:
        return {
            "respuesta": "🕒 **Horarios generales:** Las clases sincrónicas se desarrollan de lunes a jueves en turno noche (19:00 a 21:00 hs) según la comisión asignada.",
            "opciones": ["2. Mi cursada (Horarios y clases)", "Menú Principal"],
            "derivacion": False
        }
    if "enlaces" in mensaje_lower or "grabaciones" in mensaje_lower:
        return {
            "respuesta": "🔗 Los enlaces de Zoom/Meet y las grabaciones de las clases quedan alojados en la sección correspondiente de cada aula virtual en Moodle.",
            "opciones": ["2. Mi cursada (Horarios y clases)", "Menú Principal"],
            "derivacion": False
        }

    # ==========================================
    # OPCIÓN 3: Asistencia y entregas
    # ==========================================
    if "3. asistencia" in mensaje_lower or "asistencia y entregas" in mensaje_lower:
        return {
            "respuesta": "📋 **Asistencia y entregas:** Seleccioná el tema de tu interés:",
            "opciones": [
                "Requisitos de asistencia",
                "Faltas y justificaciones",
                "Entrega de actividades pendientes",
                "Condición de alumno regular",
                "Menú Principal"
            ],
            "derivacion": False
        }

    # ==========================================
    # OPCIÓN 4: Plan de estudios y carrera
    # ==========================================
    if "4. plan de estudios" in mensaje_lower or "plan de estudios" in mensaje_lower:
        respuesta_rag, deriv = buscar_en_pdf_rag("plan de estudio dsw")
        return {
            "respuesta": respuesta_rag,
            "opciones": ["Ver el plan de estudios", "Correlatividades y régimen de aprobación", "Menú Principal"],
            "derivacion": False
        }

    # ==========================================
    # OPCIÓN 5: Trámites y SIU Guaraní
    # ==========================================
    if "5. trámites" in mensaje_lower or "tramites" in mensaje_lower or "siu guaraní" in mensaje_lower:
        return {
            "respuesta": "🏛️ **Trámites y SIU Guaraní:** Elegí una opción:",
            "opciones": [
                "Pedir certificado de alumno regular",
                "Inscripción a materias y exámenes",
                "Actualizar datos personales y mail",
                "Ver el calendario académico",
                "Menú Principal"
            ],
            "derivacion": False
        }

    # ==========================================
    # OPCIÓN 6: Ayuda técnica
    # ==========================================
    if "6. ayuda técnica" in mensaje_lower or "ayuda tecnica" in mensaje_lower:
        return {
            "respuesta": "🛠️ **Ayuda técnica:** Seleccioná tu consulta:",
            "opciones": [
                "Requisitos de PC o celular para cursar",
                "Problemas de conexión en exámenes",
                "Diferencia entre consulta académica y administrativa",
                "Menú Principal"
            ],
            "derivacion": False
        }

    # ==========================================
    # RESPALDO GENERAL / RAG / TRANSVERSAL
    # ==========================================
    respuesta, derivacion = buscar_en_pdf_rag(mensaje_lower)
    registrar_consulta_anonima(mensaje_sanitizado, "DERIVADA" if derivacion else "RESPONDIDA", 0.85)

    opciones = ["Menú Principal"]
    if derivacion or "no tengo la respuesta" in mensaje_lower:
        opciones.append("Contactar a Bedelía o Tutoría")

    return {
        "respuesta": respuesta,
        "opciones": opciones,
        "derivacion": derivacion,
        "disclaimer": "Información basada en documentación oficial del IFTS 29."
    }