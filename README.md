# AG Systems — WhatsApp AI Bot

Bot de WhatsApp con IA dual (Gemini + Claude) para automatización de ventas y cotizaciones.

## Estructura

```
whatsapp-bot/
├── app.py                    # Flask webhook
├── router.py                 # Clasificador de intents (Gemini Flash)
├── handlers/
│   ├── gemini_handler.py     # Respuestas simples (saludos, horarios, menú)
│   └── claude_handler.py     # Cotizaciones complejas + cierre de pedidos
├── config/
│   └── client_config.py      # Cargador de configuración por cliente
├── utils/
│   └── whatsapp.py           # Meta Cloud API (enviar mensajes, imágenes, botones)
├── clients/
│   ├── ferreAmiga.json       # Config FerreAmiga
│   └── gallito_inn.json      # Config Taquería Gallito INN
├── requirements.txt
├── railway.toml
└── .env.example
```

## Setup rápido

### 1. Clonar y configurar entorno

```bash
git clone https://github.com/alecfckk/whatsapp-bot
cd whatsapp-bot
cp .env.example .env
# Editar .env con tus keys reales
pip install -r requirements.txt
```

### 2. Configurar Meta App

1. Ir a [developers.facebook.com](https://developers.facebook.com)
2. Crear App → Tipo: Business
3. Agregar producto: **WhatsApp**
4. En "API Setup": copiar `PHONE_NUMBER_ID` y generar `ACCESS_TOKEN`
5. En "Webhooks": URL = `https://tu-app.railway.app/webhook`
6. Suscribir evento: `messages`
7. El `VERIFY_TOKEN` debe coincidir con tu `.env`

### 3. Deploy en Railway

```bash
railway login
railway init
railway up
```

Agregar variables de entorno en el panel de Railway.

### 4. Agregar nuevo cliente

1. Crear `/clients/nuevo_cliente.json` basándote en `ferreAmiga.json`
2. Cambiar `CLIENT_ID=nuevo_cliente` en Railway
3. Redeploy

## Flujo de mensajes

```
Cliente WhatsApp
      ↓
   Webhook Flask (app.py)
      ↓
   Router → Gemini Flash clasifica intent
      ↓
   SIMPLE → Gemini Flash (respuesta rápida)
   COTIZACION → Claude Sonnet (cotización formal)
   PEDIDO → Claude Sonnet (cierre con datos de pago)
      ↓
   Respuesta → Cliente WhatsApp
```

## Modelos utilizados

| Modelo | Uso | Costo aprox |
|--------|-----|-------------|
| `gemini-2.0-flash` | Clasificación + respuestas simples | ~$0.001/1k tokens |
| `claude-sonnet-4-20250514` | Cotizaciones complejas | ~$0.015/1k tokens |

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `WA_TOKEN` | Token de acceso de Meta |
| `PHONE_NUMBER_ID` | ID del número de WhatsApp |
| `VERIFY_TOKEN` | Token para verificar el webhook |
| `ANTHROPIC_API_KEY` | API key de Anthropic (Claude) |
| `GEMINI_API_KEY` | API key de Google (Gemini) |
| `CLIENT_ID` | ID del cliente activo (`ferreAmiga`, `gallito_inn`, etc.) |
