import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

#Constantes
MODELO = "gemini-3.8-flash"  #elegido en docs/decision-arquitectura.md
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI_API_KEY")

#función para crear la solicitud
#modelo=MODELO: si no le paso un modelo, usa el de siempre
def armar_peticion(pregunta, modelo=MODELO):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacia")
    url = f"{URL_BASE}{modelo}:generateContent?key={API_KEY}"
    body = {
        "contents":
            [{"parts": [{"text": pregunta}]}]
        }
    return url, body

#función envía la petición
def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body, timeout=60) #sin timeout, el except Timeout nunca se activa
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta dentro de unos momentos")
    except requests.exceptions.Timeout:
        raise RuntimeError("Se agoto el tiempo. Intenta en unos momentos")

    if respuesta.status_code != 200:
        raise RuntimeError(f"El servicio respondio con error {respuesta.status_code}")

    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llego en el formato esperado")

#funcion procesa y extrae dato
def extraer_texto(datos): #Gemini
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("la respuesta no recibe el texto generado en el lugar definido.")

def obtener_dato_de_prueba(pregunta):
    url, body = armar_peticion(pregunta) #obtiene url y body

    inicio = time.perf_counter() #empezar contador
    datos = enviar_peticion(url, body)
    fin = time.perf_counter() #termina el contador
    latencia = fin - inicio
    print(f"Latencia {latencia:.2f} segundos")

    costo = calcular_costo(datos, 0.00000075, 0.00000375)
    print(f"Costo de la peticion: ${costo:.6f} USD")
    return extraer_texto(datos)

def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usageMetadata"]
    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso.get("candidatesTokenCount", 0)
    tokens_razonamiento = uso.get("thoughtsTokenCount", 0) #si el modelo no "piensa", este campo no viene
    costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
    return costo

#esto solo se ejecuta si corro ESTE archivo directamente (python consumir_gemini.py),
#NO cuando otro archivo hace "from consumir_gemini import ..."
if __name__ == "__main__":
    try:
        print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operacion: ", error)