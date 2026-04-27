import os
import openai
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request
import asyncio

# Initialize Flask for webhook (required for Render)
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

# Initialize Telegram bot
telegram_bot = None
if TELEGRAM_BOT_TOKEN:
    telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    print("✅ Telegram bot token configured")
else:
    print("❌ No Telegram bot token found")

# Flask route for health check
@app.route('/')
def home():
    return {
        'status': 'active',
        'openai_configured': OPENAI_API_KEY is not None,
        'telegram_configured': TELEGRAM_BOT_TOKEN is not None
    }

@app.route('/health')
def health():
    return {'status': 'healthy'}

# Telegram bot command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎨 Hello! I'm a Text-to-Image Bot!\n\n"
        "Just send me any text description, and I'll generate an image for you!\n\n"
        "Example: 'a cute cat wearing a wizard hat'"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 How to use:\n"
        "1. Send me any text description\n"
        "2. I'll generate an image using DALL-E\n"
        "3. Wait a few seconds for the result\n\n"
        "Tips:\n"
        "- Be descriptive for better results\n"
        "- Include art style if you want (e.g., 'digital art', 'oil painting')\n"
        "- Specify details like colors, mood, lighting"
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    
    # Send "typing" indicator
    await update.message.chat.send_action(action="upload_photo")
    
    # Send initial message
    status_msg = await update.message.reply_text(f"🎨 Generating image for: '{prompt[:50]}...'\n⏳ Please wait...")
    
    try:
        # Generate image using DALL-E
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        
        image_url = response['data'][0]['url']
        
        # Delete status message
        await status_msg.delete()
        
        # Send the generated image
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🖼️ Generated for: {prompt[:200]}"
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}\n\nPlease try again with a different prompt.")

# Setup webhook for Telegram
@app.route(f'/webhook/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
async def webhook():
    if request.method == 'POST':
        update = telegram.Update.de_json(request.get_json(force=True), telegram_bot)
        # Process update
        await update_application.process_update(update)
        return 'ok'
    return 'ok'

def main():
    # Create Telegram application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    
    # Set webhook (for production on Render)
    webhook_url = f"https://magicassistancebot.onrender.com/webhook/{TELEGRAM_BOT_TOKEN}"
    application.bot.set_webhook(webhook_url)
    
    print(f"✅ Telegram bot configured with webhook: {webhook_url}")
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
