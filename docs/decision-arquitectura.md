# Decisión de arquitectura: elección de modelo

**Proyecto:** Asistente Laboral (finiquito, vacaciones proporcionales e indemnización por años de servicio)
**Autor:** Gonzalo Vera
**Fecha:** 20 de octubre de 2026

## Modelo elegido

**`gemini-3.8-flash`** (Google Gemini API)

## Diagrama de arquitectura

Así fluye una pregunta en mi miniaplicación. El modelo elegido es el que va en la caja "API de Gemini".

![Diagrama de arquitectura de la miniaplicación](diagrama_arquitectura.png)

Archivo editable: [`diagrama_arquitectura.drawio`](diagrama_arquitectura.drawio)

## Comparación de candidatos

Mandé **la misma pregunta 4 veces** a cada modelo con el script `comparar_modelos.py`, que reutiliza las funciones de `consumir_gemini.py`:

> Trabajé desde el 1 de marzo de 2022 hasta el 15 de septiembre de 2026 con contrato indefinido. Mi sueldo era de $850.000 mensuales. Me despidieron por necesidades de la empresa y no me dieron aviso previo. ¿Qué me corresponde en el finiquito? Responde en máximo 150 palabras e indica los artículos del Código del Trabajo.

La respuesta correcta tiene que incluir:
- Aviso previo: 1 sueldo, $850.000 (art. 161 y 162).
- Años de servicio: **5 años = $4.250.000**. Son 4 años, 6 meses y 14 días, y la fracción de más de 6 meses cuenta como año completo (art. 163).
- Feriado proporcional (art. 73).

| Criterio | gemini-3.1-flash-lite | gemini-3.6-flash | gemini-3.8-flash |
|---|---|---|---|
| Precio entrada (USD por 1M tokens) | 0,25 | 0,75 | 0,75 |
| Precio salida (USD por 1M tokens) | 1,50 | 3,75 | 3,75 |
| Peticiones exitosas | 4/4 | 3/4 (una falló por error 503) | 4/4 |
| Costo promedio por petición | $0,000446 | $0,006520 | $0,004458 |
| Latencia promedio | 9,17 s | 10,19 s | 31,41 s |
| Rango de latencia | 3,85 – 14,18 s | 10,14 – 10,22 s | 21,09 – 41,26 s |
| Calculó bien los 5 años | 2 de 4 | 3 de 3 | 4 de 4 |
| Artículos citados | Correctos | Uno equivocado (art. 156 para feriado) | Correctos |
| Consistencia entre respuestas | Baja | Alta, pero una respuesta llegó cortada | Alta |
| **Calidad para mi caso** | **Mala** | **Buena** | **Muy buena** |

*Precios del plan pagado, sacados de la [página de precios de Gemini](https://ai.google.dev/gemini-api/docs/pricing) el 20-10-2026. Los Flash suben al doble desde el 1 de enero de 2027. Uso el plan gratuito, así que el costo es lo que pagaría en el plan pagado y sirve para comparar.*

El detalle de cada modelo está en [`comparacion_modelos.md`](comparacion_modelos.md).

## Justificación

**El criterio que más pesó fue la calidad de la respuesta para mi caso.**

Mi asistente le dice a una persona cuánto le corresponde en su finiquito. Si el modelo calcula mal los años o cita un artículo que no es, la persona podría firmar recibiendo menos plata de la que le corresponde. Por eso, que la respuesta sea correcta y no invente artículos es uno de mis criterios críticos del proyecto.

`gemini-3.8-flash` fue el único que respondió **bien las 4 veces**, con los artículos correctos y sin cambiar el cálculo entre una respuesta y otra.

Además salió **un 32% más barato por petición** que `gemini-3.6-flash`. Los dos cobran lo mismo por token, pero el 3.8 usó menos tokens.

**Lo que acepto a cambio:** es el más lento, con unos 31 segundos promedio. Lo acepto porque:
- la prueba la hice con Gemini saturado (hubo varios errores 503), así que voy a volver a medir en otro horario;
- para mi caso, una respuesta correcta en 30 segundos vale más que una equivocada en 10.

## Alternativa descartada y por qué

**`gemini-3.1-flash-lite`**
- **Descartado por calidad.** En 2 de las 4 respuestas calculó **4 años** de indemnización en vez de 5, y en una prueba anterior inventó un recargo del 30% que no corresponde.
- Para la misma pregunta, a veces decía 5 años y a veces 4.
- Es unas 15 veces más barato, pero un asistente legal que se equivoca la mitad de las veces no sirve, por barato que sea.

**`gemini-3.6-flash`**
- **Descartado, pero queda como alternativa.** Es 3 veces más rápido (10 s) y calculó bien los años.
- Quedó fuera por tres razones:
  - citó el **art. 156** para el feriado proporcional, cuando el que corresponde es el art. 73;
  - una de sus respuestas **llegó cortada**;
  - fue **el más caro** por petición.
- Si al volver a medir la latencia del 3.8 sigue sobre 30 segundos, reconsideraría el 3.6. Eso sí, tendría que validar sus citas de artículos.
