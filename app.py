"""
AG Systems — WhatsApp AI Bot
app.py — Punto de entrada Flask + webhook de Meta
"""

from flask import Flask, request, jsonify
from utils.whatsapp import send_text_message, send_typing
from router import route_message
import os, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "ag_systems_2025")


# ─── Verificación del Webhook (Meta lo llama una sola vez al configurar) ───────
@app.route("/webhook", methods=["GET"])
def verify():
    mode  = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        log.info("Webhook verificado ✅")
        return challenge, 200

    log.warning("Verificación fallida ❌")
    return "Forbidden", 403


# ─── Recepción de mensajes ─────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "no data"}), 400

    try:
        entry   = data["entry"][0]
        changes = entry["changes"][0]["value"]

        # Ignorar notificaciones de estado (delivered, read, etc.)
        if "messages" not in changes:
            return jsonify({"status": "ok"}), 200

        message = changes["messages"][0]
        phone   = message["from"]
        msg_type = message.get("type", "")

        # Solo procesamos texto por ahora
        if msg_type != "text":
            send_text_message(phone, "Por el momento solo proceso mensajes de texto 😊")
            return jsonify({"status": "ok"}), 200

        user_text = message["text"]["body"].strip()
        log.info(f"MSG de {phone}: {user_text[:60]}")

        # Indicador de "escribiendo..."
        send_typing(phone)

        # Router decide qué modelo usa y devuelve la respuesta
        reply = route_message(phone, user_text)
        send_text_message(phone, reply)

    except (KeyError, IndexError) as e:
        log.error(f"Estructura inesperada del payload: {e}")
    except Exception as e:
        log.error(f"Error general: {e}", exc_info=True)

    return jsonify({"status": "ok"}), 200


# ─── Health check para Railway ─────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "AG Systems Bot activo 🤖", "version": "1.0.0"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
