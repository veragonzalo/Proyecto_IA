# Banco de prompts del Asistente Laboral
# Cada prompt tiene:
#   nombre            -> para identificarlo
#   system_instruction-> el ROL y las reglas que sigue el modelo
#   ejemplo_usuario   -> una pregunta real que haría un usuario
#   claves_esperadas  -> las claves que DEBEN venir en el JSON de respuesta (para validar)
#   response_schema   -> la forma exacta del JSON que le pedimos a Gemini

BANCO_DE_PROMPT = [
    # 1) Clasificar la consulta: ¿de qué tema me está preguntando el usuario?
    {
        "nombre": "clasificar_consulta",
        "system_instruction": (
            "Eres un clasificador de consultas de un asistente de derechos laborales en Chile. "
            "Lee la pregunta del usuario y clasifícala en una sola categoría: "
            "finiquito, vacaciones, indemnizacion u otro. "
            "Indica si para responder hay que hacer un cálculo con montos o fechas. "
            "Responde solo con el JSON pedido."
        ),
        "ejemplo_usuario": (
            "Hola, me despidieron la semana pasada y no sé si me están pagando bien "
            "los años que trabajé. ¿Cuánto me debería llegar?"
        ),
        "claves_esperadas": ["categoria", "requiere_calculo", "resumen"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "categoria": {
                    "type": "STRING",
                    "enum": ["finiquito", "vacaciones", "indemnizacion", "otro"]
                },
                "requiere_calculo": {"type": "BOOLEAN"},
                "resumen": {"type": "STRING"}
            },
            "required": ["categoria", "requiere_calculo", "resumen"]
        }
    },

    # 2) Extraer los datos de un despido para calcular finiquito e indemnización
    {
        "nombre": "extraer_datos_despido",
        "system_instruction": (
            "Eres un asistente que extrae datos de consultas laborales en Chile. "
            "De la pregunta del usuario, extrae: fecha de inicio y de término del contrato "
            "(formato AAAA-MM-DD), sueldo mensual en pesos (solo el número), la causal del término "
            "y si le dieron aviso previo de 30 días. "
            "Si un dato no aparece en la pregunta, déjalo en null. No inventes datos. "
            "Responde solo con el JSON pedido."
        ),
        "ejemplo_usuario": (
            "Entré a trabajar el 1 de marzo de 2022 y me despidieron el 15 de septiembre de 2026 "
            "por necesidades de la empresa. Ganaba $850.000 líquidos y me avisaron el mismo día."
        ),
        "claves_esperadas": ["fecha_inicio", "fecha_termino", "sueldo_mensual", "causal", "aviso_previo"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "fecha_inicio": {"type": "STRING", "nullable": True},
                "fecha_termino": {"type": "STRING", "nullable": True},
                "sueldo_mensual": {"type": "NUMBER", "nullable": True},
                "causal": {
                    "type": "STRING",
                    "enum": [
                        "necesidades_empresa",
                        "renuncia",
                        "mutuo_acuerdo",
                        "despido_disciplinario",
                        "vencimiento_plazo",
                        "desconocida"
                    ]
                },
                "aviso_previo": {"type": "BOOLEAN", "nullable": True}
            },
            "required": ["fecha_inicio", "fecha_termino", "sueldo_mensual", "causal", "aviso_previo"]
        }
    },

    # 3) Extraer los datos para calcular vacaciones proporcionales
    {
        "nombre": "extraer_datos_vacaciones",
        "system_instruction": (
            "Eres un asistente que extrae datos sobre vacaciones (feriado legal) de consultas "
            "laborales en Chile. De la pregunta del usuario, extrae: fecha de inicio del contrato, "
            "fecha de término (formato AAAA-MM-DD), sueldo mensual en pesos (solo el número) "
            "y cuántos días de vacaciones ya tomó en el último año. "
            "Si un dato no aparece en la pregunta, déjalo en null. No inventes datos. "
            "Responde solo con el JSON pedido."
        ),
        "ejemplo_usuario": (
            "Renuncié y mi último día es el 31 de octubre de 2026. Trabajo desde el 10 de enero de 2024, "
            "gano $620.000 y este año solo me tomé 5 días de vacaciones. "
            "¿Me tienen que pagar los días que no usé?"
        ),
        "claves_esperadas": ["fecha_inicio", "fecha_termino", "sueldo_mensual", "dias_tomados"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "fecha_inicio": {"type": "STRING", "nullable": True},
                "fecha_termino": {"type": "STRING", "nullable": True},
                "sueldo_mensual": {"type": "NUMBER", "nullable": True},
                "dias_tomados": {"type": "INTEGER", "nullable": True}
            },
            "required": ["fecha_inicio", "fecha_termino", "sueldo_mensual", "dias_tomados"]
        }
    },
]