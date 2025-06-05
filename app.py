from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import os
import json
import random
import time

app = Flask(__name__)

# Konfiguration laden
config_name = os.environ.get('FLASK_ENV', 'development')
if config_name == 'production':
    from config import ProductionConfig
    app.config.from_object(ProductionConfig)
else:
    from config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)

# Fallback für direkte Konfiguration (falls config.py nicht funktioniert)
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
if not app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS'):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Datei-Upload-Konfiguration
UPLOAD_FOLDER = 'static/uploads/profile_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB in Bytes

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Upload-Ordner erstellen falls nicht vorhanden
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# E-Mail-Konfiguration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lars03203@gmail.com'  # Ändern Sie dies
app.config['MAIL_PASSWORD'] = 'tojzwcafknwdnejo'  # Gmail App-Passwort
app.config['MAIL_DEFAULT_SENDER'] = 'lars03203@gmail.com'

db = SQLAlchemy(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Benutzer-Modell für die Datenbank
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(120), nullable=True)  # Pfad zum Profilbild
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_confirmation_token(self):
        return serializer.dumps(self.email, salt='email-confirm')
    
    def confirm_token(self, token, expiration=3600):
        try:
            email = serializer.loads(token, salt='email-confirm', max_age=expiration)
        except:
            return False
        if email != self.email:
            return False
        self.email_confirmed = True
        return True
    
    def __repr__(self):
        return f'<User {self.username}>'

# Mathe-Quiz-Modell
class MathQuiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # JSON-String mit Aufgaben
    answers = db.Column(db.Text, nullable=False)    # JSON-String mit Antworten
    score = db.Column(db.Integer, nullable=False)   # Punktzahl (0-5)
    total_questions = db.Column(db.Integer, default=5)
    difficulty = db.Column(db.String(20), default='mixed')  # Schwierigkeitsgrad
    time_taken = db.Column(db.Float, nullable=True)  # Zeit in Sekunden
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehung zum User
    user = db.relationship('User', backref=db.backref('quiz_attempts', lazy=True))
    
    def calculate_points(self):
        """Berechnet Punkte basierend auf Score, Schwierigkeit und Zeit"""
        base_points = self.score * 100  # 100 Punkte pro richtige Antwort
        
        # Schwierigkeits-Multiplikator
        difficulty_multiplier = {
            'easy': 1.0,
            'medium': 1.5,
            'hard': 2.0,
            'mixed': 1.8
        }
        
        points = base_points * difficulty_multiplier.get(self.difficulty, 1.0)
        
        # Zeit-Bonus (wenn Zeit unter 30 Sekunden pro Frage)
        if self.time_taken:
            avg_time_per_question = self.time_taken / self.total_questions
            if avg_time_per_question < 30:  # Unter 30 Sekunden pro Frage
                time_bonus = max(0, (30 - avg_time_per_question) * 10)
                points += time_bonus
        
        # Perfekt-Bonus (alle richtig)
        if self.score == self.total_questions:
            points *= 1.2
        
        return int(points)
    
    def __repr__(self):
        return f'<MathQuiz {self.id} by User {self.user_id}>'

# Leaderboard-Modell für beste Ergebnisse
class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_points = db.Column(db.Integer, default=0)
    total_quizzes = db.Column(db.Integer, default=0)
    best_score = db.Column(db.Integer, default=0)
    perfect_scores = db.Column(db.Integer, default=0)  # Anzahl perfekter Scores (5/5)
    average_score = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehung zum User
    user = db.relationship('User', backref=db.backref('leaderboard_entry', uselist=False))
    
    def update_stats(self):
        """Aktualisiert die Leaderboard-Statistiken basierend auf allen Quiz-Versuchen"""
        user_quizzes = MathQuiz.query.filter_by(user_id=self.user_id).all()
        
        if not user_quizzes:
            return
        
        self.total_quizzes = len(user_quizzes)
        self.total_points = sum(quiz.calculate_points() for quiz in user_quizzes)
        self.best_score = max(quiz.score for quiz in user_quizzes)
        self.perfect_scores = sum(1 for quiz in user_quizzes if quiz.score == quiz.total_questions)
        self.average_score = sum(quiz.score for quiz in user_quizzes) / len(user_quizzes)
        self.last_updated = datetime.utcnow()
        
        db.session.commit()
    
    def get_rank(self):
        """Ermittelt den aktuellen Rang des Users"""
        better_entries = Leaderboard.query.filter(Leaderboard.total_points > self.total_points).count()
        return better_entries + 1
    
    def __repr__(self):
        return f'<Leaderboard User {self.user_id}: {self.total_points} points>'

