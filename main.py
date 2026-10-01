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
    version="3.1"
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
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "index.html")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return "<h3>Interfaz no encontrada en el servidor.</h3>"
    except Exception as e:
        return f"<h3>Error interno al cargar la interfaz: {str(e)}</h3>"

@app.post("/api/chat")
def procesar_chat(request: ConsultaRequest):
    try:
        mensaje_original = request.mensaje.strip()
        if not mensaje_original:
            raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

        mensaje_sanitizado = enmascarar_datos_personales(mensaje_original)
        mensaje_lower = mensaje_sanitizado.lower()

        # Menú Principal
        if any(k in mensaje_lower for k in ["menú principal", "menu principal", "inicio", "hola", "volver", "comenzar"]):
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

        # Submenú 1: Primeros pasos y Moodle
        if "1. primeros pasos" in mensaje_lower or "primeros pasos" in mensaje_lower or "moodle" in mensaje_lower:
            return {
                "respuesta": "📚 **Primeros pasos y Moodle:** Seleccioná qué querés consultar:",
                "opciones": ["Curso de ingreso y familiarización", "Cómo usar el campus Moodle", "Materiales para arrancar", "Volver al menú principal"],
                "derivacion": False
            }

        # Submenú 2: Mi cursada
        if "2. mi cursada" in mensaje_lower or "mi cursada" in mensaje_lower or "horarios y clases" in mensaje_lower:
            return {
                "respuesta": "📖 **Paso A:** ¿De qué materia necesitás información?",
                "opciones": ["Administración de Base de Datos", "Técnicas de Programación", "Lógica Computacional", "Elementos de Análisis Matemático", "Volver al menú principal"],
                "derivacion": False
            }

        if any(m in mensaje_lower for m in ["base de datos", "programación", "lógica", "matemático"]):
            return {
                "respuesta": "👥 **Paso B:** ¿En qué comisión estás?",
                "opciones": ["Comisión A", "Comisión B", "Comisión C", "Comisión D", "Comisión E", "Comisión F", "No sé mi comisión", "Volver al menú principal"],
                "derivacion": False
            }

        if "comisión" in mensaje_lower or "comision" in mensaje_lower:
            return {
                "respuesta": "⚙️ **Paso C:** ¿Qué querés consultar sobre esta materia y comisión?",
                "opciones": ["Días y horarios", "Enlaces de clases y grabaciones", "Contactar a los docentes", "Descargar el cronograma", "Descargar el programa", "Volver al menú principal"],
                "derivacion": False
            }

        # Submenú 3: Asistencia
        if "3. asistencia" in mensaje_lower or "asistencia y entregas" in mensaje_lower:
            return {
                "respuesta": "📋 **Asistencia y entregas:** Seleccioná el tema de tu interés:",
                "opciones": ["Requisitos de asistencia", "Faltas y justificaciones", "Entrega de actividades pendientes", "Condición de alumno regular", "Volver al menú principal"],
                "derivacion": False
            }

        # Submenú 5: Trámites
        if "5. trámites" in mensaje_lower or "tramites" in mensaje_lower or "siu guaraní" in mensaje_lower:
            return {
                "respuesta": "🏛️ **Trámites y SIU Guaraní:** Elegí una opción:",
                "opciones": ["Pedir certificado de alumno regular", "Inscripción a materias y exámenes", "Actualizar datos personales y mail", "Ver el calendario académico", "Volver al menú principal"],
                "derivacion": False
            }

        # Submenú 6: Ayuda técnica
        if "6. ayuda técnica" in mensaje_lower or "ayuda tecnica" in mensaje_lower:
            return {
                "respuesta": "🛠️️ **Ayuda técnica:** Seleccioná tu consulta:",
                "opciones": ["Requisitos de PC o celular para cursar", "Problemas de conexión en exámenes", "Diferencia entre consulta académica y administrativa", "Volver al menú principal"],
                "derivacion": False
            }

        # Búsqueda general por RAG o Drive
        respuesta, derivacion = buscar_en_pdf_rag(mensaje_lower)
        opciones = ["Volver al menú principal"]
        if derivacion:
            opciones.append("Contactar a Bedelía o Tutoría")

        return {
            "respuesta": respuesta,
            "opciones": opciones,
            "derivacion": derivacion
        }

    except Exception as e:
        print(f"Error en procesar_chat: {e}")
        return {
            "respuesta": "Recibimos tu consulta. Para una atención personalizada, por favor contactá a Bedelía institucional.",
            "opciones": ["Volver al menú principal", "Contactar a Bedelía o Tutoría"],
            "derivacion": True
        }