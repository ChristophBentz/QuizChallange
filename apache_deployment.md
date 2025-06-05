# Apache Deployment Anleitung

## 🌐 Apache + mod_wsgi Deployment

### Voraussetzungen
- Ubuntu/Debian Server mit Root-Zugriff
- Python 3.8+
- Apache2 installiert

## Schritt 1: System vorbereiten

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Apache und Python-Module installieren
sudo apt install apache2 apache2-dev python3 python3-pip python3-venv libapache2-mod-wsgi-py3

# mod_wsgi aktivieren
sudo a2enmod wsgi
sudo systemctl reload apache2
```

## Schritt 2: Projekt-Verzeichnis einrichten

```bash
# Projekt-Verzeichnis erstellen
sudo mkdir -p /var/www/quiz-app
sudo chown $USER:$USER /var/www/quiz-app

# Projekt-Dateien hochladen
cd /var/www/quiz-app
# Hier alle Ihre Projektdateien kopieren
```

## Schritt 3: Virtual Environment einrichten

```bash
# Virtual Environment erstellen
cd /var/www/quiz-app
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
pip install gunicorn

# Datenbank initialisieren
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Schritt 4: Berechtigungen setzen

```bash
# Ordner-Berechtigungen
sudo chown -R www-data:www-data /var/www/quiz-app
sudo chmod -R 755 /var/www/quiz-app

# Upload-Ordner beschreibbar machen
sudo chmod -R 775 /var/www/quiz-app/static/uploads/
sudo chmod -R 775 /var/www/quiz-app/instance/
```

## Schritt 5: Apache Virtual Host konfigurieren

Virtual Host Datei: `/etc/apache2/sites-available/quiz-app.conf`

## Schritt 6: SSL-Zertifikat (Let's Encrypt)

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-apache

# SSL-Zertifikat erstellen
sudo certbot --apache -d ihre-domain.de
```

## Schritt 7: Aktivieren und starten

```bash
# Site aktivieren
sudo a2ensite quiz-app.conf
sudo a2dissite 000-default.conf

# Apache neustarten
sudo systemctl reload apache2
sudo systemctl restart apache2
```

## Logs überprüfen

```bash
# Apache Error Logs
sudo tail -f /var/log/apache2/error.log

# Apache Access Logs
sudo tail -f /var/log/apache2/access.log
```

## Troubleshooting

### 500 Internal Server Error
1. Überprüfen Sie die Error Logs
2. Stellen Sie sicher, dass alle Dependencies installiert sind
3. Prüfen Sie Dateiberechtigungen
4. Überprüfen Sie die wsgi.py Datei

### Permission Denied
```bash
sudo chown -R www-data:www-data /var/www/quiz-app
sudo chmod -R 755 /var/www/quiz-app
```

### Import Errors
- Stellen Sie sicher, dass das Virtual Environment korrekt ist
- Überprüfen Sie Python-Pfade in der Apache-Konfiguration 