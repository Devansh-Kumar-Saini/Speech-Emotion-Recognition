from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import librosa
import numpy as np
import tensorflow as tf
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Load model and labels
from tensorflow.keras.models import load_model
model = load_model("model.h5")  # Or .keras if you used that format

# Compile if needed (especially for prediction)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

emotion_labels = ['angry', 'calm', 'disgust', 'fearful', 'happy', 'neutral', 'sad', 'surprised']

def extract_features(audio_path):
    SAMPLE_RATE = 22050
    DURATION = 4
    FIXED_LENGTH = 173
    N_MFCC = 40

    y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, duration=DURATION)
    if len(y) < SAMPLE_RATE * DURATION:
        padding = SAMPLE_RATE * DURATION - len(y)
        y = np.pad(y, (0, padding), mode='constant')

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc = (mfcc - np.mean(mfcc)) / (np.std(mfcc) + 1e-10)

    if mfcc.shape[1] < FIXED_LENGTH:
        pad_width = FIXED_LENGTH - mfcc.shape[1]
        mfcc = np.pad(mfcc, ((0, 0), (0, pad_width)), mode='constant')
    else:
        mfcc = mfcc[:, :FIXED_LENGTH]

    return mfcc.T[np.newaxis, :, :]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/technical')
def technical():
    return render_template('technical.html')






@app.route('/predict', methods=['POST'])
def predict():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    file = request.files['audio']
    filename = secure_filename(file.filename)
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)

    try:
        features = extract_features(filepath)
        prediction = model.predict(features)
        predicted_label = emotion_labels[np.argmax(prediction)]
        confidence = float(np.max(prediction))
        os.remove(filepath)
        return jsonify({'emotion': predicted_label, 'confidence': confidence})
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 