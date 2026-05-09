"""
AG Systems — handlers/gemini_handler.py
Gemini 2.0 Flash maneja respuestas simples: saludos, horarios, ubicación, menú básico.
Es rápido y económico para estos casos.
"""

from google import genai
from google.genai import types
import os, logging

log = logging.getLogger(__name__)

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Historial de conversación por usuario (en memoria)
_histories: dict[str, list] = {}


def _build_system_prompt(config: dict) -> str:
    negocio      = config.get("nombre", "el negocio")
    horario      = config.get("horario", "Lunes a Sábado 8am-7pm")
    direccion    = config.get("direccion", "Tonalá, Chiapas")
    telefono     = config.get("telefono", "")
    descripcion  = config.get("descripcion", "")
    menu_resumen = config.get("menu_resumen", "")

    return f"""Eres el asistente virtual de *{negocio}* en WhatsApp.
{descripcion}

📍 Dirección: {direccion}
🕐 Horario: {horario}
📞 Teléfono: {telefono}

{menu_resumen}

INSTRUCCIONES:
- Responde siempre en español, tono amigable y natural
- Usa emojis con moderación para hacer la conversación más cálida
- Sé breve: máximo 3-4 líneas por respuesta
- Si el cliente pregunta por precios de múltiples productos, dile que estás preparando su cotización
- Si preguntan algo que no sabes, diles que en breve un asesor los atiende
- NO inventes precios ni información que no tengas
- Siempre termina invitando al cliente a preguntar más"""


def handle_simple(phone: str, message: str, config: dict) -> str:
    """
    Maneja mensajes simples con Gemini 2.0 Flash (nuevo SDK google-genai).
    Mantiene historial de conversación por usuario.
    """
    system_prompt = _build_system_prompt(config)

    if phone not in _histories:
        _histories[phone] = []
        log.info(f"Nueva sesión Gemini para {phone}")

    # Agregar mensaje del usuario al historial
    _histories[phone].append(
        types.Content(role="user", parts=[types.Part(text=message)])
    )

    try:
        response = _client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(system_instruction=system_prompt),
            contents=_histories[phone],
        )

        reply = response.text.strip()

        # Guardar respuesta en historial
        _histories[phone].append(
            types.Content(role="model", parts=[types.Part(text=reply)])
        )

        # Limitar historial a 20 mensajes
        if len(_histories[phone]) > 20:
            _histories[phone] = _histories[phone][-20:]

        log.info(f"Gemini respondió a {phone}: {reply[:60]}...")
        return reply

    except Exception as e:
        log.error(f"Error en Gemini handler: {e}", exc_info=True)
        return "Disculpa, tuve un problema técnico. ¿Puedes repetir tu pregunta? 🙏"


def clear_session(phone: str):
    """Limpia el historial de un usuario."""
    if phone in _histories:
        del _histories[phone]
        log.info(f"Sesión Gemini limpiada para {phone}")
