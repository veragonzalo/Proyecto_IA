import time

# Reutilizo las funciones que ya tengo en consumir_gemini.py
from consumir_gemini import armar_peticion, enviar_peticion, extraer_texto, calcular_costo

# Los 3 modelos a comparar, con su precio POR TOKEN (USD).
# Fuente: https://ai.google.dev/gemini-api/docs/pricing (consultado el 20-10-2026)
# La página da el precio por 1 millón de tokens, por eso se divide por 1_000_000.
MODELOS = {
    "gemini-3.1-flash-lite": {"entrada": 0.25 / 1_000_000, "salida": 1.50 / 1_000_000},
    "gemini-3.6-flash":      {"entrada": 0.75 / 1_000_000, "salida": 3.75 / 1_000_000},
    "gemini-3.8-flash":      {"entrada": 0.75 / 1_000_000, "salida": 3.75 / 1_000_000},
}

REPETICIONES = 4

# La MISMA pregunta para todos los modelos, relacionada con mi proyecto
PREGUNTA = (
    "Trabajé desde el 1 de marzo de 2022 hasta el 15 de septiembre de 2026 con contrato "
    "indefinido. Mi sueldo era de $850.000 mensuales. Me despidieron por necesidades de la "
    "empresa y no me dieron aviso previo. ¿Qué me corresponde en el finiquito? "
    "Responde en máximo 150 palabras e indica los artículos del Código del Trabajo."
)

# Prompt de sistema: le dice al modelo QUÉ ROL cumple (va en "systemInstruction" del body)
SYSTEM_INSTRUCTION = (
    "Eres un asistente de derechos laborales en Chile. Respondes en lenguaje simple, "
    "citas el artículo del Código del Trabajo que respalda cada punto y no inventas artículos."
)


MAX_INTENTOS = 3   # cuántas veces reintentar si el servicio está saturado
ESPERA_BASE = 5    # segundos de espera antes del primer reintento (después 10, 15...)


# envía la petición y, si Gemini responde 503 (saturado) o 429 (límite de uso),
# espera un poco y vuelve a intentar. Devuelve los datos y la latencia del intento exitoso.
def enviar_con_reintentos(url, body):
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            inicio = time.perf_counter()  # empieza el contador
            datos = enviar_peticion(url, body)
            fin = time.perf_counter()  # termina el contador
            return datos, fin - inicio
        except RuntimeError as error:
            es_temporal = "503" in str(error) or "429" in str(error)
            if es_temporal and intento < MAX_INTENTOS:
                espera = ESPERA_BASE * intento
                print(f"   (intento {intento} falló: {error}. Reintentando en {espera} s...)")
                time.sleep(espera)  # la espera queda FUERA del cronómetro
            else:
                raise  # no es temporal o se acabaron los intentos: el error sube


# hace 4 veces la misma petición con UN modelo e imprime latencia, costo y respuesta
def probar_modelo(modelo, pregunta):
    precios = MODELOS[modelo]
    latencias = []
    costos = []

    print("\n" + "=" * 70)
    print(f"MODELO: {modelo}")
    print("=" * 70)

    for i in range(REPETICIONES):
        print(f"\n--- Petición {i + 1} de {REPETICIONES} ---")
        # el try va DENTRO del for: si falla una petición, no se pierden las demás
        try:
            url, body = armar_peticion(modelo, pregunta, SYSTEM_INSTRUCTION)  # mismo orden que la definición
            datos, latencia = enviar_con_reintentos(url, body)
            costo = calcular_costo(datos, precios["entrada"], precios["salida"])
            texto = extraer_texto(datos)
        except (ValueError, RuntimeError) as error:
            print(f"Petición fallida: {error}")
            continue  # salta a la siguiente petición

        latencias.append(latencia)
        costos.append(costo)

        print(f"Latencia: {latencia:.2f} segundos")
        print(f"Costo: ${costo:.6f} USD")
        print(f"Respuesta:\n{texto}")

        time.sleep(2)  # pausa fuera del cronómetro, para no chocar con el límite de uso (error 429)

    exitosas = len(latencias)
    if exitosas == 0:
        print(f"\n>> {modelo}: ninguna petición funcionó")
        return None

    promedio_latencia = sum(latencias) / exitosas
    promedio_costo = sum(costos) / exitosas
    print(f"\n>> Promedio {modelo} ({exitosas}/{REPETICIONES} exitosas): "
          f"{promedio_latencia:.2f} s | ${promedio_costo:.6f} USD")
    return promedio_latencia, promedio_costo, exitosas


if __name__ == "__main__":
    resultados = {}
    for modelo in MODELOS:
        resultados[modelo] = probar_modelo(modelo, PREGUNTA)

    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"{'Modelo':<25}{'Exitosas':>10}{'Latencia prom.':>16}{'Costo prom. (USD)':>20}")
    for modelo, resultado in resultados.items():
        if resultado is None:
            print(f"{modelo:<25}{'0/' + str(REPETICIONES):>10}{'-':>16}{'-':>20}")
        else:
            latencia, costo, exitosas = resultado
            print(f"{modelo:<25}{f'{exitosas}/{REPETICIONES}':>10}{latencia:>14.2f} s{costo:>20.6f}")