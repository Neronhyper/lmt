"""
AG Systems — handlers/gemini_handler.py
Gemini 2.0 Flash maneja respuestas simples: saludos, horarios, ubicación, menú básico.
Es rápido y económico para estos casos.
"""

import google.generativeai as genai
import os, logging

log = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Historial de conversación por usuario (en memoria)
# En producción usar Redis para persistencia entre reinicios
_sessions: dict[str, any] = {}


def _build_system_prompt(config: dict) -> str:
    negocio  = config.get("nombre", "el negocio")
    horario  = config.get("horario", "Lunes a Sábado 8am-7pm")
    direccion = config.get("direccion", "Tonalá, Chiapas")
    telefono = config.get("telefono", "")
    descripcion = config.get("descripcion", "")
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
    Maneja mensajes simples con Gemini Flash.
    Mantiene historial de conversación por usuario.
    """
    system_prompt = _build_system_prompt(config)

    try:
        # Crear o recuperar sesión del usuario
        if phone not in _sessions:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=system_prompt
            )
            _sessions[phone] = model.start_chat(history=[])
            log.info(f"Nueva sesión Gemini para {phone}")

        chat     = _sessions[phone]
        response = chat.send_message(message)
        reply    = response.text.strip()

        log.info(f"Gemini respondió a {phone}: {reply[:60]}...")
        return reply

    except Exception as e:
        log.error(f"Error en Gemini handler: {e}", exc_info=True)
        return "Disculpa, tuve un problema técnico. ¿Puedes repetir tu pregunta? 🙏"


def clear_session(phone: str):
    """Limpia el historial de un usuario (útil para reiniciar conversación)."""
    if phone in _sessions:
        del _sessions[phone]
        log.info(f"Sesión Gemini limpiada para {phone}")
