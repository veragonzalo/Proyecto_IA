import time
import random
from typing import Callable, Any

from src.consumir_gemini import MODELO, armar_peticion, extraer_texto, enviar_peticion
#MODELO se define en un solo lugar (src/consumir_gemini.py) para no tener dos valores distintos

#Rol del asistente: se usa cuando no se pasa otro system_instruction
#(un systemInstruction vacío puede hacer que Gemini responda error 400)
SYSTEM_INSTRUCTION = (
    "Eres un asistente de derechos laborales en Chile. Respondes en lenguaje simple, "
    "en máximo 80 palabras, y citas el artículo del Código del Trabajo que respalda "
    "cada punto. No inventas artículos."
)

def con_reintento(
    funcion: Callable[[], Any], 
    intentos: int = 3, 
    espera_base: float = 2, 
    espera_maxima: float = 30,) -> Any:
    
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError as error:
            if intento == intentos:
                raise
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)
            espera_con_jitter = espera + random.uniform(0, espera * 0.1)
            print(f"Intento {intento} de {intentos} falló ({error}). Reintentando en {espera_con_jitter:.1f}s...")
            time.sleep(espera_con_jitter)


COSTO_POR_1000_TOKENS = 0.002  # referencial, ajusta según el modelo que uses
costo_total_sesion = 0.0

def registrar_costo(respuesta: dict) -> float:
    global costo_total_sesion
    uso = respuesta.get("usageMetadata", {})
    total_tokens = uso.get("totalTokenCount", 0)
    costo_estimado = (total_tokens / 1000) * COSTO_POR_1000_TOKENS
    costo_total_sesion += costo_estimado
    print(f"Operación: {total_tokens} tokens, costo estimado: ${costo_estimado:.5f} (acumulado: ${costo_total_sesion:.5f})")
    return costo_estimado
 
 
def consultar_modelo(pregunta: str, system_instruction: str = SYSTEM_INSTRUCTION) -> str:
    url, cuerpo = armar_peticion(MODELO, pregunta, system_instruction)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(url, cuerpo))
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")
    registrar_costo(respuesta)
    return extraer_texto(respuesta)
 
 
if __name__ == "__main__":
    resultado = consultar_modelo("¿Cuántos días de vacaciones me corresponden al año?")
    print(resultado)

'''
    for i in range(10):
        try:
            respuesta = consultar_modelo(f"Pregunta de prueba número {i}")
            print(f"Respuesta {i}: {respuesta[:40]}...")
        except RuntimeError as error:
            print(f"Respuesta {i} falló definitivamente: {error}")

'''