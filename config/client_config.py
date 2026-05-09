"""
AG Systems — config/client_config.py
Carga la configuración del cliente activo.
Para manejar múltiples clientes, cada uno tiene su propio archivo JSON en /clients/
"""

import json
import os
import logging

log = logging.getLogger(__name__)

# El cliente activo se define por variable de entorno
# Esto permite correr múltiples instancias en Railway con diferente CLIENT_ID
CLIENT_ID = os.environ.get("CLIENT_ID", "ferreAmiga")

CLIENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "clients")


def load_client_config(client_id: str = None) -> dict:
    """
    Carga el JSON de configuración del cliente.
    Si no existe el archivo, devuelve configuración de ejemplo.
    """
    cid = client_id or CLIENT_ID
    config_path = os.path.join(CLIENTS_DIR, f"{cid}.json")

    if not os.path.exists(config_path):
        log.warning(f"Config para '{cid}' no encontrada. Usando default.")
        return _default_config()

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    log.info(f"Config cargada: {config.get('nombre', cid)}")
    return config


def _default_config() -> dict:
    """Configuración de fallback si no hay archivo JSON."""
    return {
        "nombre": "AG Systems Demo",
        "tipo": "ferreteria",
        "descripcion": "Tu ferretería de confianza en Tonalá, Chiapas.",
        "horario": "Lunes a Sábado 8am-7pm",
        "direccion": "Tonalá, Chiapas",
        "telefono": "966 113 0527",
        "menu_resumen": "",
        "pago_info": "Transferencia CLABE: 000 000 000 000 000 00 (BBVA)\nCUENTA: 000 000 0000",
        "catalogo": {
            "Cemento Cruz Azul": {"precio": 205, "unidad": "bulto"},
            "Varilla corrugada 3/8": {"precio": 178, "unidad": "pza"},
            "Block 15x20x40": {"precio": 14, "unidad": "pza"},
            "Tinaco Rotoplas 1100L": {"precio": 2350, "unidad": "pza"}
        },
        "fletes": {
            "Tonalá": 150,
            "Arriaga": 200,
            "Pijijiapan": 250,
            "Cintalapa": 300
        },
        "descuentos": [
            {"condicion": "Cemento Cruz Azul >= 50 bultos", "porcentaje": 5},
            {"condicion": "Block 15x20x40 >= 100 pzas", "porcentaje": 3}
        ]
    }
