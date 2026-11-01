# Límites de la métrica de evaluación

Asistente Laboral · Gonzalo Vera · revisión del 1 de noviembre de 2026

## Qué mide

Cuántas palabras tiene en común la respuesta del modelo con mi respuesta de referencia, contando repeticiones, después de pasar ambos textos a minúsculas y sin puntuación (`calcular_metricas` en `pipeline_texto.py`: precisión, cobertura y F1).

## Modos de falla conocidos

- **Respuestas correctas pero largas puntúan bajo.** Mis referencias tienen en promedio 21 palabras y las respuestas 70, unas 3,3 veces más. Por eso la precisión promedio es 0,22 y ningún F1 pasa de 0,50, aunque las respuestas revisadas son correctas. Ejemplo: caso 4 (vacaciones al despedirme antes del año), correcto y con el F1 más bajo de todos (0,19).
- **Sinónimos y paráfrasis puntúan bajo.** El modelo dice "vacaciones proporcionales" donde mi referencia dice "feriado proporcional" (caso 4), o nombra al "Inspector del Trabajo" y al "Notario" sin decir "ministro de fe" (caso 16, F1 0,26). Las dos respuestas son correctas.
- **Un dato equivocado no baja el puntaje.** En el caso 9, el modelo dice que la UF se toma el mes anterior al *despido*, cuando el art. 172 dice al *pago*. Su F1 (0,30) es igual al de respuestas sin errores (casos 1 y 18: 0,31 y 0,30).
- **La métrica no ve las negaciones.** En esta corrida el modelo respondió bien los 6 casos con "No" (por ejemplo, el caso 11 de la renuncia), pero la métrica no lo habría notado si se equivocaba. "No te corresponde indemnización si renuncias" vs "Te corresponde indemnización si renuncias" da F1 0,91 (prueba `test_calcular_metricas_no_detecta_negacion`).
- **La limpieza borra información de los números.** `limpiar_texto` convierte "$850.000" en "850000" y "art. 163" en "art 163". La métrica cuenta "163" como una palabra más y no distingue un artículo de un plazo en días.
- **"F1 alto" es relativo.** Con todos los casos entre 0,19 y 0,50, los "mejores" no son respuestas mejores: son las que se parecen más en largo y en palabras a mi referencia.

## Muestra revisada

10 casos de 19 respuestas generadas el 2026-11-01 con `gemini-3.6-flash` (detalle en `revision_manual.py`):

- los 5 con F1 más bajo: casos 4, 16, 2, 11 y 8;
- los 5 con F1 más alto: casos 14, 19, 3, 17 y 7;
- más el caso 9, revisado por contener cifras.

Resultado: 10 de los 10 casos de la muestra son correctos, ninguno contradice la referencia, y el único error que encontré (caso 9) tiene un F1 promedio. **En este proyecto, el F1 no separa las respuestas correctas de las incorrectas.**

Usé `gemini-3.6-flash` y no `gemini-3.8-flash` (el modelo de la aplicación) porque el plan gratuito del 3.8 permite solo 20 peticiones por día. El caso 20 quedó pendiente por el mismo límite.

## Recomendación de uso

Usar la **cobertura** como señal de que la respuesta incluye las palabras clave de la referencia, y el F1 solo para comparar versiones del prompt o del modelo sobre los mismos 20 casos. **No usar ningún número para decidir si una respuesta legal es correcta: revisar siempre a mano los días, montos, plazos, artículos y cualquier respuesta que empiece con "No".**
