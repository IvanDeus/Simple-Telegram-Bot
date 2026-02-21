import telebot
from flask import Flask, request, jsonify
from pyngrok import ngrok
import time
import logging

# Import configuration
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot with token from config
bot = telebot.TeleBot(config.BOT_TOKEN)

# Flask app for webhook
app = Flask(__name__)

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
            return jsonify({"error": str(e)}), 500
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
    welcome_text = (
        "👋 Hello! Welcome to this bot.\n\n"
        "I'm running via webhook and ngrok!\n"
        "Send me any message and I'll respond."
    )
    bot.reply_to(message, welcome_text)
    logger.info(f"Start command from user {message.from_user.id}")

@bot.message_handler(func=lambda message: True)
def default_response(message):
    """Default response for all other messages"""
    response_text = f"📨 You sent: {message.text}\n\n🤖 This is a simple default message for all other inputs."
    bot.reply_to(message, response_text)
    logger.info(f"Message from user {message.from_user.id}: {message.text}")

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
            logger.info(f"Webhook info: URL={webhook_info.url}, pending updates={webhook_info.pending_update_count}")
            return True
        else:
            logger.error("❌ Failed to set webhook")
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
