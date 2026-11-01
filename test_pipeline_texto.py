import pytest

from pipeline_texto import (
    limpiar_texto,
    procesar_texto,
    vectorizar,
    coincidencia_por_palabras,
    contar_coincidencias,
    calcular_precision_cobertura_f1,
    calcular_metricas,
    resumir_metricas,
)

# Estas pruebas no necesitan mocks: el pipeline no toca la red.


# ---------------- Bloque 15 ----------------

def test_procesar_texto_normaliza_mayusculas_y_puntuacion():
    resultado = procesar_texto("El Cielo, es AZUL!")
    assert resultado == ["el", "cielo", "es", "azul"]


def test_procesar_texto_solo_puntuacion_devuelve_lista_vacia():
    resultado = procesar_texto("¡¡¡...!!!")
    assert resultado == []


def test_limpiar_texto_conserva_tildes_y_enie():
    assert limpiar_texto("¿Cuántos AÑOS de indemnización?") == "cuántos años de indemnización"


def test_limpiar_texto_numeros_sobreviven_sin_puntuacion():
    # el monto pierde el "$" y el punto de miles: es un límite conocido del pipeline
    assert limpiar_texto("Ganaba $850.000 (art. 163)") == "ganaba 850000 art 163"


def test_limpiar_texto_rechaza_lo_que_no_es_texto():
    with pytest.raises(TypeError):
        limpiar_texto(None)


def test_vectorizar_cuenta_repeticiones():
    assert vectorizar(["el", "gato", "el"]) == {"el": 2, "gato": 1}


def test_coincidencia_cruda_vs_procesada():
    referencia = "El cielo es azul."
    respuesta = "el cielo es azul"
    assert coincidencia_por_palabras(referencia.split(), respuesta.split()) == pytest.approx(0.5)
    assert coincidencia_por_palabras(procesar_texto(referencia), procesar_texto(respuesta)) == pytest.approx(1.0)


# ---------------- Bloque 16 ----------------

def test_contar_coincidencias_no_cuenta_repeticiones_de_mas():
    # "el gato el gato" contra "el gato": solo coinciden 1 "el" y 1 "gato"
    assert contar_coincidencias(["el", "gato"], ["el", "gato", "el", "gato"]) == 2


def test_calcular_metricas_ejemplo_calculado_a_mano():
    # mismo ejemplo de la lección: 5 coincidencias, 9 tokens en la respuesta, 6 en la referencia
    resultado = calcular_metricas(
        "El gato duerme en el sofá.",
        "El gato duerme en el sillón todo el día.",
    )
    assert resultado["precision"] == pytest.approx(5 / 9)
    assert resultado["cobertura"] == pytest.approx(5 / 6)
    assert resultado["f1"] == pytest.approx(2 / 3)


def test_calcular_metricas_respuesta_vacia_no_divide_por_cero():
    resultado = calcular_metricas("Te corresponden 15 días hábiles.", "")
    assert resultado == {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}


def test_calcular_metricas_no_detecta_negacion():
    # límite documentado: quitar el "no" invierte el sentido, pero el F1 sigue alto
    resultado = calcular_precision_cobertura_f1(
        procesar_texto("No te corresponde indemnización si renuncias."),
        procesar_texto("Te corresponde indemnización si renuncias."),
    )
    assert resultado["precision"] == pytest.approx(1.0)
    assert resultado["f1"] > 0.9


def test_resumir_metricas_promedia_y_maneja_lista_vacia():
    resultados = [
        {"precision": 1.0, "cobertura": 0.5, "f1": 0.6},
        {"precision": 0.5, "cobertura": 0.5, "f1": 0.4},
    ]
    resumen = resumir_metricas(resultados)
    assert resumen["precision_promedio"] == pytest.approx(0.75)
    assert resumen["f1_promedio"] == pytest.approx(0.5)
    assert resumir_metricas([])["f1_promedio"] == 0.0
