from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from cadena_tres_pasos import construir_cadena

# El modelo se reemplaza por un mock: estas pruebas no llaman a Gemini ni gastan cuota.
# Ojo: el side_effect va en el mock mismo, no en .invoke (LangChain lo llama como función),
# y cada respuesta tiene que ser un AIMessage real para que StrOutputParser pueda leerla.

DATOS_FALSOS = "fecha_inicio: 2022-03-01\nsueldo_mensual: 850000\ncausal_termino: necesidades de la empresa"
EXPLICACION_FALSA = "Le corresponden 5 años de indemnización (art. 163)."
VINETAS_FALSAS = "- Te pagan 5 sueldos por años de servicio (art. 163)\nEsta información es referencial."


def crear_modelo_falso():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content=DATOS_FALSOS),        # respuesta del paso 1 (extraer)
        AIMessage(content=EXPLICACION_FALSA),   # respuesta del paso 2 (explicar)
        AIMessage(content=VINETAS_FALSAS),      # respuesta del paso 3 (simplificar)
    ]
    return modelo_falso


def test_cadena_conecta_los_tres_pasos():
    modelo_falso = crear_modelo_falso()
    cadena = construir_cadena(modelo_falso)

    resultado = cadena.invoke({"consulta": "me despidieron, ¿qué me corresponde?"})

    assert modelo_falso.call_count == 3
    assert resultado == VINETAS_FALSAS
    assert isinstance(resultado, str)  # gracias a StrOutputParser, no un objeto con .content


def test_cada_paso_recibe_la_salida_del_anterior():
    modelo_falso = crear_modelo_falso()
    cadena = construir_cadena(modelo_falso)

    cadena.invoke({"consulta": "me despidieron, ¿qué me corresponde?"})

    # lo que el modelo recibió en cada llamada (el prompt ya armado)
    prompt_paso_1 = str(modelo_falso.call_args_list[0])
    prompt_paso_2 = str(modelo_falso.call_args_list[1])
    prompt_paso_3 = str(modelo_falso.call_args_list[2])

    assert "me despidieron" in prompt_paso_1
    assert "sueldo_mensual: 850000" in prompt_paso_2       # el paso 2 usa los datos del paso 1
    assert "me despidieron" not in prompt_paso_2           # ...y no la consulta original
    assert "5 años de indemnización" in prompt_paso_3      # el paso 3 usa la explicación del paso 2


def test_cadena_sin_consulta_falla_antes_de_llamar_al_modelo():
    modelo_falso = crear_modelo_falso()
    cadena = construir_cadena(modelo_falso)

    with pytest.raises(KeyError):
        cadena.invoke({"pregunta": "nombre de variable equivocado"})

    assert modelo_falso.call_count == 0
