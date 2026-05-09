"""
AG Systems — handlers/claude_handler.py
Claude Sonnet maneja cotizaciones complejas, listas multi-item, cálculo de IVA/fletes,
descuentos por volumen y cierre de pedidos con instrucciones de pago.
"""

import anthropic
import json
import os
import logging
import random
import string
from datetime import datetime

log = logging.getLogger(__name__)

_claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Historial por usuario (lista de dicts role/content)
_histories: dict[str, list] = {}


def _generate_quote_id() -> str:
    """Genera un ID de cotización único tipo FA-240515-XK2"""
    date_part = datetime.now().strftime("%y%m%d")
    rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"COT-{date_part}-{rand_part}"


def _build_system_prompt(config: dict, mode: str = "quote") -> str:
    negocio   = config.get("nombre", "el negocio")
    catalogo  = json.dumps(config.get("catalogo", {}), ensure_ascii=False, indent=2)
    fletes    = json.dumps(config.get("fletes", {}), ensure_ascii=False)
    descuentos = json.dumps(config.get("descuentos", []), ensure_ascii=False)
    pago_info = config.get("pago_info", "Transferencia CLABE: consultar con el asesor")
    tipo_negocio = config.get("tipo", "ferreteria")

    quote_id = _generate_quote_id()
    fecha    = datetime.now().strftime("%d de %B de %Y")

    if tipo_negocio == "restaurante":
        catalogo_label = "MENÚ"
        item_label     = "platillo"
        total_label    = "Total del pedido"
    else:
        catalogo_label = "CATÁLOGO (precios sin IVA)"
        item_label     = "producto"
        total_label    = "Total con IVA"

    base_prompt = f"""Eres el cotizador profesional de *{negocio}*.

{catalogo_label}:
{catalogo}

FLETES POR ZONA:
{fletes}

DESCUENTOS POR VOLUMEN:
{descuentos}

INFORMACIÓN DE PAGO:
{pago_info}

ID DE COTIZACIÓN PARA ESTA CONVERSACIÓN: {quote_id}
Fecha actual: {fecha}
"""

    if tipo_negocio == "ferreteria":
        base_prompt += """
REGLAS DE COTIZACIÓN:
1. Genera cotizaciones formales con el ID, fecha, tabla de productos, subtotal, IVA 16% y total
2. Si el cliente menciona su ubicación/ciudad, agrega el flete correspondiente automáticamente
3. Aplica descuentos por volumen cuando corresponda y notifícalo
4. Formato WhatsApp: usa *negrita*, líneas separadoras (---) y emojis claros
5. Al terminar la cotización, pregunta: "¿Confirmas este pedido? Puedo enviarte los datos de pago 💳"
6. Si el cliente confirma, muestra los datos de pago y di que el pedido queda registrado

FORMATO DE COTIZACIÓN:
```
🧾 *COTIZACIÓN {ID}*
📅 {fecha}
🏪 {negocio}
---
PRODUCTO          CANT   P/U      IMPORTE
{productos}
---
Subtotal:         ${subtotal}
IVA (16%):        ${iva}
Flete:            ${flete}
*TOTAL:           ${total}*
---
¿Confirmas este pedido?
```
"""
    else:  # restaurante
        base_prompt += """
REGLAS DE PEDIDO:
1. Muestra el pedido claro con cada platillo, cantidad y precio
2. Calcula el total correctamente
3. Si aplica domicilio, agrega el costo
4. Haz sugerencias de complementos: si piden tacos, sugiere bebidas o extras populares
5. Al terminar, pregunta si el pedido es para recoger o a domicilio
6. Si es domicilio, pide la dirección y confirma el tiempo estimado

FORMATO DE PEDIDO:
```
🧾 *PEDIDO {ID}*
🌮 {negocio}
---
{platillos}
---
*TOTAL: ${total}*
🛵 Domicilio: ${costo_domicilio} (~30-40 min)
---
¿Tu pedido es para recoger o a domicilio?
```
"""

    return base_prompt


def handle_quote(phone: str, message: str, config: dict, mode: str = "quote") -> str:
    """
    Maneja cotizaciones y cierres de pedido con Claude Sonnet.
    Mantiene historial de conversación por usuario.
    """
    system_prompt = _build_system_prompt(config, mode)

    # Inicializar historial si es usuario nuevo
    if phone not in _histories:
        _histories[phone] = []
        log.info(f"Nueva sesión Claude para {phone}")

    # Agregar mensaje del usuario
    _histories[phone].append({"role": "user", "content": message})

    try:
        response = _claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=system_prompt,
            messages=_histories[phone]
        )

        reply = response.content[0].text.strip()

        # Guardar respuesta en historial
        _histories[phone].append({"role": "assistant", "content": reply})

        # Limitar historial a últimos 20 mensajes para controlar costos
        if len(_histories[phone]) > 20:
            _histories[phone] = _histories[phone][-20:]

        log.info(f"Claude respondió a {phone}: {reply[:80]}...")
        return reply

    except anthropic.APIError as e:
        log.error(f"Error API Anthropic: {e}")
        return "Tuve un problema generando tu cotización. Por favor intenta en un momento 🙏"
    except Exception as e:
        log.error(f"Error inesperado en Claude handler: {e}", exc_info=True)
        return "Ocurrió un error. Por favor contáctanos directamente 📞"


def clear_history(phone: str):
    """Limpia el historial de cotización de un usuario."""
    if phone in _histories:
        del _histories[phone]
        log.info(f"Historial Claude limpiado para {phone}")
