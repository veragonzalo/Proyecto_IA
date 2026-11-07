"""
Enrutamiento por tema y manejo de errores del Asistente Laboral (Unidad 2.3, Bloques 19 y 20).

Flujo:
  1. Clasificación: el modelo decide el tema de la consulta (vacaciones, indemnizacion,
     finiquito u otro) y la respuesta se normaliza antes de comparar.
  2. Bifurcación: RunnableBranch elige la ruta de ese tema. Si la categoría no se reconoce
     (o es "otro"), cae en la ruta por defecto: responder que está fuera del alcance.
  3. Manejo de errores:
     - cada ruta tiene with_fallbacks: primero un modelo de respaldo, después un mensaje fijo;
     - procesar_consulta_segura envuelve todo en try/except y registra el error con logging.

Uso:  python enrutamiento.py   (hace 2 llamadas reales a Gemini por consulta de ejemplo)
"""
import logging
import unicodedata

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELO_PRINCIPAL = "gemini-3.8-flash"  # el elegido en docs/decision-arquitectura.md
MODELO_RESPALDO = "gemini-3.6-flash"   # la alternativa evaluada, con su propia cuota diaria

CATEGORIAS = ["vacaciones", "indemnizacion", "finiquito", "otro"]


# ---------------------------------------------------------------
# 1. Clasificación de la consulta
# ---------------------------------------------------------------

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica la siguiente consulta laboral en una sola palabra: vacaciones, indemnizacion, "
    "finiquito u otro. Usa 'otro' si no trata de ninguno de esos temas. Responde solo con esa "
    "palabra.\n\nConsulta: {consulta}"
)


def normalizar_categoria(texto: str) -> str:
    """Deja la categoría comparable: sin espacios, en minúsculas, sin tildes ni puntuación.
    Así ' Indemnización.\\n' queda como 'indemnizacion'."""
    texto = texto.strip().lower()
    sin_tildes = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")
    return sin_tildes.strip(" .,;:!¡?¿'\"")


def construir_paso_clasificacion(modelo):
    return plantilla_clasificacion | modelo | StrOutputParser() | normalizar_categoria


# ---------------------------------------------------------------
# 2. Las rutas: un prompt distinto por tema
# ---------------------------------------------------------------

INSTRUCCION_COMUN = (
    "Responde en lenguaje simple, en máximo 80 palabras, citando el artículo del Código del "
    "Trabajo que respalda cada punto. Si te falta un dato para responder, dilo en vez de "
    "suponerlo. No inventes artículos."
)

plantilla_vacaciones = PromptTemplate.from_template(
    "Eres un asistente de derechos laborales en Chile, especializado en feriado legal "
    "(vacaciones): días que corresponden, feriado progresivo, acumulación y feriado "
    "proporcional al terminar el contrato (arts. 67 al 73). " + INSTRUCCION_COMUN +
    "\n\nConsulta: {consulta}"
)

plantilla_indemnizacion = PromptTemplate.from_template(
    "Eres un asistente de derechos laborales en Chile, especializado en indemnizaciones: "
    "por años de servicio, sustitutiva del aviso previo, topes y recargos (arts. 161 al 172). "
    "Si la consulta trae fechas y sueldo, indica cuántos sueldos corresponden y por qué. "
    + INSTRUCCION_COMUN + "\n\nConsulta: {consulta}"
)

plantilla_finiquito = PromptTemplate.from_template(
    "Eres un asistente de derechos laborales en Chile, especializado en el término del "
    "contrato y el finiquito: causales, plazo de pago, firma ante ministro de fe y plazos "
    "para reclamar (arts. 159, 162, 168 y 177). " + INSTRUCCION_COMUN +
    "\n\nConsulta: {consulta}"
)

plantilla_fuera_de_alcance = PromptTemplate.from_template(
    "La siguiente consulta no trata de vacaciones, indemnizaciones ni finiquito. No la "
    "respondas. En máximo 2 oraciones, explica con amabilidad que este asistente solo cubre "
    "esos tres temas y sugiere consultar en la Dirección del Trabajo (dt.gob.cl).\n\n"
    "Consulta: {consulta}"
)


def construir_rutas(modelo) -> dict:
    """Las 4 rutas armadas con un mismo modelo (se llama una vez con el principal y otra con el de respaldo)."""
    return {
        "vacaciones": plantilla_vacaciones | modelo | StrOutputParser(),
        "indemnizacion": plantilla_indemnizacion | modelo | StrOutputParser(),
        "finiquito": plantilla_finiquito | modelo | StrOutputParser(),
        "otro": plantilla_fuera_de_alcance | modelo | StrOutputParser(),
    }


# ---------------------------------------------------------------
# 3. Bifurcación: clasificación + RunnableBranch
# ---------------------------------------------------------------

