"""
Pruebas de manejo de errores del flujo orquestado (Bloque 20), según el checklist:
  - una ruta con with_fallbacks: el fallback se ejecuta y en el orden correcto;
  - un fallo FUERA de las rutas (la clasificación) igual entrega una respuesta;
  - el error queda registrado, no solo oculto;
  - el flujo completo, armado con construir_asistente, sigue funcionando cuando el modelo
    principal se cae.

Para simular un paso que falla se usa un RunnableLambda real que lanza la excepción
(un MagicMock genérico puede hacer que la prueba pase sin que el fallback se ejecute de verdad).
"""
import logging
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from enrutamiento import (
    MENSAJE_RESPALDO,
    construir_asistente,
    construir_cadena_con_enrutamiento,
    construir_ruta_segura,
    procesar_consulta_segura,
)


def fallar_a_proposito(x):
    raise ConnectionError("Error de red simulado")


# ---------------- with_fallbacks en una ruta ----------------

def test_ruta_indemnizacion_usa_fallback_ante_fallo_del_modelo():
    cadena_rota = RunnableLambda(fallar_a_proposito)
    cadena_segura = construir_ruta_segura(cadena_rota)

    resultado = cadena_segura.invoke({"consulta": "me despidieron"})

    assert resultado == MENSAJE_RESPALDO
    assert "dirección del trabajo" in resultado.lower()


def test_ruta_usa_primero_el_modelo_de_respaldo():
    cadena_rota = RunnableLambda(fallar_a_proposito)
    cadena_respaldo = RunnableLambda(lambda x: "respuesta del modelo de respaldo")
    cadena_segura = construir_ruta_segura(cadena_rota, cadena_respaldo)

    resultado = cadena_segura.invoke({"consulta": "me despidieron"})

    # el respaldo funcionó, así que el mensaje fijo nunca se usa
    assert resultado == "respuesta del modelo de respaldo"


def test_ruta_cae_en_mensaje_fijo_si_tambien_falla_el_respaldo():
    cadena_rota = RunnableLambda(fallar_a_proposito)
    respaldo_roto = RunnableLambda(fallar_a_proposito)
    cadena_segura = construir_ruta_segura(cadena_rota, respaldo_roto)

    resultado = cadena_segura.invoke({"consulta": "me despidieron"})

    assert resultado == MENSAJE_RESPALDO


def test_ruta_segura_no_cambia_el_camino_normal():
    # si la ruta principal funciona, el fallback no debe intervenir
    cadena_ok = RunnableLambda(lambda x: "respuesta normal")
    cadena_segura = construir_ruta_segura(cadena_ok, RunnableLambda(lambda x: "respaldo"))

    assert cadena_segura.invoke({"consulta": "algo"}) == "respuesta normal"


# ---------------- try/except general ----------------

def test_procesar_consulta_segura_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")  # falla ANTES de elegir ruta
    cadena_falsa = construir_cadena_con_enrutamiento(paso_clasificacion=clasificacion_falsa)

    resultado = procesar_consulta_segura(cadena_falsa, "consulta de prueba")

    assert "no pudimos procesar" in resultado.lower()


def test_procesar_consulta_segura_registra_el_error(caplog):
    cadena_rota = RunnableLambda(fallar_a_proposito)

    with caplog.at_level(logging.ERROR):
        procesar_consulta_segura(cadena_rota, "consulta de prueba")

    # manejar el error no es ocultarlo: tiene que quedar en el registro
    assert "Error de red simulado" in caplog.text


def test_procesar_consulta_segura_devuelve_respuesta_normal():
    cadena_ok = RunnableLambda(lambda x: f"respuesta a: {x['consulta']}")

    assert procesar_consulta_segura(cadena_ok, "hola") == "respuesta a: hola"


# ---------------- flujo completo: construir_asistente ----------------

def test_asistente_completo_usa_modelo_de_respaldo_si_cae_el_principal():
    modelo_caido = MagicMock()
    modelo_caido.side_effect = ConnectionError("modelo principal caído")
    modelo_respaldo = MagicMock()
    modelo_respaldo.side_effect = [
        AIMessage(content="finiquito"),                          # clasificación (respaldo)
        AIMessage(content="Tienen 10 días hábiles (art. 177)."), # ruta finiquito (respaldo)
    ]
    asistente = construir_asistente(modelo_caido, modelo_respaldo)

    resultado = procesar_consulta_segura(asistente, "¿cuándo me pagan el finiquito?")

    assert resultado == "Tienen 10 días hábiles (art. 177)."
    assert modelo_respaldo.call_count == 2


def test_asistente_completo_responde_aunque_fallen_los_dos_modelos():
    modelo_caido = MagicMock()
    modelo_caido.side_effect = ConnectionError("caído")
    respaldo_caido = MagicMock()
    respaldo_caido.side_effect = ConnectionError("también caído")
    asistente = construir_asistente(modelo_caido, respaldo_caido)

    resultado = procesar_consulta_segura(asistente, "¿cuándo me pagan el finiquito?")

    # la clasificación no tiene mensaje fijo: el try/except general entrega la respuesta segura
    assert "no pudimos procesar" in resultado.lower()
