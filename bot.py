import os
import openai
from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Get tokens from environment variables
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Initialize OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    print("✅ OpenAI API key configured")
else:
    print("❌ No OpenAI API key found")

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

@app.route('/')
def home():
    return jsonify({
        'status': 'active',
        'openai_configured': OPENAI_API_KEY is not None,
        'telegram_configured': TELEGRAM_BOT_TOKEN is not None
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route(f'/webhook/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        # Get update from Telegram
        update = request.get_json()
        
        if update and 'message' in update:
            chat_id = update['message']['chat']['id']
            message_text = update['message'].get('text', '')
            
            # Handle commands
            if message_text == '/start':
                send_telegram_message(chat_id, 
                    "🎨 Hello! I'm a Text-to-Image Bot!\n\n"
                    "Just send me any text description, and I'll generate an image for you!\n\n"
                    "Example: 'a cute cat wearing a wizard hat'")
                return 'ok'
            
            elif message_text == '/help':
                send_telegram_message(chat_id,
                    "📝 How to use:\n"
                    "Send me any text description\n\n"
                    "Tips:\n"
                    "- Be descriptive for better results\n"
                    "- Include art style (e.g., 'digital art')\n"
                    "- Specify colors, mood, lighting")
                return 'ok'
            
            # Generate image for any other text
            else:
                # Send typing indicator
                send_telegram_action(chat_id, 'upload_photo')
                
                # Send initial message
                send_telegram_message(chat_id, f"🎨 Generating image for: '{message_text[:50]}...'\n⏳ Please wait...")
                
                try:
                    # Generate image using DALL-E
                    response = openai.Image.create(
                        prompt=message_text,
                        n=1,
                        size="1024x1024"
                    )
                    
                    image_url = response['data'][0]['url']
                    
                    # Send the generated image
                    send_telegram_photo(chat_id, image_url, f"🖼️ Generated for: {message_text[:200]}")
                    
                except Exception as e:
                    send_telegram_message(chat_id, f"❌ Error: {str(e)}\n\nPlease try again with a different prompt.")
        
        return 'ok'
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'error', 500

def send_telegram_message(chat_id, text):
    """Send a text message via Telegram"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {'chat_id': chat_id, 'text': text}
    try:
        requests.post(url, json=data)
    except Exception as e:
        print(f"Error sending message: {e}")

def send_telegram_action(chat_id, action):
    """Send a chat action (typing, upload_photo, etc.)"""
    url = f"{TELEGRAM_API_URL}/sendChatAction"
    data = {'chat_id': chat_id, 'action': action}
    try:
        requests.post(url, json=data)
    except Exception as e:
        print(f"Error sending action: {e}")

def send_telegram_photo(chat_id, photo_url, caption):
    """Send a photo via Telegram"""
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    data = {'chat_id': chat_id, 'photo': photo_url, 'caption': caption}
    try:
        requests.post(url, json=data)
    except Exception as e:
        print(f"Error sending photo: {e}")

# Set webhook when the server starts
def set_webhook():
    if TELEGRAM_BOT_TOKEN:
        webhook_url = f"https://magicassistancebot.onrender.com/webhook/{TELEGRAM_BOT_TOKEN}"
        url = f"{TELEGRAM_API_URL}/setWebhook"
        response = requests.post(url, json={'url': webhook_url})
        if response.status_code == 200:
            print(f"✅ Webhook set to: {webhook_url}")
        else:
            print(f"❌ Failed to set webhook: {response.text}")

if __name__ == '__main__':
    # Set webhook on startup
    set_webhook()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
