import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from classifier import classify_ticket, adjust_item
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Estados de conversación
WAITING_ADJUSTMENT = 1

# Almacenamiento temporal por chat (en memoria, se pierde al reiniciar)
chat_state = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola! Soy tu bot para dividir gastos del super.\n\n"
        "📸 Mándame una foto o captura de un ticket y lo clasifico automáticamente.\n\n"
        "Comandos disponibles:\n"
        "/ayuda — Ver todos los comandos\n"
        "/reglas — Ver las reglas de clasificación actuales"
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Cómo usar el bot:*\n\n"
        "1. Mándame una foto del ticket\n"
        "2. Te devuelvo la clasificación por producto\n"
        "3. Si algo está mal, escríbeme:\n"
        "   • `el pollo es común`\n"
        "   • `la cerveza es mía`\n"
        "   • `el gel es de ella`\n\n"
        "*Comandos:*\n"
        "/start — Inicio\n"
        "/ayuda — Esta ayuda\n"
        "/reglas — Ver reglas de clasificación\n"
        "/cancelar — Cancelar ajuste en curso",
        parse_mode="Markdown"
    )


async def reglas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📏 *Reglas de clasificación actuales:*\n\n"
        "🔴 *Solo Tomas:* carne (ternera, pollo, cerdo, jamón, chorizo, bacon, salchichas, hamburguesas...)\n\n"
        "🔵 *Solo pareja:* productos veganos/vegetarianos específicos de ella\n\n"
        "🟢 *Común:* pescado, marisco, lácteos, huevos, frutas, verduras, pan, pasta, arroz, legumbres, "
        "aceite, condimentos, bebidas (agua, zumos, refrescos), limpieza, papel higiénico\n\n"
        "❓ *Duda:* alcohol, snacks, higiene personal de marca, cualquier cosa ambigua\n\n"
        "_Puedes corregir cualquier clasificación respondiendo al mensaje del bot._",
        parse_mode="Markdown"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("🔍 Analizando el ticket, un momento...")

    # Descargar la foto en mayor resolución
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    # Clasificar con Gemini
    result = await classify_ticket(bytes(image_bytes))

    if result.get("error"):
        await update.message.reply_text(
            f"❌ No pude procesar el ticket: {result['error']}\n"
            "Intenta con una foto más nítida."
        )
        return

    # Guardar estado para posibles ajustes
    chat_state[chat_id] = {"last_result": result, "adjustments": []}

    # Formatear respuesta
    mensaje = format_result(result)
    await update.message.reply_text(mensaje, parse_mode="Markdown")

    if result.get("preguntas"):
        preguntas_txt = "\n".join(f"• {p}" for p in result["preguntas"])
        await update.message.reply_text(
            f"❓ *Necesito confirmar:*\n{preguntas_txt}\n\n"
            "_Respóndeme con algo como: 'el gel es mío' o 'la cerveza es común'_",
            parse_mode="Markdown"
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if chat_id not in chat_state or not chat_state[chat_id].get("last_result"):
        await update.message.reply_text(
            "No tengo ningún ticket en memoria. Mándame primero una foto 📸"
        )
        return

    last_result = chat_state[chat_id]["last_result"]

    # Intentar ajustar con Gemini
    adjusted = await adjust_item(last_result, text)

    if adjusted.get("error"):
        await update.message.reply_text(
            f"No entendí el ajuste: {adjusted['error']}\n"
            "Prueba con: 'el pollo es mío', 'la leche es común', 'el vino es de ella'"
        )
        return

    # Actualizar estado
    chat_state[chat_id]["last_result"] = adjusted
    chat_state[chat_id]["adjustments"].append(text)

    mensaje = format_result(adjusted)
    await update.message.reply_text(
        f"✅ Ajustado.\n\n{mensaje}",
        parse_mode="Markdown"
    )


def format_result(result: dict) -> str:
    items = result.get("items", [])
    resumen = result.get("resumen", {})

    solo_tomas = [i for i in items if i["categoria"] == "solo_tomas"]
    solo_pareja = [i for i in items if i["categoria"] == "solo_pareja"]
    comun = [i for i in items if i["categoria"] == "comun"]
    dudas = [i for i in items if i["categoria"] == "duda"]

    lines = ["🧾 *Clasificación del ticket:*\n"]

    if solo_tomas:
        lines.append("🔴 *Solo Tomas:*")
        for i in solo_tomas:
            lines.append(f"  • {i['nombre']} — {i['precio']:.2f}€")

    if solo_pareja:
        lines.append("\n🔵 *Solo pareja:*")
        for i in solo_pareja:
            lines.append(f"  • {i['nombre']} — {i['precio']:.2f}€")

    if comun:
        lines.append("\n🟢 *Común:*")
        for i in comun:
            lines.append(f"  • {i['nombre']} — {i['precio']:.2f}€")

    if dudas:
        lines.append("\n❓ *Por confirmar:*")
        for i in dudas:
            razon = f" ({i.get('razon', '')})" if i.get('razon') else ""
            lines.append(f"  • {i['nombre']} — {i['precio']:.2f}€{razon}")

    # Resumen financiero
    total = resumen.get("total_ticket", 0)
    s_tomas = resumen.get("solo_tomas", 0)
    s_pareja = resumen.get("solo_pareja", 0)
    comun_total = resumen.get("comun", 0)
    a_confirmar = resumen.get("a_confirmar", 0)

    lines.append(f"\n💰 *Resumen:*")
    lines.append(f"  Total ticket: *{total:.2f}€*")
    lines.append(f"  Común (mitad cada uno): {comun_total:.2f}€ → *{comun_total/2:.2f}€ c/u*")
    lines.append(f"  Tomas paga: *{s_tomas + comun_total/2:.2f}€*")
    lines.append(f"  Pareja paga: *{s_pareja + comun_total/2:.2f}€*")

    if a_confirmar > 0:
        lines.append(f"  ⚠️ Pendiente de confirmar: {a_confirmar:.2f}€")

    return "\n".join(lines)


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_state.pop(chat_id, None)
    await update.message.reply_text("❌ Estado limpiado. Mándame un nuevo ticket cuando quieras.")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("reglas", reglas))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot iniciado...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
