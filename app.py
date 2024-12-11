from flask import Flask, request, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
import random
import string
import os

app = Flask(__name__)

# Load database URL from environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://username:password@localhost/links_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Load API token from environment variable
API_TOKEN = os.getenv('API_TOKEN', 'default_api_token')

db = SQLAlchemy(app)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(2048), nullable=False)
    short_url = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(2048), nullable=True)

def generate_short_url():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=6))

def require_bearer_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization header with Bearer token is required'}), 401
    token = auth_header.split(' ')[1]
    if token != API_TOKEN:
        return jsonify({'error': 'Invalid API token'}), 405

@app.route('/')
def index():
    links = Link.query.all()
    return render_template('index.html', links=links)

@app.route('/links', methods=['POST'])
def create_link():
    auth_check = require_bearer_token()
    if auth_check:
        return auth_check

    data = request.json
    long_url = data.get('long_url')
    title = data.get('title')
    image_url = data.get('image_url')

    if not long_url:
        return jsonify({'error': 'Long URL is required'}), 400

    short_url = generate_short_url()
    while Link.query.filter_by(short_url=short_url).first():
        short_url = generate_short_url()

    new_link = Link(long_url=long_url, short_url=short_url, title=title, image_url=image_url)
    db.session.add(new_link)
    db.session.commit()

    return jsonify({'long_url': long_url, 'short_url': short_url, 'title': title, 'image_url': image_url})

@app.route('/<short_url>')
def redirect_to_long_url(short_url):
    link = Link.query.filter_by(short_url=short_url).first()
    if link:
        return redirect(link.long_url)
    return jsonify({'error': 'URL not found'}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
