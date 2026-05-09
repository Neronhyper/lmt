"""
AG Systems — utils/whatsapp.py
Funciones para enviar mensajes, imágenes y botones a través de la Meta Cloud API.
"""

import requests
import os
import logging

log = logging.getLogger(__name__)

WA_TOKEN        = os.environ.get("WA_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
API_VERSION     = "v19.0"
BASE_URL        = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }


def send_text_message(to: str, text: str) -> bool:
    """Envía un mensaje de texto simple."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text, "preview_url": False}
    }
    return _post("/messages", payload)


def send_typing(to: str) -> bool:
    """
    Marca el chat como 'escribiendo...' para mejorar la UX.
    NOTA: La API de Meta no tiene typing indicator nativo en Cloud API,
    esto es un workaround enviando status 'read'.
    """
    # En su lugar simplemente omitimos — la respuesta llega rápido
    return True


def send_image(to: str, image_url: str, caption: str = "") -> bool:
    """Envía una imagen con caption opcional."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption
        }
    }
    return _post("/messages", payload)


def send_document(to: str, doc_url: str, filename: str, caption: str = "") -> bool:
    """Envía un PDF o documento."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "link": doc_url,
            "filename": filename,
            "caption": caption
        }
    }
    return _post("/messages", payload)


def send_location(to: str, lat: float, lng: float, name: str, address: str) -> bool:
    """Envía pin de ubicación (útil para dirección del negocio)."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "location",
        "location": {
            "latitude": lat,
            "longitude": lng,
            "name": name,
            "address": address
        }
    }
    return _post("/messages", payload)


def send_buttons(to: str, body_text: str, buttons: list[dict]) -> bool:
    """
    Envía mensaje con botones interactivos.
    buttons: [{"id": "btn_1", "title": "Ver menú"}, ...]
    Máximo 3 botones.
    """
    if len(buttons) > 3:
        buttons = buttons[:3]

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons
                ]
            }
        }
    }
    return _post("/messages", payload)


def send_list(to: str, body_text: str, button_label: str, sections: list[dict]) -> bool:
    """
    Envía un menú tipo lista desplegable.
    sections: [{"title": "Tacos", "rows": [{"id": "taco_pastor", "title": "Pastor $18"}]}]
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_label,
                "sections": sections
            }
        }
    }
    return _post("/messages", payload)


def mark_as_read(message_id: str) -> bool:
    """Marca un mensaje como leído (doble palomita azul)."""
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    return _post("/messages", payload)


def _post(endpoint: str, payload: dict) -> bool:
    """Realiza el POST a la Meta API. Retorna True si fue exitoso."""
    try:
        response = requests.post(
            BASE_URL + endpoint,
            headers=_headers(),
            json=payload,
            timeout=10
        )
        if response.status_code not in (200, 201):
            log.error(f"Error Meta API {response.status_code}: {response.text[:200]}")
            return False
        return True
    except requests.exceptions.Timeout:
        log.error("Timeout al llamar Meta API")
        return False
    except Exception as e:
        log.error(f"Error enviando mensaje WA: {e}")
        return False
