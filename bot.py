import os
from openai import OpenAI
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def home():
    return jsonify({
        'status': 'active',
        'message': 'Text-to-Image Bot with DALL-E is running!'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt parameter'}), 400
        
        prompt = data['prompt']
        size = data.get('size', '1024x1024')  # Options: 256x256, 512x512, 1024x1024
        quality = data.get('quality', 'standard')  # Options: standard, hd
        n = min(data.get('n', 1), 5)  # Number of images (max 5 for DALL-E 3)
        
        # Check API key
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        # Generate image using DALL-E
        response = client.images.generate(
            model="dall-e-3",  # or "dall-e-2" for cheaper/faster
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )
        
        # Extract image URLs
        image_urls = [image.url for image in response.data]
        
        return jsonify({
            'success': True,
            'prompt': prompt,
            'image_urls': image_urls,
            'count': len(image_urls)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Simple text-to-image endpoint
@app.route('/generate/simple', methods=['POST'])
def generate_simple():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'error': 'Missing prompt'}), 400
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        return jsonify({
            'image_url': response.data[0].url,
            'prompt': prompt
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