def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_vacaciones=None,
    cadena_indemnizacion=None,
    cadena_finiquito=None,
    cadena_por_defecto=None,
):
    # una ruta que no se pasa queda como RunnablePassthrough: solo se ejecuta si la eligen,
    # así en una prueba basta con pasar la ruta que se quiere verificar
    cadena_vacaciones = cadena_vacaciones or RunnablePassthrough()
    cadena_indemnizacion = cadena_indemnizacion or RunnablePassthrough()
    cadena_finiquito = cadena_finiquito or RunnablePassthrough()
    cadena_por_defecto = cadena_por_defecto or RunnablePassthrough()

    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "vacaciones", cadena_vacaciones),
        (lambda x: x["categoria"] == "indemnizacion", cadena_indemnizacion),
        (lambda x: x["categoria"] == "finiquito", cadena_finiquito),
        cadena_por_defecto,  # "otro" y cualquier categoría que no se reconozca
    )
    # assign agrega "categoria" al diccionario SIN perder "consulta", que las rutas necesitan
    return RunnablePassthrough.assign(categoria=paso_clasificacion) | bifurcacion


# ---------------------------------------------------------------
# 4. Manejo de errores (Bloque 20)
# ---------------------------------------------------------------

MENSAJE_RESPALDO = (
    "En este momento no puedo generar una respuesta a tu consulta. Puedes revisar tu caso "
    "en la Dirección del Trabajo (dt.gob.cl)."
)

respuesta_generica = RunnableLambda(lambda x: MENSAJE_RESPALDO)


def construir_ruta_segura(cadena, cadena_respaldo=None):
    """Protege una ruta: si falla, prueba la ruta de respaldo (otro modelo) y, si esa también
    falla, devuelve el mensaje fijo. El orden va de lo más parecido a lo más básico."""
    alternativas = [cadena_respaldo] if cadena_respaldo is not None else []
    return cadena.with_fallbacks(alternativas + [respuesta_generica])


def procesar_consulta_segura(cadena, consulta: str) -> str:
    """Red de seguridad final: ningún fallo, en ningún paso, deja al usuario sin respuesta.
    El error queda registrado con logging para quien mantiene el proyecto."""
    try:
        return cadena.invoke({"consulta": consulta})
    except Exception as error:
        logger.error(f"Error procesando la consulta: {error}")
        return (
            "No pudimos procesar tu consulta en este momento. Intenta de nuevo más tarde."
        )


def construir_asistente(modelo, modelo_respaldo=None):
    """Arma el flujo completo: clasificación + rutas, cada pieza con su respaldo."""
    paso_clasificacion = construir_paso_clasificacion(modelo)
    rutas = construir_rutas(modelo)
    rutas_respaldo = construir_rutas(modelo_respaldo) if modelo_respaldo is not None else {}

    if modelo_respaldo is not None:
        # si la clasificación falla con el modelo principal, se intenta con el de respaldo
        paso_clasificacion = paso_clasificacion.with_fallbacks(
            [construir_paso_clasificacion(modelo_respaldo)]
        )

    rutas_seguras = {
        tema: construir_ruta_segura(cadena, rutas_respaldo.get(tema))
        for tema, cadena in rutas.items()
    }
    return construir_cadena_con_enrutamiento(
        paso_clasificacion=paso_clasificacion,
        cadena_vacaciones=rutas_seguras["vacaciones"],
        cadena_indemnizacion=rutas_seguras["indemnizacion"],
        cadena_finiquito=rutas_seguras["finiquito"],
        cadena_por_defecto=rutas_seguras["otro"],
    )


if __name__ == "__main__":
    load_dotenv()
    # max_retries=1: los reintentos internos de LangChain también gastan la cuota diaria
    modelo = ChatGoogleGenerativeAI(model=MODELO_PRINCIPAL, temperature=0, max_retries=1, timeout=90)
    # sin temperature: gemini-3.6-flash usa valores fijos y avisaría que lo ignora
    modelo_respaldo = ChatGoogleGenerativeAI(model=MODELO_RESPALDO, max_retries=1, timeout=90)
    asistente = construir_asistente(modelo, modelo_respaldo)

    consultas = [
        "Llevo 8 meses trabajando y renuncié, ¿me pagan algo por las vacaciones?",
        "Me despidieron por necesidades de la empresa después de 3 años, ¿cuántos sueldos me tocan?",
        "¿Cuántos días tiene la empresa para pagarme el finiquito?",
        "¿Cómo saco mi licencia de conducir?",  # fuera de alcance: debe caer en la ruta por defecto
    ]
    for consulta in consultas:
        print(f"\n>>> {consulta}")
        print(procesar_consulta_segura(asistente, consulta))
