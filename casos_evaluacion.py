"""
20 casos de evaluación del Asistente Laboral (Unidad 2.2, Bloque 17).

Cada caso tiene:
  id         -> número para identificarlo
  tema       -> vacaciones, indemnizacion o finiquito
  consulta   -> la pregunta, como la haría un usuario real
  referencia -> la respuesta correcta, escrita por mí según el Código del Trabajo
  alerta     -> por qué este caso puede engañar a la métrica (para la revisión manual)

Las referencias son cortas y con datos verificables (días, meses, artículos),
porque esos son justo los tokens donde la métrica F1 se equivoca más.
"""

CASOS_EVALUACION = [
    # ---------------- VACACIONES (feriado legal) ----------------
    {
        "id": 1,
        "tema": "vacaciones",
        "consulta": "¿Cuántos días de vacaciones me corresponden al año?",
        "referencia": "Te corresponden 15 días hábiles de feriado anual con remuneración íntegra, "
                      "después de un año de trabajo (art. 67).",
        "alerta": "cifra: 15 días hábiles",
    },
    {
        "id": 2,
        "tema": "vacaciones",
        "consulta": "Para contar mis días de vacaciones, ¿el sábado cuenta como día hábil?",
        "referencia": "No, para el feriado el sábado se considera siempre inhábil (art. 69).",
        "alerta": "negación: 'no'",
    },
    {
        "id": 3,
        "tema": "vacaciones",
        "consulta": "Llevo más de diez años trabajando, ¿tengo derecho a más días de vacaciones?",
        "referencia": "Sí, con diez años de trabajo tienes un día adicional de feriado por cada "
                      "tres nuevos años trabajados, llamado feriado progresivo (art. 68).",
        "alerta": "cifras: diez años, un día, tres años",
    },
    {
        "id": 4,
        "tema": "vacaciones",
        "consulta": "Me despidieron antes de cumplir un año, ¿me pagan algo por vacaciones?",
        "referencia": "Sí, te corresponde una indemnización por feriado proporcional al tiempo "
                      "trabajado desde tu contratación o último aniversario (art. 73).",
        "alerta": "sinónimos: feriado proporcional / vacaciones proporcionales",
    },
    {
        "id": 5,
        "tema": "vacaciones",
        "consulta": "¿Puedo pedirle a mi jefe que me pague las vacaciones en vez de tomarlas?",
        "referencia": "No, el feriado no se puede compensar en dinero mientras el contrato está "
                      "vigente; solo se paga en dinero si el contrato termina (art. 73).",
        "alerta": "negación: 'no' / 'solo si termina'",
    },
    {
        "id": 6,
        "tema": "vacaciones",
        "consulta": "¿Puedo juntar las vacaciones de varios años?",
        "referencia": "Sí, el feriado se puede acumular, pero solo hasta por dos períodos "
                      "consecutivos (art. 70).",
        "alerta": "cifra: dos períodos",
    },

    # ---------------- INDEMNIZACIÓN ----------------
    {
        "id": 7,
        "tema": "indemnizacion",
        "consulta": "¿Cuánto me pagan de indemnización por años de servicio si me despiden por "
                    "necesidades de la empresa?",
        "referencia": "Te corresponde un mes de remuneración por cada año de servicio y fracción "
                      "superior a seis meses, con un tope de 11 años (art. 163).",
        "alerta": "cifras: un mes, seis meses, 11 años",
    },
    {
        "id": 8,
        "tema": "indemnizacion",
        "consulta": "Trabajé 8 meses y me despidieron por necesidades de la empresa, ¿me pagan "
                    "indemnización por años de servicio?",
        "referencia": "No, la indemnización por años de servicio exige que el contrato haya "
                      "durado al menos un año (art. 163).",
        "alerta": "negación + cifra: 'no', un año",
    },
    {
        "id": 9,
        "tema": "indemnizacion",
        "consulta": "Gano un sueldo muy alto, ¿hay un tope para calcular mi indemnización?",
        "referencia": "Sí, para calcular la indemnización la remuneración mensual tiene un tope "
                      "de 90 UF (art. 172).",
        "alerta": "cifra: 90 UF",
    },
    {
        "id": 10,
        "tema": "indemnizacion",
        "consulta": "Me despidieron sin avisarme con anticipación, ¿me corresponde algo?",
        "referencia": "Sí, si no te avisaron con 30 días de anticipación te corresponde una "
                      "indemnización sustitutiva equivalente a tu última remuneración mensual "
                      "(art. 161 y 162).",
        "alerta": "cifra: 30 días; sinónimo: aviso previo / mes de aviso",
    },
    {
        "id": 11,
        "tema": "indemnizacion",
        "consulta": "¿Me corresponde indemnización por años de servicio si renuncio voluntariamente?",
        "referencia": "No, la renuncia voluntaria no da derecho a indemnización por años de "
                      "servicio, salvo que tu contrato lo establezca (art. 159 y 163).",
        "alerta": "negación: 'no'",
    },
    {
        "id": 12,
        "tema": "indemnizacion",
        "consulta": "Si me despiden por falta de probidad, ¿tengo derecho a indemnización?",
        "referencia": "No, el despido por una causal del art. 160, como la falta de probidad, "
                      "no da derecho a indemnización por años de servicio.",
        "alerta": "negación: 'no'; cifra: art. 160",
    },
    {
        "id": 13,
        "tema": "indemnizacion",
        "consulta": "Si un juez dice que mi despido por necesidades de la empresa fue injustificado, "
                    "¿me pagan más?",
        "referencia": "Sí, la indemnización por años de servicio se aumenta en un 30% (art. 168).",
        "alerta": "cifra: 30%",
    },
    {
        "id": 14,
        "tema": "indemnizacion",
        "consulta": "¿El empleador me puede descontar algo de la indemnización por el seguro de cesantía?",
        "referencia": "Sí, en un despido por necesidades de la empresa se descuenta lo que el "
                      "empleador aportó a tu cuenta individual del seguro de cesantía "
                      "(Ley 19.728, art. 13).",
        "alerta": "cifra: Ley 19.728",
    },

    # ---------------- FINIQUITO Y TÉRMINO DEL CONTRATO ----------------
    {
        "id": 15,
        "tema": "finiquito",
        "consulta": "¿Cuánto tiempo tiene la empresa para pagarme el finiquito?",
        "referencia": "El empleador debe pagar el finiquito dentro de 10 días hábiles desde la "
                      "separación del trabajador (art. 177).",
        "alerta": "cifra: 10 días hábiles",
    },
    {
        "id": 16,
        "tema": "finiquito",
        "consulta": "¿Dónde tengo que firmar el finiquito para que sea válido?",
        "referencia": "El finiquito debe ser firmado y ratificado ante un ministro de fe, como un "
                      "inspector del trabajo o un notario (art. 177).",
        "alerta": "sinónimos: ministro de fe / notario / inspección",
    },
    {
        "id": 17,
        "tema": "finiquito",
        "consulta": "Creo que me despidieron injustamente, ¿cuánto plazo tengo para reclamar?",
        "referencia": "Tienes 60 días hábiles desde la separación para demandar ante el juzgado "
                      "del trabajo, plazo que puede llegar a 90 días hábiles si antes reclamas "
                      "en la Inspección del Trabajo (art. 168).",
        "alerta": "cifras: 60 y 90 días hábiles",
    },
    {
        "id": 18,
        "tema": "finiquito",
        "consulta": "Si quiero renunciar, ¿con cuánta anticipación tengo que avisar?",
        "referencia": "Debes avisar a tu empleador por escrito con al menos 30 días de "
                      "anticipación (art. 159).",
        "alerta": "cifra: 30 días",
    },
    {
        "id": 19,
        "tema": "finiquito",
        "consulta": "Me despidieron pero tenían mis cotizaciones previsionales impagas, ¿es válido el despido?",
        "referencia": "No, si las cotizaciones no están pagadas al día el despido no pone término "
                      "al contrato y el empleador debe seguir pagando las remuneraciones hasta "
                      "regularizarlas (art. 162, Ley Bustos).",
        "alerta": "negación: 'no'",
    },
    {
        "id": 20,
        "tema": "finiquito",
        "consulta": "Mi contrato a plazo fijo terminó en su fecha, ¿me corresponde indemnización "
                    "por años de servicio?",
        "referencia": "No, el vencimiento del plazo convenido no da derecho a indemnización por "
                      "años de servicio (art. 159).",
        "alerta": "negación: 'no'",
    },
]
