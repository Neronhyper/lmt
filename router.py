"""
AG Systems — router.py
Gemini Flash clasifica la intención → decide si va a Gemini (simple) o Claude (cotización)
"""

from handlers.gemini_handler import handle_simple
from handlers.claude_handler import handle_quote
from config.client_config import load_client_config
import google.generativeai as genai
import os, logging

log = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_classifier = genai.GenerativeModel("gemini-2.0-flash")

# ─── Intents ──────────────────────────────────────────────────────────────────
INTENT_QUOTE  = "COTIZACION"
INTENT_SIMPLE = "SIMPLE"
INTENT_ORDER  = "PEDIDO"      # confirmación de compra

CLASSIFIER_PROMPT = """Eres un clasificador de mensajes para un negocio local en México.
Clasifica el siguiente mensaje en UNA sola palabra:

- COTIZACION → el cliente pide precios, presupuesto, cuánto cuesta, lista de materiales, cotización
- PEDIDO     → el cliente confirma un pedido, quiere pagar, dice "sí confirmo", "lo quiero", "me lo llevan"
- SIMPLE     → cualquier otra cosa: saludos, horarios, dirección, preguntas generales, agradecimientos

Responde ÚNICAMENTE con la palabra: COTIZACION, PEDIDO o SIMPLE

Mensaje: "{message}"
"""


def classify_intent(message: str) -> str:
    try:
        prompt   = CLASSIFIER_PROMPT.format(message=message)
        response = _classifier.generate_content(prompt)
        intent   = response.text.strip().upper()

        if intent not in [INTENT_QUOTE, INTENT_SIMPLE, INTENT_ORDER]:
            intent = INTENT_SIMPLE

        log.info(f"Intent clasificado: {intent}")
        return intent

    except Exception as e:
        log.error(f"Error clasificando intent: {e}")
        return INTENT_SIMPLE  # fallback seguro


def route_message(phone: str, message: str) -> str:
    """
    Punto de entrada principal.
    Recibe el teléfono y mensaje, devuelve la respuesta final como string.
    """
    # Cargar configuración del cliente (catálogo, prompts, nombre del negocio)
    # Por ahora usa el cliente por defecto. En producción puedes mapear
    # phone_number_id → cliente si manejas múltiples negocios.
    config = load_client_config()

    intent = classify_intent(message)

    if intent == INTENT_QUOTE:
        return handle_quote(phone, message, config)

    elif intent == INTENT_ORDER:
        # Redirigir a Claude para cerrar el pedido con instrucciones de pago
        return handle_quote(phone, message, config, mode="order")

    else:
        return handle_simple(phone, message, config)
