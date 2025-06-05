# Deployment-Anleitung für Plesk

Diese Anleitung führt Sie durch den Prozess, Ihre Flask Quiz-Anwendung auf einem Server mit Plesk zu deployen.

## Voraussetzungen

- Plesk-Panel Zugang
- Python 3.7+ auf dem Server
- SSH-Zugang (optional, aber empfohlen)

## Schritt 1: Domain/Subdomain in Plesk einrichten

1. Loggen Sie sich in Ihr Plesk-Panel ein
2. Gehen Sie zu **"Websites & Domains"**
3. Klicken Sie auf **"Add Domain"** oder **"Add Subdomain"**
4. Geben Sie Ihre gewünschte Domain/Subdomain ein (z.B. `quiz.ihre-domain.de`)
5. Wählen Sie das **"Document Root"** Verzeichnis

## Schritt 2: Python-Anwendung in Plesk konfigurieren

1. Gehen Sie zu **"Websites & Domains"**
2. Klicken Sie auf Ihre Domain
3. Suchen Sie nach **"Python"** oder **"Python App"** und klicken Sie darauf
4. Klicken Sie auf **"Create Python App"**
5. Konfigurieren Sie:
   - **Python Version**: 3.8+ (falls verfügbar)
   - **App Root**: `/httpdocs` (oder Ihr gewähltes Verzeichnis)
   - **App URL**: `/` (für Hauptdomain) oder gewünschter Pfad
   - **Startup File**: `wsgi.py`
   - **Application Entry Point**: `application`

## Schritt 3: Dateien hochladen

### Option A: Über Plesk File Manager
1. Gehen Sie zu **"Files"** in Ihrem Plesk-Panel
2. Navigieren Sie zum Document Root Ihrer Domain
3. Laden Sie alle Projektdateien hoch:
   ```
   app.py
   wsgi.py
   config.py
   requirements.txt
   env.example
   templates/ (kompletter Ordner)
   static/ (kompletter Ordner)
   instance/ (falls bereits vorhanden)
   ```

### Option B: Über SSH/SFTP
```bash
# Via SCP/SFTP alle Dateien in das Document Root hochladen
scp -r * user@server:/var/www/vhosts/ihre-domain.de/httpdocs/
```

## Schritt 4: Abhängigkeiten installieren

1. In Plesk gehen Sie zu **"Python"** → Ihre App
2. Klicken Sie auf **"Install/Uninstall Packages"**
3. Installieren Sie die Pakete aus `requirements.txt`:
   ```
   Flask==2.3.3
   Flask-SQLAlchemy==3.0.5
   Flask-Mail==0.9.1
   itsdangerous==2.1.2
   Werkzeug==2.3.7
   ```

### Oder über SSH:
```bash
cd /var/www/vhosts/ihre-domain.de/httpdocs
pip3 install -r requirements.txt
```

## Schritt 5: Umgebungsvariablen konfigurieren

1. In Plesk gehen Sie zu **"Python"** → Ihre App
2. Unter **"Environment Variables"** fügen Sie hinzu:
   ```
   FLASK_ENV=production
   SECRET_KEY=ihr-super-sicherer-secret-key
   MAIL_USERNAME=ihre-email@gmail.com
   MAIL_PASSWORD=ihr-gmail-app-passwort
   MAIL_DEFAULT_SENDER=ihre-email@gmail.com
   ```

### Oder erstellen Sie eine `.env` Datei:
```bash
# Kopieren Sie env.example zu .env und bearbeiten Sie die Werte
cp env.example .env
nano .env
```

## Schritt 6: Datenbank initialisieren

### Über SSH:
```bash
cd /var/www/vhosts/ihre-domain.de/httpdocs
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Oder über Plesk Python Console:
1. Gehen Sie zu **"Python"** → Ihre App
2. Öffnen Sie die **"Python Console"**
3. Führen Sie aus:
   ```python
   from app import app, db
   app.app_context().push()
   db.create_all()
   ```

## Schritt 7: Verzeichnisberechtigungen setzen

Stellen Sie sicher, dass folgende Verzeichnisse beschreibbar sind:
```bash
chmod 755 static/uploads/profile_images/
chmod 755 instance/
```

## Schritt 8: Anwendung starten

1. In Plesk gehen Sie zu **"Python"** → Ihre App
2. Klicken Sie auf **"Restart App"**
3. Überprüfen Sie den Status - er sollte **"Running"** anzeigen

## Schritt 9: SSL-Zertifikat einrichten (empfohlen)

1. Gehen Sie zu **"SSL/TLS Certificates"**
2. Klicken Sie auf **"Get a free basic certificate by Let's Encrypt"**
3. Aktivieren Sie das Zertifikat für Ihre Domain
4. Aktivieren Sie **"Permanent SEO-safe 301 redirect from HTTP to HTTPS"**

## Schritt 10: Tests

Besuchen Sie Ihre Website:
- `https://ihre-domain.de` - Sollte die Startseite anzeigen
- Testen Sie Registrierung, Login und Quiz-Funktionen

## Troubleshooting

### Häufige Probleme:

1. **500 Internal Server Error**
   - Überprüfen Sie die Error Logs in Plesk
   - Stellen Sie sicher, dass alle Dependencies installiert sind
   - Prüfen Sie Dateiberechtigungen

2. **Import-Fehler**
   - Stellen Sie sicher, dass `wsgi.py` korrekt konfiguriert ist
   - Überprüfen Sie Python-Pfade

3. **Datenbank-Fehler**
   - Stellen Sie sicher, dass das `instance/` Verzeichnis existiert und beschreibbar ist
   - Führen Sie `db.create_all()` aus

4. **E-Mail-Versand funktioniert nicht**
   - Überprüfen Sie Gmail App-Passwort
   - Stellen Sie sicher, dass Umgebungsvariablen korrekt gesetzt sind

### Log-Dateien überprüfen:
- Plesk: **"Logs"** → **"Error Logs"**
- SSH: `tail -f /var/log/plesk/panel.log`

## Wartung

### Regelmäßige Updates:
```bash
# Backup der Datenbank
cp instance/users.db instance/users_backup_$(date +%Y%m%d).db

# Code aktualisieren
git pull origin main  # falls Sie Git verwenden

# Anwendung neu starten
# Über Plesk Python Interface
```

### Backup-Strategie:
- Regelmäßige Backups der SQLite-Datenbank
- Backup der Upload-Dateien (`static/uploads/`)
- Plesk-eigene Backup-Funktionen nutzen

---

Bei Problemen oder Fragen kontaktieren Sie Ihren Hosting-Provider oder überprüfen Sie die Plesk-Dokumentation. 