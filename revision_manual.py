"""
Revisión manual de una muestra de resultados (Unidad 2.2, Bloque 17).

Muestra: los 5 casos con F1 más bajo y los 5 con F1 más alto de resultados_metricas.json
(19 respuestas generadas el 2026-11-01 con gemini-3.6-flash).
Además reviso el caso 9 por la regla "toda respuesta con cifras merece una lectura".

Rúbrica (Bloque 17), por cada caso:
  correccion_factual -> ¿los datos verificables (días, montos, artículos) coinciden con la referencia? si / no / parcialmente
  completitud        -> ¿cubre todo lo que cubre la referencia? si / no / parcialmente
  contradiccion      -> ¿afirma lo contrario de algo en la referencia (por ejemplo, una negación)? si / no
  nota               -> por qué califiqué así

Uso:  python revision_manual.py   (genera revision_manual.json)
"""
import json

revision_manual = [
    
    {
        "id": 4,
        "consulta": "Me despidieron antes de cumplir un año, ¿me pagan algo por vacaciones?",
        "f1": 0.188,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Respuesta correcta y es el F1 MÁS BAJO de todos. Dice 'vacaciones proporcionales' y "
                "'pago' donde la referencia dice 'indemnización por feriado proporcional': mismo "
                "significado con otras palabras. Además es mucho más larga que la referencia.",
    },
    {
        "id": 16,
        "consulta": "¿Dónde tengo que firmar el finiquito para que sea válido?",
        "f1": 0.261,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Correcta y más completa que la referencia: agrega al presidente del sindicato y la "
                "ratificación electrónica en dt.gob.cl. No usa 'ministro de fe', que era una palabra "
                "clave de la referencia, y eso le baja el F1.",
    },
    {
        "id": 2,
        "consulta": "Para contar mis días de vacaciones, ¿el sábado cuenta como día hábil?",
        "f1": 0.267,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Correcta: responde 'No' y cita el art. 69, igual que la referencia. El F1 es bajo "
                "solo porque la respuesta explica más (cuenta de lunes a viernes, cita el artículo).",
    },
    {
        "id": 11,
        "consulta": "¿Me corresponde indemnización por años de servicio si renuncio voluntariamente?",
        "f1": 0.274,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Caso con negación: el modelo dice 'no te corresponde', igual que la referencia, e "
                "incluye la excepción del pacto en el contrato. Agrega correctamente que sí se paga el "
                "feriado proporcional (art. 73).",
    },
    {
        "id": 8,
        "consulta": "Trabajé 8 meses y me despidieron por necesidades de la empresa, ¿me pagan "
                    "indemnización por años de servicio?",
        "f1": 0.286,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Negación y cifra correctas ('No', 'al menos un año'). Agrega lo que sí le "
                "corresponde (aviso previo y feriado proporcional), que es útil para el usuario pero "
                "no está en la referencia.",
    },

    # ---------------- 5 casos con F1 más alto ----------------
    {
        "id": 14,
        "consulta": "¿El empleador me puede descontar algo de la indemnización por el seguro de cesantía?",
        "f1": 0.378,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Correcta: solo en despido por necesidades de la empresa y solo los aportes del "
                "empleador (Ley 19.728, art. 13). Precisa algo que la referencia no dice: nunca se "
                "descuentan los aportes del trabajador.",
    },
    {
        "id": 19,
        "consulta": "Me despidieron pero tenían mis cotizaciones previsionales impagas, ¿es válido el despido?",
        "f1": 0.381,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Correcta: el despido no pone término al contrato y se deben seguir pagando las "
                "remuneraciones (art. 162, Ley Bustos).",
    },
    {
        "id": 3,
        "consulta": "Llevo más de diez años trabajando, ¿tengo derecho a más días de vacaciones?",
        "f1": 0.424,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Cifras correctas: 10 años, 1 día adicional por cada 3 nuevos años (art. 68). Agrega "
                "que los 3 nuevos años deben ser con el empleador actual y que se acredita con el "
                "certificado de la AFP: no está en la referencia, lo dejo anotado para verificarlo.",
    },
    {
        "id": 17,
        "consulta": "Creo que me despidieron injustamente, ¿cuánto plazo tengo para reclamar?",
        "f1": 0.480,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "Plazos correctos: 60 días hábiles, hasta 90 si se reclama antes en la Inspección "
                "(art. 168). Agrega que los días hábiles son de lunes a sábado, dato que no está en "
                "la referencia.",
    },
    {
        "id": 7,
        "consulta": "¿Cuánto me pagan de indemnización por años de servicio si me despiden por "
                    "necesidades de la empresa?",
        "f1": 0.500,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "El F1 más alto, y la respuesta es correcta: un mes por año y fracción superior a seis "
                "meses, tope de 11 años (art. 163). Agrega el tope de 90 UF (art. 172), también correcto.",
    },

    # ---------------- revisión adicional: respuesta con cifras ----------------
    {
        "id": 9,
        "consulta": "Gano un sueldo muy alto, ¿hay un tope para calcular mi indemnización?",
        "f1": 0.301,
        "correccion_factual": "parcialmente",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "El tope de 90 UF y el art. 172 son correctos, pero dice que la UF se toma 'el último "
                "día del mes anterior al despido'; el art. 172 habla del mes anterior al PAGO. Es un "
                "detalle que cambia el monto y el F1 (0.30) es igual al de respuestas sin errores.",
    },
]


if __name__ == "__main__":
    with open("revision_manual.json", "w", encoding="utf-8") as archivo:
        json.dump(revision_manual, archivo, indent=2, ensure_ascii=False)

    correctas = sum(1 for caso in revision_manual if caso["correccion_factual"] == "si")
    contradicciones = sum(1 for caso in revision_manual if caso["contradiccion"] == "si")
    print(f"{len(revision_manual)} casos revisados a mano")
    print(f"Corrección factual completa: {correctas} de {len(revision_manual)}")
    print(f"Contradicciones encontradas: {contradicciones}")
    print("Guardado en revision_manual.json")
