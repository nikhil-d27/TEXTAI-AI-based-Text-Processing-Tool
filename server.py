from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import random
import string
import re
import os
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer

app = Flask(__name__)
CORS(app)

CSV_PATH = 'Parapharse.csv'
if not os.path.exists(CSV_PATH):
    print(f"Error: {CSV_PATH} not found in {os.getcwd()}")
    print("Available files:", os.listdir())

# Load and process the CSV data
def load_paraphrase_dict():
    try:
        print("Attempting to load CSV file...")
        if not os.path.exists(CSV_PATH):
            print(f"Error: {CSV_PATH} not found!")
            return {}

        df = pd.read_csv(CSV_PATH)
        print(f"CSV loaded successfully. Shape: {df.shape}")
        paraphrase_dict = {}

        for _, row in df.iterrows():
            if pd.isna(row['Column1']) or pd.isna(row['Column2']):
                continue

            original = str(row['Column1']).lower().strip()
            alternatives = str(row['Column2']).strip()

            # Split by both commas and semicolons
            alt_list = []
            for part in alternatives.replace(';', ',').split(','):
                part = part.strip()
                if part and part.lower() != original:
                    alt_list.append(part)

            alt_list = list(set(alt_list))  # remove duplicates

            if alt_list:
                paraphrase_dict[original] = alt_list

        print(f"Loaded {len(paraphrase_dict)} entries.")
        sample = list(paraphrase_dict.items())[:5]
        for word, alts in sample:
            print(f"{word}: {alts}")
        return paraphrase_dict

    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
        return {}

PARAPHRASE_DICT = load_paraphrase_dict()

def preserve_case(original_word, new_word):
    if original_word.isupper():
        return new_word.upper()
    elif original_word.istitle():
        return new_word.capitalize()
    return new_word.lower()

def paraphrase_text(text):
    """Paraphrase the input text while preserving structure"""
    if not text.strip():
        return "", 0, []
    
    try:
        print(f"Input text: {text}")
        words_changed = 0
        changed_words = []  # Track changed words and their replacements
        
        def replace_word(match):
            nonlocal words_changed
            original_word = match.group(0)
            lower_word = original_word.lower()
            
            if lower_word in PARAPHRASE_DICT:
                replacement = random.choice(PARAPHRASE_DICT[lower_word])
                if replacement.lower() != lower_word:
                    words_changed += 1
                    changed_words.append({
                        'original': original_word,
                        'replacement': preserve_case(original_word, replacement)
                    })
                    print(f"Changed {original_word} to {replacement}")
                return preserve_case(original_word, replacement)
            return original_word

        pattern = r'\b(' + '|'.join(re.escape(word) for word in PARAPHRASE_DICT.keys()) + r')\b'
        result = re.sub(pattern, replace_word, text, flags=re.IGNORECASE)
        
        print(f"Final result: {result}")
        print(f"Words changed: {words_changed}")
        return result.strip(), words_changed, changed_words

    except Exception as e:
        print(f"Error in paraphrasing: {str(e)}")
        return text, 0, []

@app.route('/api/paraphrase', methods=['POST'])
def paraphrase():
    try:
        if not PARAPHRASE_DICT:
            return jsonify({
                'status': 'error',
                'message': 'Paraphrase dictionary not loaded properly'
            }), 500

        data = request.json
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No text provided'
            }), 400

        input_text = data['text'].strip()

        if len(input_text.split()) < 3:
            return jsonify({
                'status': 'error',
                'message': 'Please provide at least 3 words for paraphrasing.'
            }), 400

        if len(input_text.split()) > 1000:
            return jsonify({
                'status': 'error',
                'message': 'Text is too long. Please limit to 1000 words.'
            }), 400

        paraphrased_text, words_changed, changed_words = paraphrase_text(input_text)

        original_words = len(input_text.split())
        similarity_score = ((original_words - words_changed) / original_words) * 100

        return jsonify({
            'status': 'success',
            'result': paraphrased_text,
            'changed_words': changed_words,
            'statistics': {
                'original_word_count': original_words,
                'words_changed': words_changed,
                'similarity_score': f"{similarity_score:.1f}%",
                'change_ratio': f"{(words_changed / original_words * 100):.1f}%"
            }
        })

    except Exception as e:
        print(f"Error in /api/paraphrase: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during paraphrasing.'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'dictionary_loaded': len(PARAPHRASE_DICT) > 0,
        'words_available': len(PARAPHRASE_DICT)
    })

if __name__ == '__main__':
    try:
        nltk.download('punkt', quiet=True)
    except:
        print("Error downloading NLTK data")
    app.run(host='0.0.0.0', port=5505, debug=True)
