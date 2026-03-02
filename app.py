from flask import Flask, render_template, request, redirect, url_for, session, Response
import cv2
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import sys
import os

# -----------------------------
# Basic App Configuration
# -----------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------
# Import Recognizer Module
# -----------------------------

sys.path.append('modules')
from alphabet_recognizer import AlphabetRecognizer

recognizer = AlphabetRecognizer()

# -----------------------------
# Global Camera Initialization
# -----------------------------

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# -----------------------------
# Database Model
# -----------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# -----------------------------
# Video Frame Generator
# -----------------------------

def generate_frames():
    global camera

    while True:
        success, frame = camera.read()
        if not success:
            break

        try:
            predicted_letter = recognizer.predict(frame)

            cv2.putText(frame, f'Sign: {predicted_letter}', (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            height, width = frame.shape[:2]
            cv2.rectangle(frame,
                          (width // 4, height // 4),
                          (3 * width // 4, 3 * height // 4),
                          (255, 0, 0), 2)

        except Exception as e:
            cv2.putText(frame, f'Error: {str(e)}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# -----------------------------
# Routes
# -----------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists"

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            return redirect(url_for('main_app'))

        return "Invalid username or password"

    return render_template('login.html')

@app.route('/app')
def main_app():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('main_app.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# -----------------------------
# Run Server
# -----------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)