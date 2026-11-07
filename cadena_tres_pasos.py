"""
Chain de tres pasos del Asistente Laboral (Unidad 2.3, Bloque 18).

Paso 1 · Extraer:     saca de la consulta los datos laborales (fechas, sueldo, causal, aviso previo).
Paso 2 · Explicar:    con esos datos, explica qué le corresponde al trabajador, citando artículos.
Paso 3 · Simplificar: reescribe la explicación en lenguaje simple, en viñetas, con una advertencia.

Cada paso usa SOLO la salida del anterior: el paso 2 no ve la consulta original, solo los datos
extraídos. Así, si el paso 1 se equivoca o deja un dato "no indicado", se nota en el paso 2.

Uso:  python cadena_tres_pasos.py   (hace 3 llamadas reales a Gemini)
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

MODELO = "gemini-3.8-flash"
MODELO_RESPALDO = "gemini-3.6-flash"  # si el principal falla (503 saturado, 429 cuota)

# Paso 1: convierte una consulta escrita libremente en una lista ordenada de datos.
plantilla_extraccion = PromptTemplate.from_template(
    "Extrae de la siguiente consulta laboral estos datos, uno por línea, con el formato "
    "'campo: valor':\n"
    "fecha_inicio, fecha_termino, sueldo_mensual, causal_termino, aviso_previo.\n"
    "Usa fechas en formato AAAA-MM-DD y el sueldo solo como número. "
    "Si un dato no aparece en la consulta, escribe 'no indicado'. No inventes datos.\n\n"
    "Consulta: {consulta}"
)

# Paso 2: aplica el Código del Trabajo a los datos extraídos.
plantilla_explicacion = PromptTemplate.from_template(
    "Eres un asistente de derechos laborales en Chile. Con los siguientes datos de un "
    "trabajador, explica qué le corresponde al terminar su contrato (indemnización por años "
    "de servicio, indemnización sustitutiva del aviso previo y feriado proporcional), "
    "citando el artículo del Código del Trabajo de cada punto. Si un dato necesario está "
    "como 'no indicado', dilo en vez de suponerlo. No inventes artículos.\n\n"
    "Datos:\n{datos}"
)

# Paso 3: deja la explicación lista para una persona sin conocimientos legales.
plantilla_simplificacion = PromptTemplate.from_template(
    "Reescribe la siguiente explicación para una persona sin conocimientos legales, en "
    "máximo 5 viñetas markdown, cada una con su artículo entre paréntesis. Sin introducción. "
    "Termina con esta línea exacta: 'Esta información es referencial; confirma tu caso en la "
    "Dirección del Trabajo.'\n\n"
    "Explicación:\n{explicacion}"
)


def construir_cadena(modelo):
    """Arma la chain de 3 pasos SIN ejecutarla. Recibe el modelo para poder usar un mock en las pruebas."""
    paso_extraccion = plantilla_extraccion | modelo | StrOutputParser()
    paso_explicacion = plantilla_explicacion | modelo | StrOutputParser()
    paso_simplificacion = plantilla_simplificacion | modelo | StrOutputParser()

    return (
        paso_extraccion
        | (lambda datos: {"datos": datos})              # str del paso 1 -> dict que espera el paso 2
        | paso_explicacion
        | (lambda explicacion: {"explicacion": explicacion})  # str del paso 2 -> dict que espera el paso 3
        | paso_simplificacion
    )


if __name__ == "__main__":
    load_dotenv()
    # temperature=0: queremos respuestas consistentes, no creativas, en un tema legal.
    # max_retries=1: los reintentos internos de LangChain también gastan la cuota diaria.
    modelo_principal = ChatGoogleGenerativeAI(model=MODELO, temperature=0, max_retries=1, timeout=90)
    # sin temperature: gemini-3.6-flash usa valores fijos y avisaría que lo ignora
    modelo_respaldo = ChatGoogleGenerativeAI(model=MODELO_RESPALDO, max_retries=1, timeout=90)
    # with_fallbacks (Bloque 20): en cada paso, si el modelo principal falla se usa el de respaldo.
    # construir_cadena no cambia: recibe "un modelo", sin importar si trae respaldo o no.
    modelo = modelo_principal.with_fallbacks([modelo_respaldo])
    cadena = construir_cadena(modelo)

    consulta = (
        "Trabajé desde el 1 de marzo de 2022 hasta el 15 de septiembre de 2026 con contrato "
        "indefinido. Ganaba $850.000 al mes y me despidieron por necesidades de la empresa "
        "sin avisarme con anticipación. ¿Qué me corresponde?"
    )
    try:
        print(cadena.invoke({"consulta": consulta}))
    except Exception as error:
        print(f"No se pudo completar la consulta, ni con el modelo de respaldo: {error}")
