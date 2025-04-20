from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline, AutoTokenizer
import torch
import re

app = Flask(__name__)
CORS(app)

# Initialize model and tokenizer
print("Loading summarization model...")
try:
    model_name = "facebook/bart-large-cnn"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    summarizer = pipeline(
        "summarization",
        model=model_name,
        tokenizer=tokenizer,
        device=0 if torch.cuda.is_available() else -1,
        framework="pt"
    )
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {str(e)}")
    raise

def clean_text(text):
    """Clean and preprocess text"""
    # Remove extra whitespace and normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    # Ensure proper sentence endings
    text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
    return text

def split_into_chunks(text, max_length=1000):
    """Split text into chunks while preserving sentence boundaries"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(tokenizer.encode(sentence))
        if current_length + sentence_length > max_length and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def calculate_summary_length(text_length, length_param):
    """Calculate target summary length based on input length and length parameter"""
    # length_param: 1 (shortest) to 5 (longest)
    base_ratio = 0.2  # minimum ratio
    ratio_step = 0.15  # increase per length unit
    target_ratio = base_ratio + (length_param - 1) * ratio_step
    
    # Calculate target length with minimum and maximum bounds
    min_words = 30
    max_words = 150
    target_length = int(text_length * target_ratio)
    
    return max(min_words, min(target_length, max_words))

def generate_summary(text, length_param):
    """Generate summary with dynamic length parameters"""
    input_length = len(text.split())
    target_length = calculate_summary_length(input_length, length_param)
    
    try:
        summary = summarizer(
            text,
            max_length=target_length + 20,  # Allow some flexibility
            min_length=max(30, target_length - 20),
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=3,
            length_penalty=2.0
        )[0]['summary_text']
        
        return clean_text(summary)
    except Exception as e:
        print(f"Error in summarization: {str(e)}")
        return None

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No text provided'
            }), 400

        text = data['text'].strip()
        # Validate length parameter is between 1 and 5
        length = int(data.get('length', 3))  # Default to 3 (middle value)
        length = max(1, min(5, length))  # Ensure length is between 1 and 5
        format_type = data.get('format', 'general')

        # Validate input
        if len(text.split()) < 30:
            return jsonify({
                'status': 'error',
                'message': 'Text is too short to summarize. Please provide at least 30 words.'
            }), 400

        # Clean input text
        text = clean_text(text)
        
        # Split long text into chunks if necessary
        if len(tokenizer.encode(text)) > 1000:
            chunks = split_into_chunks(text)
            summaries = []
            for chunk in chunks:
                summary = generate_summary(chunk, length)
                if summary:
                    summaries.append(summary)
            
            if not summaries:
                raise Exception("Failed to generate summary for any chunk")
            
            final_summary = ' '.join(summaries)
        else:
            final_summary = generate_summary(text, length)
            if not final_summary:
                raise Exception("Failed to generate summary")

        # Format summary if bullets are requested
        if format_type == 'bullets':
            sentences = re.split(r'(?<=[.!?])\s+', final_summary.strip())
            final_summary = "\n• " + "\n• ".join(s for s in sentences if s.strip())

        word_count = len(final_summary.split())
        compression_ratio = (1 - word_count / len(text.split())) * 100

        return jsonify({
            'status': 'success',
            'summary': final_summary,
            'word_count': word_count,
            'compression_ratio': f"{compression_ratio:.1f}%"
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during summarization. Please try again.'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': True
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
