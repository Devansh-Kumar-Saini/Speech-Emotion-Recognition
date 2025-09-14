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
    print("\n=== New Prediction Request ===")
    print(f"Content-Type: {request.content_type}")
    print(f"Files received: {request.files}")
    
    # Check if the post request has the file part
    if 'audio' not in request.files:
        error_msg = "No 'audio' in request.files"
        print(f"Error: {error_msg}")
        return jsonify({'error': error_msg}), 400
        
    file = request.files['audio']
    print(f"Processing file: {file.filename}")
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        error_msg = "No file selected"
        print(f"Error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    # Check file size (max 10MB)
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)  # Reset file pointer
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if file_length > MAX_FILE_SIZE:
        error_msg = f"File too large. Max size is {MAX_FILE_SIZE/1024/1024}MB"
        print(f"Error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    # Create uploads directory if it doesn't exist
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file temporarily
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_dir, filename)
    
    try:
        print(f"Saving file to {filepath}...")
        file.save(filepath)
        print(f"File saved. Size: {os.path.getsize(filepath)} bytes")
        
        # Set a timeout for feature extraction
        print("Starting feature extraction...")
        start_time = time.time()
        
        # Process the audio file with timeout
        try:
            features = extract_features(filepath)
            print(f"Feature extraction completed in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            error_msg = f"Error during feature extraction: {str(e)}"
            print(error_msg)
            return jsonify({'error': 'Error processing audio features', 'details': str(e)}), 500
        
        # Make prediction with timeout
        print("Making prediction...")
        start_time = time.time()
        
        try:
            prediction = model.predict(features, verbose=1)
            predicted_label = emotion_labels[np.argmax(prediction)]
            confidence = float(np.max(prediction))
            print(f"Prediction completed in {time.time() - start_time:.2f} seconds")
            print(f"Result: {predicted_label} (confidence: {confidence:.2f})")
            
            result = {
                'emotion': predicted_label, 
                'confidence': confidence
            }
            print(f"Returning result: {result}")
            return jsonify(result)
            
        except Exception as e:
            error_msg = f"Error during prediction: {str(e)}"
            print(error_msg)
            return jsonify({'error': 'Error making prediction', 'details': str(e)}), 500
            
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(error_msg)
        return jsonify({'error': 'Error processing file', 'details': str(e)}), 500
        
    finally:
        # Clean up the temporary file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Temporary file removed: {filepath}")
            except Exception as e:
                print(f"Warning: Could not remove temporary file {filepath}: {str(e)}")
    
    return jsonify({'error': 'Unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True) 