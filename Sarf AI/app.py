# app.py
"""
Flask application for Arabic grammar analysis.
Ensures only Arabic 2- or 3-word sentences are processed.
Includes entry point to run the server.
"""
from flask import Flask, render_template, request
import re
from sarf import analyze_sentence

app = Flask(__name__)

# Regex pattern: only Arabic letters (0621–064A) and spaces
arabic_letters_pattern = re.compile(r'^[ء-ي\s]+$')

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    if request.method == 'POST':
        sentence = request.form.get('sentence', '').strip()
        if not sentence:
            error = "❗ الرجاء إدخال جملة عربية مكوّنة من كلمتين أو ثلاث."
        else:
            # Clean diacritics and tatweel
            cleaned = re.sub(r'[ً-ْ]', '', sentence)
            cleaned = cleaned.replace('ـ', '')
            # Validate characters
            if not arabic_letters_pattern.match(cleaned):
                error = "❗ يجب إدخال أحرف عربية فقط وبدون علامات ترقيم."
            else:
                words = cleaned.split()
                if len(words) < 2 or len(words) > 3:
                    error = "❗ الجملة يجب أن تكون مكوّنة من كلمتين أو ثلاث فقط."
                else:
                    try:
                        result = analyze_sentence(cleaned)
                    except ValueError as ve:
                        error = str(ve)
                    except Exception:
                        error = "❗ حدث خطأ أثناء التحليل."
    return render_template('index.html', result=result, error=error)

# Entry point to run the Flask development server
if __name__ == '__main__':
    app.run(debug=True, port=5000)
