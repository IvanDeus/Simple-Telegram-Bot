import telebot
from flask import Flask, request, jsonify
from pyngrok import ngrok
import time
import logging
import json
import os
# Import configuration
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot with token from config
bot = telebot.TeleBot(config.BOT_TOKEN)

# Flask app for webhook
app = Flask(__name__)

# Load messages from JSON file
def load_messages(language='en'):
    """Load messages from JSON file"""
    try:
        with open('messages.json', 'r', encoding='utf-8') as file:
            messages = json.load(file)
            
        # Check if multi-language structure is used
        if language in messages:
            return messages[language]
        return messages  # Return as-is for simple structure
        
    except FileNotFoundError:
        logger.error("messages.json file not found! Using default messages.")
        return {
            "welcome": {"text": "👋 Hello! Welcome to this bot."},
            "default_response": {"text": "📨 Default response."},
            "errors": {"processing_error": "Error processing message."}
        }
    except json.JSONDecodeError:
        logger.error("Invalid JSON in messages.json! Using default messages.")
        return {
            "welcome": {"text": "👋 Hello! Welcome to this bot."},
            "default_response": {"text": "📨 Default response."},
            "errors": {"processing_error": "Error processing message."}
        }

# Load messages
MESSAGES = load_messages()  # For simple structure
# For multi-language: MESSAGES = load_messages('en')

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
            error_message = MESSAGES.get('errors', {}).get('processing_error', 'Error processing message')
            return jsonify({"error": error_message}), 500
    else:
        return jsonify({"error": "Invalid content type"}), 403


# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy", 
        "webhook_url": bot.get_webhook_info().url
    }), 200


# Message handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    welcome_text = MESSAGES.get('welcome', {}).get('text', 'Welcome!')
    bot.reply_to(message, welcome_text)
    logger.info(f"Start command from user {message.from_user.id}")

@bot.message_handler(func=lambda message: True)
def default_response(message):
    """Default response for all other messages"""
    response_text = MESSAGES.get('default_response', {}).get('text', 'Default response')
    bot.send_message(message.from_user.id, response_text)
    logger.info(f"Message from user {message.from_user.id}: {message.text}")

# Optional: Handler with language selection (for multi-language support)
@bot.message_handler(commands=['language'])
def set_language(message):
    """Change language (example command)"""
    markup = telebot.types.InlineKeyboardMarkup()
    btn_en = telebot.types.InlineKeyboardButton("English", callback_data="lang_en")
    btn_es = telebot.types.InlineKeyboardButton("Español", callback_data="lang_es")
    markup.add(btn_en, btn_es)
    bot.reply_to(message, "Select language:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def language_callback(call):
    """Handle language selection"""
    lang = call.data.split('_')[1]
    # You would need to store user language preference in a database
    # For now, just acknowledge
    bot.answer_callback_query(call.id, f"Language set to {lang}")
    bot.edit_message_text(
        f"Language changed to {lang}",
        call.message.chat.id,
        call.message.message_id
    )

def setup_webhook():
    """Setup ngrok tunnel and configure Telegram webhook"""
    try:
        # Kill any existing ngrok processes
        ngrok.kill()
        
        # Set ngrok auth token from config
        ngrok.set_auth_token(config.NGROK_AUTH_TOKEN)
        
        # Create ngrok tunnel to local port
        tunnel = ngrok.connect(config.LOCAL_PORT, "http")
        
        # Get the public URL
        public_url = tunnel.public_url
        webhook_url = f"{public_url}{config.WEBHOOK_PATH}"
        
        logger.info(f"Ngrok tunnel established: {public_url}")
        logger.info(f"Setting webhook to: {webhook_url}")
        
        # Remove existing webhook and set new one
        bot.remove_webhook()
        time.sleep(1)
        
        if bot.set_webhook(url=webhook_url):
            logger.info("✅ Webhook set successfully!")
            webhook_info = bot.get_webhook_info()
            logger.info(f"📊 Webhook info: URL={webhook_info.url}, pending updates={webhook_info.pending_update_count}")
            return True
        else:
            error_msg = MESSAGES.get('errors', {}).get('webhook_setup', 'Failed to set webhook')
            logger.error(f"❌ {error_msg}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error setting up webhook: {e}")
        return False


def cleanup():
    """Cleanup resources on shutdown"""
    try:
        bot.remove_webhook()
        ngrok.kill()
        logger.info("🧹 Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == '__main__':
    try:
        # Setup webhook
        if setup_webhook():
            logger.info(f"Starting Flask server on {config.LOCAL_HOST}:{config.LOCAL_PORT}")
            logger.info(f"Health check available at: http://localhost:{config.LOCAL_PORT}/health")
            logger.info("Press Ctrl+C to stop")
            
            # Run Flask app
            app.run(host=config.LOCAL_HOST, port=config.LOCAL_PORT, debug=False)
        else:
            logger.error("Failed to setup webhook. Exiting.")
            
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
    finally:
        cleanup()