# Hilfsfunktionen für Datei-Upload
def allowed_file(filename):
    """Prüft ob die Dateiendung erlaubt ist"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_file(file):
    """Validiert Bilddatei (Format und Größe)"""
    if not file or file.filename == '':
        return False, "Keine Datei ausgewählt"
    
    if not allowed_file(file.filename):
        return False, f"Nur folgende Dateiformate sind erlaubt: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Dateigröße prüfen (zusätzlich zur Flask-Konfiguration)
    file.seek(0, 2)  # Zum Ende der Datei
    file_size = file.tell()
    file.seek(0)  # Zurück zum Anfang
    
    if file_size > MAX_FILE_SIZE:
        return False, f"Datei ist zu groß. Maximum: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, "OK"

def save_profile_image(file, user_id):
    """Speichert Profilbild und gibt den Dateinamen zurück"""
    if file and allowed_file(file.filename):
        # Sicheren Dateinamen generieren
        filename = secure_filename(file.filename)
        # Eindeutigen Namen erstellen mit User-ID
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        
        # Datei speichern
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        return unique_filename
    return None

def delete_profile_image(filename):
    """Löscht Profilbild vom Server"""
    if filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except:
                return False
    return False

# Hilfsfunktionen für E-Mail-Versand
def send_confirmation_email(user_email, confirmation_url):
    """Sendet eine Bestätigungs-E-Mail an den Benutzer"""
    try:
        msg = Message(
            subject='E-Mail-Adresse bestätigen - Login System',
            recipients=[user_email],
            html=render_template('email_confirmation.html', confirmation_url=confirmation_url),
            body=f'''
Willkommen beim Login System!

Bitte bestätigen Sie Ihre E-Mail-Adresse, indem Sie auf den folgenden Link klicken:
{confirmation_url}

Dieser Link ist 1 Stunde gültig.

Falls Sie sich nicht registriert haben, können Sie diese E-Mail ignorieren.
            '''
        )
        mail.send(msg)
        print(f"✅ E-Mail erfolgreich an {user_email} gesendet")
        return True
    except Exception as e:
        print(f"❌ Fehler beim E-Mail-Versand an {user_email}: {e}")
        print(f"   E-Mail-Server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
        print(f"   Benutzername: {app.config['MAIL_USERNAME']}")
        print(f"   TLS: {app.config['MAIL_USE_TLS']}")
        return False

# Startseite
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user is None:
            # Benutzer existiert nicht mehr - Session löschen
            session.pop('user_id', None)
            flash('Ihre Session ist abgelaufen. Bitte loggen Sie sich erneut ein.', 'info')
            return render_template('index.html')
        
        # Top 3 Spieler für Dashboard-Widget abrufen
        top_players = db.session.query(Leaderboard, User).join(User).order_by(
            Leaderboard.total_points.desc()
        ).limit(3).all()
        
        # Aktuelle User-Statistiken
        current_user_entry = Leaderboard.query.filter_by(user_id=user.id).first()
        user_stats = None
        if current_user_entry:
            user_stats = {
                'rank': current_user_entry.get_rank(),
                'total_points': current_user_entry.total_points,
                'total_quizzes': current_user_entry.total_quizzes
            }
        
        # Top-Spieler formatieren
        top_players_data = []
        for entry, player in top_players:
            top_players_data.append({
                'username': player.username,
                'total_points': entry.total_points,
                'profile_image': player.profile_image
            })
        
        return render_template('dashboard.html', 
                             user=user,
                             top_players=top_players_data,
                             user_stats=user_stats)
    return render_template('index.html')

# Login-Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.email_confirmed:
                flash('Bitte bestätigen Sie zuerst Ihre E-Mail-Adresse!', 'error')
                return render_template('login.html')
            session['user_id'] = user.id
            flash('Erfolgreich eingeloggt!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ungültiger Benutzername oder Passwort!', 'error')
    
    return render_template('login.html')

# Registrierungs-Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validierung
        if password != confirm_password:
            flash('Passwörter stimmen nicht überein!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Benutzername bereits vergeben!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('E-Mail bereits registriert!', 'error')
            return render_template('register.html')
        
        # Neuen Benutzer erstellen
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Bestätigungs-E-Mail senden
        token = new_user.generate_confirmation_token()
        confirmation_url = url_for('confirm_email', token=token, _external=True)
        
        if send_confirmation_email(email, confirmation_url):
            flash('Registrierung erfolgreich! Bitte überprüfen Sie Ihre E-Mails und bestätigen Sie Ihre E-Mail-Adresse.', 'success')
        else:
            flash('Registrierung erfolgreich, aber E-Mail konnte nicht gesendet werden. Kontaktieren Sie den Administrator.', 'warning')
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Logout-Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Erfolgreich ausgeloggt!', 'success')
    return redirect(url_for('index'))

# Benutzerprofil
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Bitte loggen Sie sich ein!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user is None:
        # Benutzer existiert nicht mehr - Session löschen
        session.pop('user_id', None)
        flash('Ihre Session ist abgelaufen. Bitte loggen Sie sich erneut ein.', 'info')
        return redirect(url_for('login'))
    
    return render_template('profile.html', user=user)

# Profil bearbeiten
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Bitte loggen Sie sich ein!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user is None:
        session.pop('user_id', None)
        flash('Ihre Session ist abgelaufen. Bitte loggen Sie sich erneut ein.', 'info')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_email':
            new_email = request.form.get('new_email')
            current_password = request.form.get('current_password')
            
            # Passwort validieren
            if not user.check_password(current_password):
                flash('Aktuelles Passwort ist falsch!', 'error')
                return render_template('edit_profile.html', user=user)
            
            # E-Mail-Format validieren (einfache Validierung)
            if '@' not in new_email or '.' not in new_email:
                flash('Ungültiges E-Mail-Format!', 'error')
                return render_template('edit_profile.html', user=user)
            
            # Prüfen ob E-Mail bereits verwendet wird
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != user.id:
                flash('Diese E-Mail-Adresse wird bereits verwendet!', 'error')
                return render_template('edit_profile.html', user=user)
            
            # E-Mail aktualisieren und Bestätigung zurücksetzen
            user.email = new_email
            user.email_confirmed = False
            db.session.commit()
            
            # Neue Bestätigungs-E-Mail senden
            token = user.generate_confirmation_token()
            confirmation_url = url_for('confirm_email', token=token, _external=True)
            
            if send_confirmation_email(new_email, confirmation_url):
                flash('E-Mail-Adresse wurde geändert! Bitte bestätigen Sie Ihre neue E-Mail-Adresse.', 'success')
            else:
                flash('E-Mail-Adresse wurde geändert, aber Bestätigungs-E-Mail konnte nicht gesendet werden.', 'warning')
            
            return redirect(url_for('profile'))
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Aktuelles Passwort validieren
            if not user.check_password(current_password):
                flash('Aktuelles Passwort ist falsch!', 'error')
                return render_template('edit_profile.html', user=user)
            
            # Neues Passwort validieren
            if len(new_password) < 6:
                flash('Das neue Passwort muss mindestens 6 Zeichen lang sein!', 'error')
                return render_template('edit_profile.html', user=user)
            
            if new_password != confirm_password:
                flash('Die neuen Passwörter stimmen nicht überein!', 'error')
                return render_template('edit_profile.html', user=user)
            
            # Passwort aktualisieren
            user.set_password(new_password)
            db.session.commit()
            
            flash('Passwort erfolgreich geändert!', 'success')
            return redirect(url_for('profile'))
        
        elif action == 'upload_image':
            # Profilbild hochladen
            if 'profile_image' not in request.files:
                flash('Keine Datei ausgewählt!', 'error')
                return render_template('edit_profile.html', user=user)
            
            file = request.files['profile_image']
            is_valid, message = validate_image_file(file)
            
            if not is_valid:
                flash(message, 'error')
                return render_template('edit_profile.html', user=user)
            
            # Altes Profilbild löschen falls vorhanden
            if user.profile_image:
                delete_profile_image(user.profile_image)
            
            # Neues Profilbild speichern
            filename = save_profile_image(file, user.id)
            if filename:
                user.profile_image = filename
                db.session.commit()
                flash('Profilbild erfolgreich hochgeladen!', 'success')
            else:
                flash('Fehler beim Hochladen des Profilbilds!', 'error')
            
            return redirect(url_for('profile'))
        
        elif action == 'delete_image':
            # Profilbild löschen
            if user.profile_image:
                if delete_profile_image(user.profile_image):
                    user.profile_image = None
                    db.session.commit()
                    flash('Profilbild erfolgreich gelöscht!', 'success')
                else:
                    flash('Fehler beim Löschen des Profilbilds!', 'error')
            else:
                flash('Kein Profilbild vorhanden!', 'info')
            
            return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=user)

# E-Mail-Bestätigung
@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash('Der Bestätigungslink ist ungültig oder abgelaufen.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    if user is None:
        flash('Benutzer nicht gefunden.', 'error')
        return redirect(url_for('login'))
    
    if user.email_confirmed:
        flash('E-Mail-Adresse bereits bestätigt. Sie können sich anmelden.', 'info')
    else:
        user.email_confirmed = True
        db.session.commit()
        flash('E-Mail-Adresse erfolgreich bestätigt! Sie können sich jetzt anmelden.', 'success')
    
    return redirect(url_for('login'))

# Neue Bestätigungs-E-Mail anfordern
@app.route('/resend_confirmation')
def resend_confirmation():
    return render_template('resend_confirmation.html')

@app.route('/resend_confirmation', methods=['POST'])
def resend_confirmation_post():
    email = request.form['email']
    user = User.query.filter_by(email=email).first()
    
    if user is None:
        flash('E-Mail-Adresse nicht gefunden.', 'error')
        return render_template('resend_confirmation.html')
    
    if user.email_confirmed:
        flash('E-Mail-Adresse bereits bestätigt.', 'info')
        return redirect(url_for('login'))
    
    token = user.generate_confirmation_token()
    confirmation_url = url_for('confirm_email', token=token, _external=True)
    
    if send_confirmation_email(email, confirmation_url):
        flash('Neue Bestätigungs-E-Mail wurde gesendet.', 'success')
    else:
        flash('Fehler beim E-Mail-Versand. Versuchen Sie es später erneut.', 'error')
    
    return redirect(url_for('login'))

# Hilfsfunktionen für Mathe-Quiz
def generate_math_questions(num_questions=5, difficulty='mixed'):
    """
    Generiert zufällige Mathematik-Aufgaben mit verschiedenen Schwierigkeitsgraden
    
    Args:
        num_questions: Anzahl der Fragen (Standard: 5)
        difficulty: 'easy', 'medium', 'hard', 'mixed' (Standard: 'mixed')
    """
    questions = []
    
    # Schwierigkeitsgrade definieren
    difficulty_levels = ['easy', 'medium', 'hard']
    
    for i in range(num_questions):
        # Bei 'mixed' zufälligen Schwierigkeitsgrad wählen
        if difficulty == 'mixed':
            current_difficulty = random.choice(difficulty_levels)
        else:
            current_difficulty = difficulty
        
        # Frage basierend auf Schwierigkeitsgrad generieren
        if current_difficulty == 'easy':
            question_data = generate_easy_question()
        elif current_difficulty == 'medium':
            question_data = generate_medium_question()
        else:  # hard
            question_data = generate_hard_question()
        
        # Schwierigkeitsgrad zur Frage hinzufügen
        question_data['difficulty'] = current_difficulty
        questions.append(question_data)
    
    return questions

def generate_easy_question():
    """Generiert einfache Aufgaben (Addition, Subtraktion, kleine Multiplikation)"""
    operations = ['+', '-', '*']
    operation = random.choice(operations)
    
    if operation == '+':
        a = random.randint(1, 25)
        b = random.randint(1, 25)
        answer = a + b
        question = f"{a} + {b}"
    elif operation == '-':
        a = random.randint(10, 30)
        b = random.randint(1, a)  # Sicherstellen, dass Ergebnis positiv ist
        answer = a - b
        question = f"{a} - {b}"
    else:  # multiplication
        a = random.randint(2, 12)
        b = random.randint(2, 12)
        answer = a * b
        question = f"{a} × {b}"
    
    return {
        'question': question,
        'correct_answer': answer
    }

def generate_medium_question():
    """Generiert mittelschwere Aufgaben (größere Zahlen, Division, Potenzen)"""
    operations = ['+', '-', '*', '/', '**']
    operation = random.choice(operations)
    
    if operation == '+':
        a = random.randint(25, 100)
        b = random.randint(25, 100)
        answer = a + b
        question = f"{a} + {b}"
    elif operation == '-':
        a = random.randint(50, 150)
        b = random.randint(25, a)
        answer = a - b
        question = f"{a} - {b}"
    elif operation == '*':
        a = random.randint(12, 25)
        b = random.randint(12, 25)
        answer = a * b
        question = f"{a} × {b}"
    elif operation == '/':
        # Division mit ganzzahligem Ergebnis
        answer = random.randint(5, 20)
        b = random.randint(2, 12)
        a = answer * b
        question = f"{a} ÷ {b}"
    else:  # Potenz
        base = random.randint(2, 8)
        exponent = random.randint(2, 4)
        answer = base ** exponent
        question = f"{base}²" if exponent == 2 else f"{base}³" if exponent == 3 else f"{base}⁴"
    
    return {
        'question': question,
        'correct_answer': answer
    }

def generate_hard_question():
    """Generiert schwere Aufgaben (komplexe Operationen, gemischte Aufgaben)"""
    question_types = [
        'complex_arithmetic',
        'percentage',
        'square_root',
        'mixed_operations',
        'word_problem'
    ]
    
    question_type = random.choice(question_types)
    
    if question_type == 'complex_arithmetic':
        # Komplexe Arithmetik mit mehreren Operationen
        a = random.randint(15, 50)
        b = random.randint(5, 15)
        c = random.randint(2, 10)
        
        operations = [
            (f"{a} + {b} × {c}", a + b * c),
            (f"{a} - {b} + {c}", a - b + c),
            (f"({a} + {b}) × {c}", (a + b) * c),
            (f"{a} × {b} - {c}", a * b - c)
        ]
        
        question, answer = random.choice(operations)
        
    elif question_type == 'percentage':
        # Prozentrechnung
        base = random.randint(50, 500)
        percentage = random.choice([10, 20, 25, 30, 40, 50, 75])
        answer = int(base * percentage / 100)
        question = f"{percentage}% von {base}"
        
    elif question_type == 'square_root':
        # Quadratwurzeln von perfekten Quadraten
        root = random.randint(4, 15)
        number = root * root
        answer = root
        question = f"√{number}"
        
    elif question_type == 'mixed_operations':
        # Gemischte Operationen mit Klammern
        a = random.randint(10, 30)
        b = random.randint(2, 8)
        c = random.randint(5, 15)
        d = random.randint(2, 5)
        
        # (a + b) × c ÷ d
        if (a + b) * c % d == 0:  # Sicherstellen, dass Division aufgeht
            answer = (a + b) * c // d
            question = f"({a} + {b}) × {c} ÷ {d}"
        else:
            # Fallback zu einfacherer Operation
            answer = a * b + c
            question = f"{a} × {b} + {c}"
            
    else:  # word_problem
        # Einfache Textaufgaben
        scenarios = [
            {
                'template': "Ein Auto fährt {speed} km/h. Wie weit kommt es in {hours} Stunden?",
                'generator': lambda: (
                    random.randint(60, 120),  # speed
                    random.randint(2, 5)      # hours
                ),
                'calculator': lambda speed, hours: speed * hours
            },
            {
                'template': "In einem Kino sind {rows} Reihen mit je {seats} Sitzen. Wie viele Sitze gibt es insgesamt?",
                'generator': lambda: (
                    random.randint(15, 30),   # rows
                    random.randint(20, 40)    # seats
                ),
                'calculator': lambda rows, seats: rows * seats
            },
            {
                'template': "Ein Rechteck ist {length} cm lang und {width} cm breit. Wie groß ist die Fläche?",
                'generator': lambda: (
                    random.randint(8, 20),    # length
                    random.randint(5, 15)     # width
                ),
                'calculator': lambda length, width: length * width
            }
        ]
        
        scenario = random.choice(scenarios)
        values = scenario['generator']()
        answer = scenario['calculator'](*values)
        question = scenario['template'].format(*values)
    
    return {
        'question': question,
        'correct_answer': answer
    }

# Mathe-Quiz Auswahl-Seite
@app.route('/math_quiz')
def math_quiz():
    if 'user_id' not in session:
        flash('Bitte loggen Sie sich ein!', 'error')
        return redirect(url_for('login'))
    
    # Zeige Auswahl-Seite für Schwierigkeitsgrad
    return render_template('quiz_selection.html')

# Mathe-Quiz mit Schwierigkeitsgrad starten
@app.route('/math_quiz/<difficulty>')
def math_quiz_start(difficulty):
    if 'user_id' not in session:
        flash('Bitte loggen Sie sich ein!', 'error')
        return redirect(url_for('login'))
    
    # Überprüfen, ob Schwierigkeitsgrad gültig ist
    valid_difficulties = ['easy', 'medium', 'hard', 'mixed']
    if difficulty not in valid_difficulties:
        flash('Ungültiger Schwierigkeitsgrad!', 'error')
        return redirect(url_for('math_quiz'))
    
    # Generiere 5 neue Aufgaben mit gewähltem Schwierigkeitsgrad
    questions = generate_math_questions(5, difficulty)
    
    # Speichere die Aufgaben und Schwierigkeitsgrad in der Session
    session['quiz_questions'] = questions
    session['quiz_difficulty'] = difficulty
    session['quiz_started'] = True
    
    # Schwierigkeitsgrad-Namen für die Anzeige
    difficulty_names = {
        'easy': 'Einfach',
        'medium': 'Mittel', 
        'hard': 'Schwer',
        'mixed': 'Gemischt'
    }
    
    return render_template('math_quiz.html', 
                         questions=questions, 
                         difficulty=difficulty,
                         difficulty_name=difficulty_names[difficulty])

# Mathe-Quiz auswerten
@app.route('/math_quiz_submit', methods=['POST'])
def math_quiz_submit():
    if 'user_id' not in session:
        flash('Bitte loggen Sie sich ein!', 'error')
        return redirect(url_for('login'))
    
    if 'quiz_questions' not in session:
        flash('Keine Quiz-Daten gefunden. Starten Sie ein neues Quiz.', 'error')
        return redirect(url_for('math_quiz'))
    
    user = User.query.get(session['user_id'])
    questions = session['quiz_questions']
    
    # Antworten sammeln und bewerten
    results = []
    score = 0
    
    for i, question in enumerate(questions):
        user_answer = request.form.get(f'answer_{i}')
        correct_answer = question['correct_answer']
        
        is_correct = False
        if user_answer:
            try:
                user_answer_int = int(user_answer)
                is_correct = user_answer_int == correct_answer
                if is_correct:
                    score += 1
            except ValueError:
                is_correct = False
        
        results.append({
            'question': question['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })
    
    # Quiz-Ergebnis in der Datenbank speichern
    difficulty = session.get('quiz_difficulty', 'mixed')
    quiz_data = []
    for i, (question, result) in enumerate(zip(questions, results)):
        quiz_data.append({
            'question': question['question'],
            'correct_answer': question['correct_answer'],
            'user_answer': result['user_answer'],
            'is_correct': result['is_correct'],
            'difficulty': question.get('difficulty', 'unknown')
        })
    
    quiz_result = MathQuiz(
        user_id=user.id,
        questions=json.dumps(quiz_data),
        answers=json.dumps([r['user_answer'] for r in results]),
        score=score,
        total_questions=len(questions)
    )
    
    db.session.add(quiz_result)
    db.session.commit()
    
    # Leaderboard aktualisieren
    update_leaderboard(user.id)
    
    # Punkte für dieses Quiz berechnen
    points_earned = quiz_result.calculate_points()
    
    # Schwierigkeitsgrad-Namen für die Anzeige
    difficulty_names = {
        'easy': 'Einfach',
        'medium': 'Mittel', 
        'hard': 'Schwer',
        'mixed': 'Gemischt'
    }
    
    # Session-Daten löschen
    session.pop('quiz_questions', None)
    session.pop('quiz_difficulty', None)
    session.pop('quiz_started', None)
    
    return render_template('math_quiz_result.html', 
                         results=results, 
                         score=score, 
                         total=len(questions),
                         difficulty=difficulty,
                         difficulty_name=difficulty_names.get(difficulty, 'Unbekannt'),
                         points_earned=points_earned)

# Mathe-Quiz Historie anzeigen
@app.route('/math_quiz_history')
def math_quiz_history():
    if 'user_id' not in session:
        flash('Bitte loggen Sie sich ein!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    quiz_history = MathQuiz.query.filter_by(user_id=user.id).order_by(MathQuiz.created_at.desc()).limit(10).all()
    
    # Historie-Daten aufbereiten
    history_data = []
    for quiz in quiz_history:
        quiz_details = json.loads(quiz.questions)
        
        # Überprüfen ob neue oder alte Datenstruktur
        if quiz_details and isinstance(quiz_details[0], dict):
            # Neue Struktur mit vollständigen Details
            details = quiz_details
        else:
            # Alte Struktur - nur Question-Strings
            answers = json.loads(quiz.answers)
            details = []
            for i, question_str in enumerate(quiz_details):
                details.append({
                    'question': question_str,
                    'user_answer': answers[i] if i < len(answers) else None,
                    'correct_answer': 'N/A',  # Kann nicht rekonstruiert werden
                    'is_correct': False  # Kann nicht bestimmt werden
                })
        
        history_data.append({
            'id': quiz.id,
            'score': quiz.score,
            'total': quiz.total_questions,
            'percentage': round((quiz.score / quiz.total_questions) * 100, 1),
            'date': quiz.created_at.strftime('%d.%m.%Y um %H:%M'),
            'details': details
        })
    
    return render_template('math_quiz_history.html', history=history_data, user=user)

# Hilfsfunktion zum Aktualisieren des Leaderboards
def update_leaderboard(user_id):
    """Aktualisiert oder erstellt den Leaderboard-Eintrag für einen User"""
    leaderboard_entry = Leaderboard.query.filter_by(user_id=user_id).first()
    
    if not leaderboard_entry:
        # Neuen Eintrag erstellen
        leaderboard_entry = Leaderboard(user_id=user_id)
        db.session.add(leaderboard_entry)
    
    # Statistiken aktualisieren
    leaderboard_entry.update_stats()

# Leaderboard-Route
@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        flash('Bitte loggen Sie sich ein!', 'error')
        return redirect(url_for('login'))
    
    # Top 10 Spieler abrufen
    top_players = db.session.query(Leaderboard, User).join(User).order_by(
        Leaderboard.total_points.desc()
    ).limit(10).all()
    
    # Aktueller User
    current_user = User.query.get(session['user_id'])
    current_user_entry = Leaderboard.query.filter_by(user_id=current_user.id).first()
    
    # Leaderboard-Daten formatieren
    leaderboard_data = []
    for i, (entry, user) in enumerate(top_players, 1):
        leaderboard_data.append({
            'rank': i,
            'username': user.username,
            'total_points': entry.total_points,
            'total_quizzes': entry.total_quizzes,
            'average_score': round(entry.average_score, 1),
            'perfect_scores': entry.perfect_scores,
            'profile_image': user.profile_image,
            'is_current_user': user.id == current_user.id
        })
    
    # Aktuelle User-Statistiken
    user_stats = None
    if current_user_entry:
        user_stats = {
            'rank': current_user_entry.get_rank(),
            'total_points': current_user_entry.total_points,
            'total_quizzes': current_user_entry.total_quizzes,
            'average_score': round(current_user_entry.average_score, 1),
            'perfect_scores': current_user_entry.perfect_scores,
            'best_score': current_user_entry.best_score
        }
    
    return render_template('leaderboard.html', 
                         leaderboard=leaderboard_data, 
                         user_stats=user_stats,
                         current_user=current_user)

# API-Route für Leaderboard-Daten (falls gewünscht)
@app.route('/api/leaderboard')
def api_leaderboard():
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    # Top 10 abrufen
    top_players = db.session.query(Leaderboard, User).join(User).order_by(
        Leaderboard.total_points.desc()
    ).limit(10).all()
    
    data = []
    for i, (entry, user) in enumerate(top_players, 1):
        data.append({
            'rank': i,
            'username': user.username,
            'total_points': entry.total_points,
            'total_quizzes': entry.total_quizzes,
            'average_score': round(entry.average_score, 1)
        })
    
    return {'leaderboard': data}

# Error Handler für 404 - Seite nicht gefunden
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Error Handler für 500 - Server-Fehler
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Error Handler für 403 - Zugriff verweigert
@app.errorhandler(403)
def access_forbidden(e):
    flash('Zugriff verweigert. Sie haben keine Berechtigung für diese Aktion.', 'error')
    return redirect(url_for('index'))

# Error Handler für allgemeine Exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    print(f"Unhandled exception: {e}")
    
    # Für Debug-Modus: Zeige den echten Fehler
    if app.debug:
        return str(e), 500
    
    # Für Produktion: Zeige generische 500-Seite
    return render_template('500.html', error_code=500), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=8081) 