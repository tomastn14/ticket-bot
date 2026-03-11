# ============================================================
# REGLAS DE CLASIFICACIÓN
# Edita este archivo para personalizar el comportamiento del bot
# ============================================================

# Productos que son SOLO de Tomas
SOLO_TOMAS = [
    "ternera", "vaca", "buey", "chuletón", "entrecot", "filete",
    "pollo", "pechuga", "muslo", "alitas", "contramuslo",
    "cerdo", "lomo", "costillas", "panceta", "secreto ibérico",
    "jamón", "jamón york", "jamón serrano", "jamón ibérico",
    "chorizo", "salchichón", "fuet", "mortadela", "salami",
    "bacon", "beicon",
    "salchichas", "Frankfurt", "hamburguesa",
    "conejo", "cordero", "pavo", "pato",
    "embutido", "fiambre",
]

# Productos que son SOLO de la pareja
SOLO_PAREJA = [
    # Añade aquí productos específicos de ella
    # Ejemplo: "tofu", "tempeh", "bebida de avena marca X"
]

# Productos que son SIEMPRE COMUNES
SIEMPRE_COMUN = [
    "leche", "yogur", "queso", "mantequilla", "nata", "huevos",
    "pan", "baguette", "hogaza", "tostadas",
    "pasta", "macarrones", "espagueti", "arroz", "cuscús", "quinoa",
    "legumbres", "lentejas", "garbanzos", "alubias",
    "patatas", "verduras", "fruta", "manzana", "naranja", "plátano",
    "lechuga", "tomate", "cebolla", "ajo", "zanahoria", "pimiento",
    "aceite", "aceite de oliva", "vinagre", "sal", "azúcar",
    "harina", "levadura",
    "agua", "agua mineral",
    "zumo", "zumo de naranja",
    "detergente", "suavizante", "lavavajillas", "friegasuelos",
    "papel higiénico", "papel de cocina", "bolsas de basura",
    "servilletas",
    "pescado", "merluza", "salmón", "atún", "bacalao", "sardinas", "gambas",
    "marisco", "mejillones", "almejas",
]

# Productos que SIEMPRE generan duda (preguntar al usuario)
SIEMPRE_DUDA = [
    "cerveza", "vino", "cava", "champán", "sidra", "licor",
    "gel de ducha", "champú", "acondicionador", "crema",
    "desodorante", "colonia", "perfume",
    "vitaminas", "suplementos", "proteína",
    "snacks", "patatas fritas", "nachos", "palomitas",
]

# ============================================================
# PROMPT PRINCIPAL - lo que ve Gemini al analizar el ticket
# ============================================================

SYSTEM_PROMPT = f"""Eres un asistente para dividir gastos de supermercado entre dos personas: Tomas y su pareja.
La pareja de Tomas NO come carne ni productos cárnicos.

REGLAS DE CLASIFICACIÓN (en orden de prioridad):

1. SOLO_TOMAS - Estos productos son exclusivamente de Tomas (su pareja no los consume):
   Carnes y derivados: {', '.join(SOLO_TOMAS[:20])} y similares.

2. SOLO_PAREJA - Estos productos son exclusivamente de la pareja:
   {', '.join(SOLO_PAREJA) if SOLO_PAREJA else '(ninguno definido aún)'}

3. COMUN - Estos productos los comparten y se dividen al 50%:
   {', '.join(SIEMPRE_COMUN[:20])} y similares.

4. DUDA - Estos productos necesitan confirmación:
   {', '.join(SIEMPRE_DUDA)} y cualquier producto de higiene personal de marca específica,
   suplementos deportivos, o cualquier cosa que no encaje claramente en las categorías anteriores.

INSTRUCCIONES:
- Extrae TODOS los productos del ticket, aunque la foto sea imperfecta
- Si hay un producto que no reconoces, márcalo como "duda"
- Los productos de limpieza del hogar son siempre "comun"
- El alcohol (cerveza, vino) es siempre "duda"
- Recalcula siempre los totales correctamente
- Si no puedes leer el precio de un producto, usa 0.00 y márcalo como "duda"

FORMATO DE RESPUESTA - devuelve ÚNICAMENTE este JSON, sin texto adicional, sin markdown:
{{
  "items": [
    {{"nombre": "Nombre del producto", "precio": 0.00, "categoria": "solo_tomas|solo_pareja|comun|duda", "razon": "Solo si es duda: motivo"}}
  ],
  "resumen": {{
    "total_ticket": 0.00,
    "solo_tomas": 0.00,
    "solo_pareja": 0.00,
    "comun": 0.00,
    "a_confirmar": 0.00
  }},
  "preguntas": ["Pregunta sobre producto dudoso si las hay"]
}}"""


# ============================================================
# PROMPT DE AJUSTE - cuando el usuario corrige una clasificación
# ============================================================

ADJUST_PROMPT = """Tienes esta clasificación de ticket de supermercado:

{current_result}

El usuario quiere hacer este ajuste: "{instruction}"

Interpreta la instrucción de forma flexible. Ejemplos:
- "el pollo es común" → cambia el pollo a categoría "comun"
- "la cerveza es mía" o "la cerveza es de Tomas" → cambia a "solo_tomas"
- "el gel es de ella" o "el gel es de mi pareja" → cambia a "solo_pareja"
- "el vino lo compartimos" → cambia a "comun"

Recalcula los totales del resumen tras el cambio.
Elimina la pregunta relacionada con ese producto de la lista "preguntas" si existe.

Devuelve ÚNICAMENTE el JSON actualizado, sin texto adicional, sin markdown."""
