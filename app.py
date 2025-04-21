"""
to do list:

done:
- fix 2sv
- secure login
- sharex upload system
- raw cdn file and cool little file page
- progress bar for storage usage
- discord embeds

to do:
- safe approval system within the website
- profile page
- settings page
- monetization? maybe??? (buy more storage. start w shitty little 2tb ssd)
- custom embed coloring
"""
# something you guys SHOULD HOPEFULLY NEVER SEE. if you do i failed. i'm dumb.
from sensitivedetails import EMAIL_ADDRESS, EMAIL_PASSWORD

from flask import Flask, request, render_template, send_from_directory, jsonify, url_for, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os, uuid, smtplib, random
from email.message import EmailMessage
from moviepy.editor import VideoFileClip
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config['SECRET_KEY'] = 'as9ud90asud09ahsd9h0sad9h0as9dh0sa90das90hd90ahsd90hasd90hasd90h'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    api_key = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    total_file_size = db.Column(db.BigInteger, default=0)
    approved = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "100 per hour"]
)



def send_2sv_email(email, code):
    msg = EmailMessage()
    msg['Subject'] = '2-Step Verification Code'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email

    html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" type="text/css" hs-webfonts="true" href="https://fonts.googleapis.com/css?family=Lato|Lato:i,b,bi">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style type="text/css">
              h1{{font-size:56px; margin:0; padding:0;}}
              h2{{font-size:28px; font-weight:900; margin:0; padding:0;}}
              p{{font-weight:100; margin:0; padding:0;}}
              td{{vertical-align:top;}}
              .email-container{{margin:auto; width:600px; background-color:#fff;}}
            </style>
        </head>
        <body bgcolor="#F5F8FA" style="width: 100%; font-family: Impact, Arial, sans-serif; font-size:18px; margin:0; padding:0;">
        <div class="email-container">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <td bgcolor="#0000FF" align="center" style="color: white; padding: 20px;">
                        <h1 style="font-family: Impact, Arial, sans-serif; margin:0; padding:0;">2-Step Verification</h1>
                    </td>
                </tr>
            </table>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="padding: 30px;">
                <tr>
                    <td align="center">
                        <h2 style="font-family: Impact, Arial, sans-serif; margin:0; padding:0;">Your 2SV code is:</h2>
                        <h1 style="font-family: Impact, Arial, sans-serif; margin:0; padding:0;">{code}</h1>
                    </td>
                </tr>
            </table>
        </div>
        </body>
        </html>
    '''

    msg.set_content(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

@app.route('/')
@login_required
def index():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
    if not os.path.exists(user_folder):
        files = []
    else:
        files = os.listdir(user_folder)
    
    if current_user.id == 1:
        max_size = 25 * 1024 * 1024 * 1024
    elif current_user.id != 1:
        max_size = 2 * 1024 * 1024 * 1024
    used_size = current_user.total_file_size
    used_percentage = (used_size / max_size) * 100

    return render_template('index.html', api_key=current_user.api_key, files=files, used_size=used_size, max_size=max_size, used_percentage=used_percentage, user_id=current_user.id, username=current_user.username)

@app.route('/static/<path:filename>')
def static_files(filename: str):
    return send_from_directory('static', filename)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        if password == confirm:
            if existing_user:
                flash('Username already exists.', 'danger')
            elif existing_email:
                flash('Email address already exists.', 'danger')
            else:
                hashed_password = generate_password_hash(password, method='pbkdf2')
                new_user = User(username=username, email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()

                user = User.query.filter_by(username=username).first()
                if user and user.approved:

                    code = f"{random.randint(0, 999999):06d}"
                    session['2sv_code'] = code
                    session['user_id'] = new_user.id
                    send_2sv_email(email, code)

                    return redirect(url_for('verify_2sv'))
            flash('Signup failed. Please check your input.', 'danger')
        else:
            flash('Signup failed. Passwords do not match.', 'danger')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if user.approved:
                code = f"{random.randint(0, 999999):06d}"
                session['2sv_code'] = code
                session['user_id'] = user.id
                send_2sv_email(user.email, code)

                return redirect(url_for('verify_2sv'))
            else:
                flash('Account not approved yet. Please wait for approval.', 'danger')
        flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html')

@app.route('/2sv', methods=['GET', 'POST'])
def verify_2sv():
    if '2sv_code' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = ''.join([request.form[f'digit{i}'] for i in range(1, 7)])
        if code == session['2sv_code']:
            user = User.query.get(session['user_id'])
            login_user(user)
            session.pop('2sv_code', None)
            return redirect(url_for('index'))
        else:
            flash('Invalid 2SV code. Please try again.', 'danger')

    return render_template('2sv.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@limiter.limit('5 per minute')
def upload_file():
    api_key = request.headers.get('key')
    if not api_key:
        return jsonify({'error': 'Missing API key'}), 403

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user.id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    file_path = os.path.join(user_folder, filename)

    file_size = len(file.read())
    file.seek(0)

    MAX_USER_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024
    if user.total_file_size + file_size > MAX_USER_UPLOAD_SIZE:
        return jsonify({'error': 'Upload limit exceeded'}), 403

    file.save(file_path)
    user.total_file_size += file_size
    db.session.commit()

    file_url = url_for('file_page', user_id=user.id, filename=filename, _external=True)
    return jsonify({'success': 'File uploaded successfully', 'file_url': file_url}), 201

@app.route('/file/<int:user_id>/<filename>')
def file_page(user_id, filename):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
    file_path = os.path.join(user_folder, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    file_url = url_for('uploaded_file', user_id=user_id, filename=filename, _external=True)

    try:
        video = VideoFileClip(file_path)
        width, height = video.size
    except Exception as e:
        print(f"Error getting video dimensions: {e}, trying image.")
        try: 
            im = Image.open(file_path)
            width, height = im.size
        except Exception as e:
            print(f"Error getting both image and video dimensions: {e}")

    return render_template('file.html', filename=filename, user_id=user_id, username=user.username, file_url=file_url, width=width, height=height)

@app.route('/uploads/<int:user_id>/<filename>')
def uploaded_file(user_id, filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
    return send_from_directory(user_folder, filename)

@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
    file_path = os.path.join(user_folder, filename)

    if os.path.exists(file_path):
        if os.path.commonpath([file_path, user_folder]) == user_folder:
            file_size = os.path.getsize(file_path)
            os.remove(file_path)
            current_user.total_file_size -= file_size
            db.session.commit()
            flash('File deleted successfully.', 'success')
        else:
            flash('Unauthorized access.', 'danger')
    else:
        flash('File not found.', 'danger')

    return redirect(url_for('index'))

@app.route('/reset_api_key', methods=['POST'])
@login_required
def reset_api_key():
    new_api_key = str(uuid.uuid4())
    current_user.api_key = new_api_key
    db.session.commit()
    flash('API key has been reset.', 'success')
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large():
    return jsonify({'error': 'The uploaded file exceeds the allowed size limit.'}), 413

@app.errorhandler(404)
def not_found():
    return jsonify({'error': 'The requested resource could not be found.'}), 404

@app.errorhandler(429)
def too_many_requests():
    return jsonify({'error': 'You have made too many requests. Please try again later.'}), 429

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=True)