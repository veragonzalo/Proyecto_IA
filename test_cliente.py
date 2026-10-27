from unittest.mock import patch, Mock
import pytest
import cliente
from cliente import con_reintento, registrar_costo, consultar_modelo
from src.consumir_gemini import enviar_peticion


@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    cliente.costo_total_sesion = 0
    yield


# enviar_peticion (vive en src/consumir_gemini.py)


def test_enviar_peticion_credencial_invalida():
    respuesta_falsa = Mock(status_code=401)
    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion("https://ejemplo.invalid", {"pregunta": "test"})


def test_enviar_peticion_sin_permiso():
    respuesta_falsa = Mock(status_code=403)
    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion("https://ejemplo.invalid", {"pregunta": "test"})


def test_enviar_peticion_limite_de_uso():
    respuesta_falsa = Mock(status_code=429)
    respuesta_falsa.headers = {}  # sin "Retry-After"
    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion("https://ejemplo.invalid", {"pregunta": "test"})


def test_enviar_peticion_error_del_servidor():
    respuesta_falsa = Mock(status_code=503)
    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion("https://ejemplo.invalid", {"pregunta": "test"})


def test_enviar_peticion_exito():
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"texto": "respuesta simulada"}
    with patch("src.consumir_gemini.requests.post", return_value=respuesta_falsa):
        resultado = enviar_peticion("https://ejemplo.invalid", {"pregunta": "test"})
    assert resultado == {"texto": "respuesta simulada"}


# con_reintento (vive en cliente.py)


def test_con_reintento_reintenta_ante_timeout():
    intentos = {"n": 0}

    def falla_una_vez():
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise TimeoutError("simulado")
        return "ok"

    with patch("cliente.time.sleep") as mock_sleep:
        resultado = con_reintento(falla_una_vez)

    assert resultado == "ok"
    assert intentos["n"] == 2          # falló 1 vez y funcionó al 2° intento
    mock_sleep.assert_called_once()    # esperó una vez (no importa cuántos segundos)


def test_con_reintento_no_reintenta_value_error():
    intentos = {"n": 0}

    def falla_con_value_error():
        intentos["n"] += 1
        raise ValueError("credencial inválida simulada")

    with patch("cliente.time.sleep") as mock_sleep:
        with pytest.raises(ValueError):
            con_reintento(falla_con_value_error)

    assert intentos["n"] == 1          # se rindió al primer intento
    mock_sleep.assert_not_called()     # nunca esperó para reintentar


def test_con_reintento_agota_intentos():
    intentos = {"n": 0}

    def siempre_falla():
        intentos["n"] += 1
        raise TimeoutError("simulado")

    with patch("cliente.time.sleep"):
        with pytest.raises(TimeoutError):
            con_reintento(siempre_falla, intentos=3)

    assert intentos["n"] == 3          # usó los 3 intentos y dejó pasar el error original



# registrar_costo (vive en cliente.py)


def test_registrar_costo_calcula_correcto():
    respuesta_falsa = {"usageMetadata": {"totalTokenCount": 1000}}
    costo = registrar_costo(respuesta_falsa)
    assert costo == pytest.approx(cliente.COSTO_POR_1000_TOKENS)


def test_registrar_costo_acumula():
    respuesta_falsa = {"usageMetadata": {"totalTokenCount": 1000}}
    registrar_costo(respuesta_falsa)
    registrar_costo(respuesta_falsa)
    assert cliente.costo_total_sesion == pytest.approx(2 * cliente.COSTO_POR_1000_TOKENS)



# consultar_modelo (vive en cliente.py)

def test_consultar_modelo_convierte_error():
    with patch("cliente.con_reintento", side_effect=TimeoutError("simulado")):
        with pytest.raises(RuntimeError):
            consultar_modelo("pregunta de prueba")


def test_consultar_modelo_propaga_value_error():
    with patch("cliente.con_reintento", side_effect=ValueError("credencial inválida simulada")):
        with pytest.raises(ValueError):
            consultar_modelo("pregunta de prueba")

