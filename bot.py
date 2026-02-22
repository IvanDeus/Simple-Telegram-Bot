# bot.py by ivan deus
import telebot
from flask import Flask, request, jsonify
from pyngrok import ngrok
import time
import logging
import json
import os
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot with token from config
bot = telebot.TeleBot(config.BOT_TOKEN)

# Flask app for webhook
app = Flask(__name__)

# Load messages from JSON file
user_languages = {}
def load_all_messages():
    try:
        with open('messages.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error("messages.json file not found! Using default messages.")
        return {
            "en": {
                "welcome": {"text": "👋 Hello!"},
                "default_response": {"text": "Default"},
                "language_prompt": {"text": "Select language:"},
                "language_changed": {"text": "Language changed"},
                "help": {"text": "Commands:\n/start\n/language\n/help"}
            },
            "es": {
                "welcome": {"text": "👋 ¡Hola!"},
                "default_response": {"text": "Mensaje."},
                "language_prompt": {"text": "Selecciona idioma:"},
                "language_changed": {"text": "Idioma cambiado"},
                "help": {"text": "Comandos:\n/start\n/language\n/help"}
            }
        }
    except json.JSONDecodeError:
        logger.error("Invalid JSON in messages.json! Using default messages.")
        return {
            "en": {
                "welcome": {"text": "Hello!"},
                "default_response": {"text": " - "},
                "language_prompt": {"text": "Select language:"},
                "language_changed": {"text": "Eng"},
                "help": {"text": "\n/start\n/language\n/help"}
            },
            "es": {
                "welcome": {"text": "👋"},
                "default_response": {"text": " - "},
                "language_prompt": {"text": "Selecciona idioma:"},
                "language_changed": {"text": "Esp"},
                "help": {"text": "\n/start\n/language\n/help"}
            }
        }

# Load all messages
ALL_MESSAGES = load_all_messages()

def get_message(user_id, message_key):
    """Get message in user's language"""
    language = user_languages.get(user_id, 'en')  # Default to English
    return ALL_MESSAGES.get(language, {}).get(message_key, {}).get('text', f"Message not found: {message_key}")

# Webhook route
@app.route(config.WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        try:
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            logger.info("Webhook received and processed")
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return jsonify({"error": "Error processing message"}), 500
    else:
        return jsonify({"error": "Invalid content type"}), 403

# ============= MESSAGE HANDLERS =============
# IMPORTANT: Order matters! Put specific handlers FIRST, generic handlers LAST
# 1. First, handle specific commands
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    user_id = message.from_user.id
    welcome_text = get_message(user_id, 'welcome')
    bot.reply_to(message, welcome_text, parse_mode="Markdown")
    logger.info(f"Start command from user {user_id}")

# 2. Handle /help command
@bot.message_handler(commands=['help'])
def send_help(message):
    """Handle /help command"""
    user_id = message.from_user.id
    help_text = get_message(user_id, 'help')
    bot.reply_to(message, help_text, parse_mode="Markdown")
    logger.info(f"Help command from user {user_id}")

# 3. Handle /language command (specific command)
@bot.message_handler(commands=['language'])
def set_language(message):
    """Change language (example command)"""
    user_id = message.from_user.id
    markup = telebot.types.InlineKeyboardMarkup()
    btn_en = telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    btn_es = telebot.types.InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")
    markup.add(btn_en, btn_es)
    prompt_text = get_message(user_id, 'language_prompt')
    bot.reply_to(message, prompt_text, reply_markup=markup)

# 4. Handle callback queries from inline keyboards
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def language_callback(call):
    """Handle language selection"""
    user_id = call.from_user.id
    lang = call.data.split('_')[1]
    # Store user's language preference
    user_languages[user_id] = lang
    # Acknowledge the callback
    bot.answer_callback_query(call.id)
    # Update the message with confirmation in the new language
    confirmation_text = get_message(user_id, 'language_changed')
    bot.edit_message_text(
        confirmation_text,
        call.message.chat.id,
        call.message.message_id
    )
    logger.info(f"User {user_id} changed language to {lang}")

# 5. LAST - Generic handler for everything else (must be last!)
@bot.message_handler(func=lambda message: True)
def default_response(message):
    """Default response for all other messages"""
    user_id = message.from_user.id
    response_text = get_message(user_id, 'default_response')
    bot.send_message(message.chat.id, response_text)
    logger.info(f"Message from user {user_id}: {message.text}")

def setup_webhook():
    """Setup ngrok tunnel and configure Telegram webhook"""
    try:
        # Kill any existing ngrok
        ngrok.kill()
        # Set ngrok auth token from config
        ngrok.set_auth_token(config.NGROK_AUTH_TOKEN)
        # Create ngrok tunnel
        tunnel = ngrok.connect(config.LOCAL_PORT, "http")
        public_url = tunnel.public_url
        webhook_url = f"{public_url}{config.WEBHOOK_PATH}"
        logger.info(f"Ngrok tunnel established: {public_url}")
        # Remove existing webhook and set new one
        bot.remove_webhook()
        time.sleep(1)
        
        if bot.set_webhook(url=webhook_url):
            logger.info("✅ Webhook set successfully!")
            webhook_info = bot.get_webhook_info()
            logger.info(f"Webhook info: URL={webhook_info.url}, pending updates={webhook_info.pending_update_count}")
            return True
        else:
            logger.error("❌ Failed to set webhook")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error setting up webhook: {e}")
        return False

def cleanup():
    try:
        bot.remove_webhook()
        ngrok.kill()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == '__main__':
    try:
        # Setup webhook
        if setup_webhook():
            logger.info(f"Starting server on {config.LOCAL_HOST}:{config.LOCAL_PORT}")
            # Run app
            app.run(host=config.LOCAL_HOST, port=config.LOCAL_PORT, debug=False)
        else:
            logger.error("Failed to setup webhook. Exiting.")
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        cleanup()
