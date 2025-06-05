# Login System mit Datenbank

Ein sicheres und benutzerfreundliches Login-System mit SQLite-Datenbank, entwickelt mit Flask.

## Features

- ✅ **Sichere Benutzerauthentifizierung** mit verschlüsselten Passwörtern
- ✅ **Benutzerregistrierung** mit E-Mail-Bestätigung
- ✅ **E-Mail-Bestätigungssystem** mit zeitlich begrenzten Tokens
- ✅ **Session-Management** für sichere Anmeldung
- ✅ **SQLite-Datenbank** für lokale Datenspeicherung
- ✅ **E-Mail-Versand** für Bestätigungslinks
- ✅ **Responsive Design** mit Bootstrap 5
- ✅ **Moderne Benutzeroberfläche** mit Font Awesome Icons
- ✅ **Deutsche Benutzeroberfläche**

## Installation

### 1. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 2. E-Mail-Konfiguration einrichten

Bearbeiten Sie die `app.py` Datei und tragen Sie Ihre E-Mail-Konfiguration ein:

```python
app.config['MAIL_USERNAME'] = 'ihre-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'ihr-app-passwort'
app.config['MAIL_DEFAULT_SENDER'] = 'ihre-email@gmail.com'
```

**Für Gmail:**
1. Aktivieren Sie die 2-Faktor-Authentifizierung
2. Erstellen Sie ein App-spezifisches Passwort
3. Verwenden Sie dieses App-Passwort anstelle Ihres normalen Passworts

### 3. Anwendung starten

```bash
python app.py
```

### 4. Browser öffnen

Öffnen Sie Ihren Browser und navigieren Sie zu:
```
http://localhost:5000
```

## Verwendung

### Registrierung
1. Klicken Sie auf "Registrieren"
2. Geben Sie Benutzername, E-Mail und Passwort ein
3. Bestätigen Sie Ihr Passwort
4. Klicken Sie auf "Registrieren"
5. **Überprüfen Sie Ihre E-Mails und klicken Sie auf den Bestätigungslink**
6. Nach der Bestätigung können Sie sich anmelden

### E-Mail-Bestätigung
- Sie erhalten eine E-Mail mit einem Bestätigungslink
- Der Link ist **1 Stunde** gültig
- Falls Sie keine E-Mail erhalten, überprüfen Sie den Spam-Ordner
- Sie können eine neue Bestätigungs-E-Mail anfordern

### Anmeldung
1. Klicken Sie auf "Anmelden"
2. Geben Sie Ihren Benutzername und Passwort ein
3. Klicken Sie auf "Anmelden"
4. **Wichtig:** Nur Benutzer mit bestätigter E-Mail-Adresse können sich anmelden

### Dashboard
Nach der Anmeldung gelangen Sie zum Dashboard, wo Sie:
- Ihre Benutzerinformationen einsehen können
- Ihr Profil besuchen können
- Sich sicher abmelden können

## Technische Details

### Datenbankstruktur
- **Tabelle**: `user`
- **Felder**:
  - `id` (Integer, Primary Key)
  - `username` (String, Unique)
  - `email` (String, Unique)
  - `password_hash` (String, verschlüsselt)
  - `email_confirmed` (Boolean, Standard: False)
  - `created_at` (DateTime)

### Sicherheitsfeatures
- Passwörter werden mit Werkzeug's `pbkdf2:sha256` verschlüsselt
- **E-Mail-Bestätigung** vor der ersten Anmeldung erforderlich
- **Zeitlich begrenzte Tokens** für E-Mail-Bestätigung (1 Stunde)
- Session-basierte Authentifizierung
- CSRF-Schutz durch Flask's Secret Key
- Eingabevalidierung und Fehlerbehandlung
- **Sichere Token-Generierung** mit itsdangerous

### Projektstruktur
```
├── app.py                           # Hauptanwendung
├── requirements.txt                 # Python-Abhängigkeiten
├── users.db                        # SQLite-Datenbank (wird automatisch erstellt)
├── templates/                      # HTML-Templates
│   ├── base.html                   # Basis-Template
│   ├── index.html                  # Startseite
│   ├── login.html                  # Login-Seite
│   ├── register.html               # Registrierungsseite
│   ├── dashboard.html              # Dashboard für eingeloggte Benutzer
│   ├── profile.html                # Benutzerprofilseite
│   ├── email_confirmation.html     # E-Mail-Template für Bestätigung
│   └── resend_confirmation.html    # Seite für erneute Bestätigung
└── README.md                       # Diese Datei
```

## Anpassung

### Secret Key ändern
Für den Produktionseinsatz sollten Sie den Secret Key in `app.py` ändern:
```python
app.config['SECRET_KEY'] = 'ihr-sicherer-geheimer-schlüssel'
```

### Datenbank-Konfiguration
Die Standardkonfiguration verwendet SQLite. Für andere Datenbanken können Sie die `SQLALCHEMY_DATABASE_URI` in `app.py` anpassen.

## Entwicklung

Das System ist mit Flask und SQLAlchemy entwickelt und nutzt:
- **Flask**: Web-Framework
- **Flask-SQLAlchemy**: Datenbank-ORM
- **Flask-Mail**: E-Mail-Versand
- **itsdangerous**: Sichere Token-Generierung
- **Werkzeug**: Passwort-Hashing
- **Bootstrap 5**: Frontend-Framework
- **Font Awesome**: Icons

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz zur freien Verfügung. 