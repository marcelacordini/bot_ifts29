import re

def enmascarar_datos_personales(texto: str) -> str:
    """
    Enmascara patrones de datos personales (DNI, correos electrónicos, teléfonos)
    conforme a la Ley 25.326 de Protección de Datos Personales.
    """
    # Enmascarar correos electrónicos
    texto_sanitizado = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[CORREO_OCULTO]', texto)
    
    # Enmascarar posibles números de DNI o teléfonos largos
    texto_sanitizado = re.sub(r'\b\d{7,10}\b', '[DATO_OCULTO]', texto_sanitizado)
    
    return texto_sanitizado