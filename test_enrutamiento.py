"""
Pruebas del enrutamiento (Bloque 19): una por cada ruta, la ruta por defecto y la normalización.
La clasificación se reemplaza por un mock que FUERZA la categoría: así cada prueba ejercita
siempre la ruta que quiere verificar, sin depender de cómo clasifique el modelo real.
"""
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
    normalizar_categoria,
)


def clasificacion_que_devuelve(categoria):
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = categoria  # .return_value, no .invoke.return_value
    return clasificacion_falsa


def ruta_falsa(texto):
    ruta = MagicMock()
    ruta.return_value = texto
    return ruta


def test_enrutamiento_va_a_cadena_vacaciones():
    cadena_vacaciones_falsa = ruta_falsa("respuesta de vacaciones")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_que_devuelve("vacaciones"),
        cadena_vacaciones=cadena_vacaciones_falsa,
    )

    resultado = cadena.invoke({"consulta": "¿cuántos días de vacaciones me tocan?"})

    assert cadena_vacaciones_falsa.called
    assert resultado == "respuesta de vacaciones"


def test_enrutamiento_va_a_cadena_indemnizacion():
    cadena_indemnizacion_falsa = ruta_falsa("respuesta de indemnización")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_que_devuelve("indemnizacion"),
        cadena_indemnizacion=cadena_indemnizacion_falsa,
    )

    resultado = cadena.invoke({"consulta": "me despidieron, ¿cuánto me pagan?"})

    assert cadena_indemnizacion_falsa.called
    assert resultado == "respuesta de indemnización"


def test_enrutamiento_va_a_cadena_finiquito():
    cadena_finiquito_falsa = ruta_falsa("respuesta de finiquito")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_que_devuelve("finiquito"),
        cadena_finiquito=cadena_finiquito_falsa,
    )

    resultado = cadena.invoke({"consulta": "¿dónde firmo el finiquito?"})

    assert cadena_finiquito_falsa.called
    assert resultado == "respuesta de finiquito"


def test_enrutamiento_consulta_otro_va_a_ruta_por_defecto():
    cadena_por_defecto_falsa = ruta_falsa("fuera de alcance")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_que_devuelve("otro"),
        cadena_por_defecto=cadena_por_defecto_falsa,
    )

    resultado = cadena.invoke({"consulta": "¿cómo saco mi licencia de conducir?"})

    assert cadena_por_defecto_falsa.called
    assert resultado == "fuera de alcance"


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    cadena_por_defecto_falsa = ruta_falsa("fuera de alcance")
    cadena_vacaciones_falsa = ruta_falsa("no debería ejecutarse")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_que_devuelve("no estoy seguro"),
        cadena_vacaciones=cadena_vacaciones_falsa,
        cadena_por_defecto=cadena_por_defecto_falsa,
    )

    resultado = cadena.invoke({"consulta": "consulta ambigua"})

    assert cadena_por_defecto_falsa.called
    assert not cadena_vacaciones_falsa.called
    assert resultado == "fuera de alcance"


def test_ruta_recibe_la_consulta_original():
    # RunnablePassthrough.assign agrega "categoria" sin perder "consulta"
    cadena_finiquito_falsa = ruta_falsa("ok")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_que_devuelve("finiquito"),
        cadena_finiquito=cadena_finiquito_falsa,
    )

    cadena.invoke({"consulta": "¿dónde firmo el finiquito?"})

    entrada_de_la_ruta = cadena_finiquito_falsa.call_args.args[0]
    assert entrada_de_la_ruta == {"consulta": "¿dónde firmo el finiquito?", "categoria": "finiquito"}


def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Indemnización.\n")

    resultado = construir_paso_clasificacion(modelo_falso).invoke({"consulta": "me despidieron"})

    assert resultado == "indemnizacion"


@pytest.mark.parametrize("texto, esperado", [
    ("Vacaciones", "vacaciones"),
    ("  FINIQUITO  ", "finiquito"),
    ("indemnización", "indemnizacion"),
    ("otro.", "otro"),
])
def test_normalizar_categoria_variantes(texto, esperado):
    assert normalizar_categoria(texto) == esperado
