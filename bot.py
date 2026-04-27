import os
import openai
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Initialize OpenAI correctly
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    print("✅ OpenAI API key configured")
else:
    print("❌ No OpenAI API key found")

@app.route('/')
def home():
    return jsonify({
        'status': 'active',
        'message': 'Text-to-Image Bot with DALL-E is running!',
        'api_configured': OPENAI_API_KEY is not None
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'api_ready': OPENAI_API_KEY is not None
    })

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt parameter'}), 400
        
        prompt = data['prompt']
        size = data.get('size', '1024x1024')
        n = min(data.get('n', 1), 5)
        
        print(f"🎨 Generating image for: {prompt}")
        
        # Generate image using OpenAI
        response = openai.Image.create(
            prompt=prompt,
            n=n,
            size=size
        )
        
        image_urls = [image['url'] for image in response['data']]
        
        print(f"✅ Generated {len(image_urls)} image(s)")
        
        return jsonify({
            'success': True,
            'prompt': prompt,
            'image_urls': image_urls,
            'count': len(image_urls)
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate/simple', methods=['POST'])
def generate_simple():
    try:
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'error': 'Missing prompt'}), 400
        
        print(f"🎨 Generating single image for: {prompt}")
        
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        
        print(f"✅ Image generated successfully")
        
        return jsonify({
            'image_url': response['data'][0]['url'],
            'prompt': prompt
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
