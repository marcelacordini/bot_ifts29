from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.rag_service import buscar_respuesta_rag
from services.rag_service import buscar_en_pdf_rag
from services.safety import enmascarar_datos_personales
from services.db_service import registrar_consulta_anonima

app = FastAPI(
    title="AppMinds API",
    description="Backend del Asistente Virtual para Ingresantes del IFTS N.° 29",
    version="2.0"
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

@app.get("/")
def health_check():
    return {
        "status": "activo",
        "empresa": "AppMinds",
        "proyecto": "Asistente Virtual IFTS 29",
        "arquitectura": "FastAPI / RAG modular"
    }

@app.post("/api/chat")
def procesar_chat(request: ConsultaRequest):
    mensaje_original = request.mensaje.strip()
    if not mensaje_original:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    mensaje_sanitizado = enmascarar_datos_personales(mensaje_original)
    mensaje_lower = mensaje_sanitizado.lower()

    # Menú Principal
    if "volver al menú principal" in mensaje_lower or "inicio" in mensaje_lower or "hola" in mensaje_lower:
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": "¡Hola! Soy el asistente virtual de AppMinds para ingresantes del IFTS 29. ¿Qué información deseas consultar?",
            "opciones": ["📚 Materias", "📋 Plan de Estudio y Correlatividades DSW", "📂 Documentación a entregar Ingresantes", "❓ Preguntas Frecuentes"],
            "derivacion": False
        }

    # Opción 1: Menú de Materias -> Muestra las 4 materias
    if "materias" in mensaje_lower and "plan" not in mensaje_lower:
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": "Has seleccionado Materias de primer año (primer cuatrimestre). Selecciona una para ver su programa o sus horarios:",
            "opciones": ["Administración de Base de Datos", "Técnicas de Programación", "Lógica Computacional", "Elementos de Análisis Matemático", "Volver al menú principal"],
            "derivacion": False
        }

    # Subopciones dentro de cada materia (Programa / Horario)
    if any(mat in mensaje_lower for mat in ["base de datos", "programación", "lógica", "matemático"]):
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": f"Has seleccionado una materia. ¿Qué deseas consultar sobre ella?",
            "opciones": ["📄 Ver Programa", "🕒 Ver Horarios (Comisión A y B)", "Volver al menú principal"],
            "derivacion": False
        }

    # Opción de Horarios por Comisión
    if "ver horarios" in mensaje_lower or "comision" in mensaje_lower:
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": "🕒 **Horarios disponibles:**\n- **Comisión A:** Lunes y miércoles de 19:00 a 21:00 hs.\n- **Comisión B:** Martes y jueves de 19:00 a 21:00 hs.",
            "opciones": ["Volver al menú principal"],
            "derivacion": False
        }

    # Opción Plan de Estudio y Correlatividades DSW
    if "plan de estudio" in mensaje_lower or "correlatividades" in mensaje_lower or "dsw" in mensaje_lower:
        respuesta_rag, deriv = buscar_en_pdf_rag("plan de estudio dsw")
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": respuesta_rag,
            "opciones": ["Volver al menú principal"],
            "derivacion": False
        }

    # Opción Documentación a entregar Ingresantes
    if "documentación" in mensaje_lower or "ingresantes" in mensaje_lower:
        respuesta_rag, deriv = buscar_en_pdf_rag("documentacion ingresantes")
        registrar_consulta_anonima(mensaje_sanitizado, "RESPONDIDA", 1.0)
        return {
            "respuesta": respuesta_rag,
            "opciones": ["Volver al menú principal"],
            "derivacion": False
        }

    # Si llega una consulta libre, procesa con el RAG general de Drive
    respuesta, derivacion = buscar_en_pdf_rag(mensaje_lower)
    registrar_consulta_anonima(mensaje_sanitizado, "DERIVADA" if derivacion else "RESPONDIDA", 0.85)

    opciones = ["Volver al menú principal"]
    if derivacion:
        opciones.append("Contactar a Bedelía")

    return {
        "respuesta": respuesta,
        "opciones": opciones,
        "derivacion": derivacion,
        "disclaimer": "Información basada en documentación oficial del IFTS 29."
    }