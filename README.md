# Simple-Telegram-Bot
Simple Telegram Bot With Ngrok Webhook Setup
# Telegram Bot with Webhook and Ngrok

A simple Telegram bot with multilanguage support that uses webhooks instead of polling, with ngrok for local development and testing. The bot responds to `/start` and `/help` commands and provides a default response for all other messages.

## Features

- Webhook-based Telegram bot using Flask
- Ngrok integration for exposing local server to the internet
- Separate configuration file for easy setup
- Clean shutdown and resource cleanup
- Comprehensive logging

## Prerequisites

- Python 3.7 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Ngrok account (free tier works fine) and auth token

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/IvanDeus/Simple-Telegram-Bot.git
cd Simple-Telegram-Bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up configuration**

Copy the example config file:
```bash
cp config.py.example config.py
```

Edit `config.py` and add your tokens:
```python
# Telegram Bot Token (get from @BotFather)
BOT_TOKEN = "your_telegram_bot_token_here"

# Ngrok Auth Token (get from https://dashboard.ngrok.com/auth)
NGROK_AUTH_TOKEN = "your_ngrok_auth_token_here"

# Local server configuration (default values work fine)
LOCAL_HOST = "0.0.0.0"
LOCAL_PORT = 7777
WEBHOOK_PATH = "/webhook"
```

## 📡 Usage

1. **Run the bot**
```bash
python bot.py
```

2. **Expected output**
```
INFO:__main__:Ngrok tunnel established: https://xxxx-xx-xxx-xxx.ngrok-free.app
INFO:__main__:Setting webhook to: https://xxxx-xx-xxx-xxx.ngrok-free.app/webhook
INFO:__main__:Webhook set successfully!
INFO:__main__:Starting Flask server on 127.0.0.1:7777
```

3. **Test your bot**
- Open Telegram and find your bot
- Send `/start` and `/help` commands
- Send any other message
- The bot should respond accordingly

## 📁 Project Structure

```
Simple-Telegram-Bot/
├── bot.py                 # Main bot application
├── config.py              # Configuration file (create from example)
├── config.py.example      # Example configuration template
├── messages.json          # All bot messages in several languages 
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── .gitignore            # Git ignore rules
```

## 🔧 How It Works

1. **Flask Server**: Runs locally on port 7777, handling webhook requests at `/webhook`
2. **Ngrok Tunnel**: Creates a secure public URL that forwards to your local server
3. **Telegram Webhook**: Configures Telegram to send updates to your ngrok URL
4. **Message Handlers**:
   - `/start` command: Returns a welcome message
   - All other messages: Returns a simple default response

## 🧹 Cleanup

The bot automatically:
- Removes the webhook on shutdown
- Kills ngrok processes
- Performs proper resource cleanup

## ⚠️ Important Notes

- The ngrok URL changes each time you restart the bot (free tier)
- Keep the script running to maintain the webhook
- The bot will stop responding if you close the terminal
- For production, consider using a VPS instead of ngrok

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 
2026 [ ivan deus ]
