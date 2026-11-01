"""
Pipeline de texto del Asistente Laboral (Unidad 2.2).

Bloque 15: limpiar_texto, tokenizar, vectorizar, procesar_texto
Bloque 16: contar_coincidencias, calcular_precision_cobertura_f1, calcular_metricas, resumir_metricas

Si ejecutas este archivo directamente (python pipeline_texto.py), compara 3 respuestas reales
de consultar_modelo contra referencias escritas por mí, midiendo la coincidencia ANTES
(texto crudo) y DESPUÉS (texto procesado) del pipeline.
"""
import json
import re
from collections import Counter

from cliente import consultar_modelo


# ---------------------------------------------------------------
# Bloque 15: del texto crudo a una lista de tokens
# ---------------------------------------------------------------

def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: minúsculas, sin puntuación y sin espacios repetidos."""
    if not isinstance(texto, str):
        tipo = type(texto).__name__
        raise TypeError(f"limpiar_texto espera str, no {tipo}")

    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)      # quita todo lo que no sea letra, número o espacio
    texto = re.sub(r"\s+", " ", texto).strip()  # junta espacios repetidos en uno solo
    return texto


def tokenizar(texto_limpio: str) -> list[str]:
    """Convierte texto limpio en una lista de tokens (palabras)."""
    return texto_limpio.split()


def vectorizar(tokens: list[str]) -> Counter:
    """Cuenta cuántas veces aparece cada token ("bolsa de palabras")."""
    return Counter(tokens)


def procesar_texto(texto: str) -> list[str]:
    """Limpia y tokeniza en un solo paso, para no olvidar ninguno de los dos."""
    texto_limpio = limpiar_texto(texto)
    return tokenizar(texto_limpio)


def coincidencia_por_palabras(tokens_referencia: list[str], tokens_respuesta: list[str]) -> float:
    """Métrica simple del Bloque 15: qué proporción de las palabras de la referencia aparecen en la respuesta."""
    if not tokens_referencia:
        return 0.0  # evita la división por cero si la referencia quedó vacía
    comunes = set(tokens_referencia) & set(tokens_respuesta)
    return len(comunes) / len(set(tokens_referencia))


# ---------------------------------------------------------------
# Bloque 16: precisión, cobertura y F1
# ---------------------------------------------------------------

def contar_coincidencias(tokens_referencia: list[str], tokens_respuesta: list[str]) -> int:
    """Cuenta las coincidencias entre referencia y respuesta, respetando repeticiones."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta  # toma el mínimo de cada palabra
    return sum(interseccion.values())


def calcular_precision_cobertura_f1(tokens_referencia: list[str], tokens_respuesta: list[str]) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    coincidencias = contar_coincidencias(tokens_referencia, tokens_respuesta)
    precision = coincidencias / len(tokens_respuesta)   # de lo que dijo el modelo, ¿cuánto está en la referencia?
    cobertura = coincidencias / len(tokens_referencia)  # de lo que debía decir, ¿cuánto dijo?

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    return {"precision": precision, "cobertura": cobertura, "f1": f1}


def calcular_metricas(texto_referencia: str, texto_respuesta: str) -> dict[str, float]:
    """De dos textos a sus métricas: procesa AMBOS lados antes de comparar."""
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)
    return calcular_precision_cobertura_f1(tokens_referencia, tokens_respuesta)


def resumir_metricas(resultados: list[dict]) -> dict[str, float]:
    """Promedio de precisión, cobertura y F1 sobre una lista de resultados."""
    if not resultados:
        return {"precision_promedio": 0.0, "cobertura_promedio": 0.0, "f1_promedio": 0.0}
    n = len(resultados)
    return {
        "precision_promedio": sum(r["precision"] for r in resultados) / n,
        "cobertura_promedio": sum(r["cobertura"] for r in resultados) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }


# ---------------------------------------------------------------
# Actividad Bloque 15: 3 respuestas reales, antes y después del pipeline
# ---------------------------------------------------------------

# (consulta, referencia escrita por mí según el Código del Trabajo)
CASOS = [
    (
        "¿Cuántos días de vacaciones me corresponden al año si trabajo de lunes a viernes?",
        "Te corresponden 15 días hábiles de feriado anual con remuneración íntegra, "
        "después de un año de trabajo (art. 67 del Código del Trabajo).",
    ),
    (
        "¿Cuánto me pagan de indemnización por años de servicio si me despiden por necesidades de la empresa?",
        "Te corresponde un mes de remuneración por cada año de servicio y fracción superior "
        "a seis meses, con un tope de 11 años (art. 163 del Código del Trabajo).",
    ),
    (
        "¿Me corresponde indemnización por años de servicio si renuncio voluntariamente?",
        "No te corresponde indemnización por años de servicio si renuncias voluntariamente, "
        "salvo que tu contrato lo establezca (art. 159 y 163 del Código del Trabajo).",
    ),
]


if __name__ == "__main__":
    registro = []
    for numero, (consulta, referencia) in enumerate(CASOS, start=1):
        try:
            respuesta = consultar_modelo(consulta)
        except (ValueError, RuntimeError) as error:
            print(f"[Caso {numero}] No se pudo obtener respuesta: {error}")
            continue

        # ANTES: texto crudo, separado solo por espacios
        pct_crudo = coincidencia_por_palabras(referencia.split(), respuesta.split())
        # DESPUÉS: los dos lados pasan por el pipeline
        pct_proc = coincidencia_por_palabras(procesar_texto(referencia), procesar_texto(respuesta))
        metricas = calcular_metricas(referencia, respuesta)

        print(f"\n[Caso {numero}] {consulta}")
        print(f"Respuesta: {respuesta}")
        print(f"[Caso {numero}] Coincidencia texto crudo:     {pct_crudo:.1%}")
        print(f"[Caso {numero}] Coincidencia texto procesado: {pct_proc:.1%}")
        print(f"[Caso {numero}] Precisión {metricas['precision']:.2f} | "
              f"Cobertura {metricas['cobertura']:.2f} | F1 {metricas['f1']:.2f}")

        registro.append({
            "consulta": consulta,
            "referencia": referencia,
            "respuesta": respuesta,
            "coincidencia_cruda": round(pct_crudo, 3),
            "coincidencia_procesada": round(pct_proc, 3),
            **{clave: round(valor, 3) for clave, valor in metricas.items()},
        })

    # registro del antes y el después, como evidencia de la actividad
    with open("docs/registro_pipeline.json", "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)
    print(f"\nRegistro guardado en docs/registro_pipeline.json ({len(registro)} casos)")
