# 🧾 Ticket Bot — Divisor de gastos del supermercado

Bot de Telegram que analiza fotos de tickets y divide los gastos entre tú y tu pareja.

## Stack
- **Python** + python-telegram-bot
- **Google Gemini 1.5 Flash** para OCR y clasificación (gratis)
- **Railway** para hosting (gratis)

## Estructura
```
ticket-bot/
├── bot.py          # Lógica del bot de Telegram
├── classifier.py   # Llamadas a Gemini
├── rules.py        # ⭐ REGLAS DE CLASIFICACIÓN (edita esto)
├── requirements.txt
├── .env.example    # Plantilla de variables de entorno
└── .gitignore
```

## Setup local

```bash
# 1. Clona el repo
git clone https://github.com/TU_USUARIO/ticket-bot
cd ticket-bot

# 2. Instala dependencias
pip install -r requirements.txt

# 3. Configura variables de entorno
cp .env.example .env
# Edita .env con tu TELEGRAM_TOKEN y GEMINI_API_KEY

# 4. Arranca el bot
python bot.py
```

## Deploy en Railway

1. Ve a railway.app → New Project → Deploy from GitHub repo
2. Selecciona este repositorio
3. En **Variables** añade:
   - `TELEGRAM_TOKEN` = tu token de BotFather
   - `GEMINI_API_KEY` = tu key de Google AI Studio
4. En **Settings → Start Command** pon: `python bot.py`
5. Deploy ✅

## Personalizar reglas

Edita `rules.py`:
- `SOLO_TOMAS` — productos que solo come Tomas
- `SOLO_PAREJA` — productos exclusivos de la pareja
- `SIEMPRE_COMUN` — productos que siempre se dividen al 50%
- `SIEMPRE_DUDA` — productos que siempre requieren confirmación

## Comandos del bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Bienvenida |
| `/ayuda` | Instrucciones de uso |
| `/reglas` | Ver reglas activas |
| `/cancelar` | Limpiar estado |

## Cómo corregir una clasificación

Después de mandar un ticket, escribe en lenguaje natural:
- `el pollo es común`
- `la cerveza es mía`
- `el gel es de ella`
- `el vino lo compartimos`
