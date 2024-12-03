

from flask import Flask, request, jsonify
import requests


# Flask App
app = Flask(__name__)

# LLaMA API URL and Token
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B"
API_TOKEN = "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"

# Headers for API Requests
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Session Memory
conversation_history = []

def query_llama(prompt, max_length=50, temperature=0.7):
    """
    Function to send a query to the LLaMA API.
    :param prompt: The input text for the model.
    :param max_length: Maximum length of the generated text.
    :param temperature: Randomness in text generation.
    :return: Generated text response.
    """
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": max_length,
            "temperature": temperature
        }
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        raise Exception(f"Failed to connect: {response.status_code} - {response.text}")

@app.route('/')
def home():
    return "Welcome to the Flask LLaMA app! Go to /ask to interact with LLaMA."

@app.route('/ask', methods=['GET', 'POST'])
def ask_llama():
    if request.method == 'GET':
        return "Use POST to send a prompt to LLaMA.", 405
    """
    Endpoint to send a query to LLaMA.
    """
    data = request.json
    user_input = data.get("prompt", "")
    max_length = data.get("max_length", 50)
    temperature = data.get("temperature", 0.7)

    # Include conversation history in the prompt
    full_prompt = "\n".join(conversation_history + [f"You: {user_input}"])

    try:
        response = query_llama(full_prompt, max_length=max_length, temperature=temperature)
        # Update conversation history
        conversation_history.append(f"You: {user_input}")
        conversation_history.append(f"LLaMA: {response}")
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/history', methods=['GET'])
def get_history():
    """
    Endpoint to fetch conversation history.
    """
    return jsonify({"history": conversation_history})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))