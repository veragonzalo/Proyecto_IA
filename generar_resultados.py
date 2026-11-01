"""
Genera las respuestas de los 20 casos de evaluación y calcula sus métricas (Bloque 16 y 17).

Uso:  python generar_resultados.py

- Guarda en resultados_metricas.json DESPUÉS DE CADA CASO, así no se pierde nada
  si Gemini falla a mitad de camino.
- Si lo vuelves a correr, se salta los casos que ya están guardados y solo
  genera los que faltan (por ejemplo, los que fallaron por un error 503).
"""
import json
import os
import time

import cliente
from cliente import consultar_modelo
from pipeline_texto import calcular_metricas, resumir_metricas
from casos_evaluacion import CASOS_EVALUACION

ARCHIVO_RESULTADOS = "resultados_metricas.json"

# Modelo usado SOLO para esta evaluación.
# El modelo de la aplicación (gemini-3.8-flash, en src/consumir_gemini.py) tiene un límite de
# 20 peticiones por día en el plan gratuito: no alcanza para generar los 20 casos.
# gemini-3.6-flash fue la alternativa evaluada en docs/decision-arquitectura.md.
MODELO_EVALUACION = "gemini-3.6-flash"


def cargar_resultados() -> list[dict]:
    """Lee los resultados ya guardados; si el archivo no existe, parte con una lista vacía."""
    if not os.path.exists(ARCHIVO_RESULTADOS):
        return []
    with open(ARCHIVO_RESULTADOS, encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_resultados(resultados: list[dict]) -> None:
    resultados_ordenados = sorted(resultados, key=lambda r: r["id"])
    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as archivo:
        json.dump(resultados_ordenados, archivo, indent=2, ensure_ascii=False)


def generar() -> list[dict]:
    cliente.MODELO = MODELO_EVALUACION  # consultar_modelo lee esta variable en cada llamada
    print(f"Modelo de evaluación: {MODELO_EVALUACION}\n")

    resultados = cargar_resultados()
    ids_listos = {r["id"] for r in resultados}
    fallos_seguidos = 0

    for caso in CASOS_EVALUACION:
        if caso["id"] in ids_listos:
            print(f"Caso {caso['id']:>2}: ya estaba guardado, se salta")
            continue

        try:
            respuesta = consultar_modelo(caso["consulta"])
        except ValueError as error:
            # 401/403: la API key está mal; no tiene sentido seguir con los demás casos
            print(f"Caso {caso['id']:>2}: FALLÓ ({error}). Se detiene la generación.")
            break
        except RuntimeError as error:
            print(f"Caso {caso['id']:>2}: FALLÓ ({error}).")
            fallos_seguidos += 1
            if fallos_seguidos >= 2:
                # dos casos seguidos fallando = cuota agotada o servicio caído:
                # parar ahora evita gastar peticiones (cada reintento también cuenta en la cuota)
                print("Dos casos seguidos fallaron: se detiene para no gastar más cuota. "
                      "Vuelve a correr el script más tarde; seguirá desde donde quedó.")
                break
            continue

        fallos_seguidos = 0

        metricas = calcular_metricas(caso["referencia"], respuesta)
        resultados.append({
            "id": caso["id"],
            "tema": caso["tema"],
            "modelo": MODELO_EVALUACION,
            "consulta": caso["consulta"],
            "referencia": caso["referencia"],
            "respuesta": respuesta,
            **{clave: round(valor, 3) for clave, valor in metricas.items()},
        })
        guardar_resultados(resultados)  # guarda caso por caso
        print(f"Caso {caso['id']:>2}: F1 {metricas['f1']:.2f}")

        time.sleep(5)  # pausa para no chocar con el límite de uso (429) del plan gratuito

    return resultados


if __name__ == "__main__":
    resultados = generar()

    print(f"\n{len(resultados)} de {len(CASOS_EVALUACION)} casos guardados en {ARCHIVO_RESULTADOS}")
    if len(resultados) < len(CASOS_EVALUACION):
        print("Faltan casos: vuelve a correr el script para generar solo los que faltan.")

    resumen = resumir_metricas(resultados)
    print(f"Precisión promedio: {resumen['precision_promedio']:.2f} | "
          f"Cobertura promedio: {resumen['cobertura_promedio']:.2f} | "
          f"F1 promedio: {resumen['f1_promedio']:.2f}")

    peores = sorted(resultados, key=lambda r: r["f1"])
    print("\n5 casos con F1 más bajo:")
    for r in peores[:5]:
        print(f"  Caso {r['id']:>2} (F1 {r['f1']:.2f}): {r['consulta']}")
    print("5 casos con F1 más alto:")
    for r in peores[-5:]:
        print(f"  Caso {r['id']:>2} (F1 {r['f1']:.2f}): {r['consulta']}")
