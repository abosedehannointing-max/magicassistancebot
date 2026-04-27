import os
import replicate
import base64
from io import BytesIO
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Get API key from environment variable (set this in Render)
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN')
if REPLICATE_API_TOKEN:
    os.environ['REPLICATE_API_TOKEN'] = REPLICATE_API_TOKEN

@app.route('/')
def home():
    return jsonify({
        'status': 'active',
        'message': 'Text-to-Image Bot is running!'
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
        
        # Check API token
        if not REPLICATE_API_TOKEN:
            return jsonify({'error': 'API token not configured'}), 500
        
        # Generate image using Stable Diffusion on Replicate
        output = replicate.run(
            "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
            input={
                "prompt": prompt,
                "negative_prompt": "ugly, blurry, low quality",
                "width": 768,
                "height": 768,
                "num_outputs": 1,
                "num_inference_steps": 30,
                "guidance_scale": 7.5
            }
        )
        
        # Return the image URL
        return jsonify({
            'success': True,
            'prompt': prompt,
            'image_url': output[0]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
