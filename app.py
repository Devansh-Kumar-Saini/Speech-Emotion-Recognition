from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import librosa
import numpy as np
import tensorflow as tf
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Model
from tensorflow.keras.models import load_model
model = load_model("model.h5")  


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
    print("Received request to /predict endpoint")  # Debug log
    
    # Check if the post request has the file part
    if 'audio' not in request.files:
        print("No 'audio' in request.files")  # Debug log
        return jsonify({'error': 'No audio file provided'}), 400
        
    file = request.files['audio']
    print(f"Received file: {file.filename}")  # Debug log
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        print("No selected file")  # Debug log
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = 'uploads'
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save the file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            print(f"File saved to {filepath}")  # Debug log
            
            # Process the audio file
            print("Extracting features...")  # Debug log
            features = extract_features(filepath)
            print("Making prediction...")  # Debug log
            prediction = model.predict(features)
            predicted_label = emotion_labels[np.argmax(prediction)]
            confidence = float(np.max(prediction))
            
            # Clean up the temporary file
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Temporary file {filepath} removed")  # Debug log
                
            print(f"Prediction successful: {predicted_label} (confidence: {confidence})")  # Debug log
            return jsonify({
                'emotion': predicted_label, 
                'confidence': confidence
            })
            
        except Exception as e:
            print(f"Error during prediction: {str(e)}")  # Debug log
            # Clean up in case of error
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
                print(f"Removed temporary file after error: {filepath}")  # Debug log
            return jsonify({
                'error': 'Error processing audio file',
                'details': str(e)
            }), 500
    
    return jsonify({'error': 'Invalid file'}), 400

if __name__ == '__main__':
    app.run(debug=True) 