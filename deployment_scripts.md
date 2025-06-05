# Deployment-Skripte für Quiz-App

## 🚀 Automatisierte Installation

### Apache Deployment Skript

```bash
#!/bin/bash
# apache_deploy.sh - Automatisches Apache Deployment

set -e  # Exit bei Fehlern

DOMAIN="ihre-domain.de"
PROJECT_DIR="/var/www/quiz-app"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚀 Starte Apache Deployment für Quiz-App..."

# System aktualisieren
echo "📦 Aktualisiere System..."
sudo apt update && sudo apt upgrade -y

# Apache und Dependencies installieren
echo "🔧 Installiere Apache und mod_wsgi..."
sudo apt install -y apache2 apache2-dev python3 python3-pip python3-venv libapache2-mod-wsgi-py3

# mod_wsgi aktivieren
sudo a2enmod wsgi
sudo a2enmod headers
sudo a2enmod ssl
sudo a2enmod rewrite

# Projekt-Verzeichnis vorbereiten
echo "📁 Erstelle Projekt-Verzeichnis..."
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# Virtual Environment erstellen
echo "🐍 Erstelle Virtual Environment..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# Requirements installieren
echo "📚 Installiere Python-Pakete..."
pip install --upgrade pip
pip install -r requirements.txt

# Datenbank initialisieren
echo "🗄️ Initialisiere Datenbank..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# Berechtigungen setzen
echo "🔐 Setze Berechtigungen..."
sudo chown -R www-data:www-data $PROJECT_DIR
sudo chmod -R 755 $PROJECT_DIR
sudo chmod -R 775 $PROJECT_DIR/static/uploads/
sudo chmod -R 775 $PROJECT_DIR/instance/

# Apache Virtual Host konfigurieren
echo "⚙️ Konfiguriere Apache Virtual Host..."
sudo cp quiz-app.conf /etc/apache2/sites-available/
sudo sed -i "s/ihre-domain.de/$DOMAIN/g" /etc/apache2/sites-available/quiz-app.conf

# Site aktivieren
sudo a2ensite quiz-app.conf
sudo a2dissite 000-default.conf

# Apache neustarten
echo "🔄 Starte Apache neu..."
sudo systemctl reload apache2
sudo systemctl restart apache2

# SSL-Zertifikat erstellen
echo "🔒 Erstelle SSL-Zertifikat..."
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

echo "✅ Apache Deployment abgeschlossen!"
echo "🌐 Ihre App ist verfügbar unter: https://$DOMAIN"
```

### Nginx Deployment Skript

```bash
#!/bin/bash
# nginx_deploy.sh - Automatisches Nginx + Gunicorn Deployment

set -e

DOMAIN="ihre-domain.de"
PROJECT_DIR="/var/www/quiz-app"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚀 Starte Nginx + Gunicorn Deployment..."

# System aktualisieren
echo "📦 Aktualisiere System..."
sudo apt update && sudo apt upgrade -y

# Nginx und Dependencies installieren
echo "🔧 Installiere Nginx..."
sudo apt install -y nginx python3 python3-pip python3-venv

# Projekt vorbereiten
echo "📁 Bereite Projekt vor..."
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Log-Verzeichnis erstellen
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn

# Datenbank initialisieren
echo "🗄️ Initialisiere Datenbank..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# Berechtigungen setzen
echo "🔐 Setze Berechtigungen..."
sudo chown -R $USER:www-data $PROJECT_DIR
sudo chmod -R 755 $PROJECT_DIR
sudo chmod -R 775 $PROJECT_DIR/static/uploads/
sudo chmod -R 775 $PROJECT_DIR/instance/

# Systemd Service erstellen
echo "⚙️ Erstelle Systemd Service..."
sudo cp quiz-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable quiz-app
sudo systemctl start quiz-app

# Nginx konfigurieren
echo "🌐 Konfiguriere Nginx..."
sudo cp nginx-quiz-app /etc/nginx/sites-available/quiz-app
sudo sed -i "s/ihre-domain.de/$DOMAIN/g" /etc/nginx/sites-available/quiz-app

sudo ln -s /etc/nginx/sites-available/quiz-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Nginx testen und neustarten
sudo nginx -t
sudo systemctl restart nginx

# SSL-Zertifikat erstellen
echo "🔒 Erstelle SSL-Zertifikat..."
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

echo "✅ Nginx Deployment abgeschlossen!"
echo "🌐 Ihre App ist verfügbar unter: https://$DOMAIN"
```

## 🔄 Update-Skript

```bash
#!/bin/bash
# update_app.sh - App-Update Skript

PROJECT_DIR="/var/www/quiz-app"

echo "🔄 Starte App-Update..."

cd $PROJECT_DIR

# Backup erstellen
echo "💾 Erstelle Backup..."
sudo cp instance/users.db instance/users_backup_$(date +%Y%m%d_%H%M%S).db

# Code aktualisieren (falls Git verwendet wird)
if [ -d ".git" ]; then
    echo "📥 Aktualisiere Code von Git..."
    git pull origin main
fi

# Virtual Environment aktivieren
source venv/bin/activate

# Dependencies aktualisieren
echo "📚 Aktualisiere Dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Datenbank-Migration (falls notwendig)
echo "🗄️ Führe Datenbank-Migration aus..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# Services neustarten
if systemctl is-active --quiet quiz-app; then
    echo "🔄 Starte Gunicorn neu..."
    sudo systemctl restart quiz-app
fi

if systemctl is-active --quiet apache2; then
    echo "🔄 Starte Apache neu..."
    sudo systemctl reload apache2
fi

if systemctl is-active --quiet nginx; then
    echo "🔄 Starte Nginx neu..."
    sudo systemctl reload nginx
fi

echo "✅ App-Update abgeschlossen!"
```

## 🔍 Status-Check Skript

```bash
#!/bin/bash
# check_status.sh - Status-Überprüfung

echo "🔍 Überprüfe Quiz-App Status..."

# Service-Status
echo "📊 Service-Status:"
if systemctl is-active --quiet quiz-app; then
    echo "  ✅ Gunicorn: Läuft"
else
    echo "  ❌ Gunicorn: Stopped"
fi

if systemctl is-active --quiet apache2; then
    echo "  ✅ Apache2: Läuft"
elif systemctl is-active --quiet nginx; then
    echo "  ✅ Nginx: Läuft"
else
    echo "  ❌ Webserver: Stopped"
fi

# Disk Space
echo "💾 Festplattenspeicher:"
df -h /var/www/quiz-app | tail -1

# Memory Usage
echo "🧠 Speicherverbrauch:"
free -h

# Recent Errors
echo "🚨 Letzte Fehler (falls vorhanden):"
if systemctl is-active --quiet quiz-app; then
    sudo journalctl -u quiz-app --since "1 hour ago" --no-pager | grep -i error | tail -5
fi

# Test HTTP Response
echo "🌐 HTTP-Test:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|301\|302"; then
    echo "  ✅ Lokaler HTTP-Test erfolgreich"
else
    echo "  ❌ HTTP-Test fehlgeschlagen"
fi
```

## 🛠️ Troubleshooting-Skript

```bash
#!/bin/bash
# troubleshoot.sh - Automatische Problemdiagnose

echo "🛠️ Starte Problemdiagnose..."

# Check disk space
DISK_USAGE=$(df /var/www/quiz-app | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "⚠️ Warnung: Festplatte zu 90% voll!"
fi

# Check memory
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "⚠️ Warnung: Speicher zu 90% voll!"
fi

# Check log files
echo "📋 Prüfe Log-Dateien..."
if [ -f "/var/log/gunicorn/quiz-app-error.log" ]; then
    ERROR_COUNT=$(tail -100 /var/log/gunicorn/quiz-app-error.log | grep -c ERROR)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "🚨 $ERROR_COUNT Fehler in Gunicorn-Logs gefunden"
        tail -10 /var/log/gunicorn/quiz-app-error.log
    fi
fi

# Check permissions
echo "🔐 Prüfe Dateiberechtigungen..."
if [ ! -w "/var/www/quiz-app/instance" ]; then
    echo "❌ instance/ Verzeichnis nicht beschreibbar"
    echo "Reparatur: sudo chmod 775 /var/www/quiz-app/instance/"
fi

if [ ! -w "/var/www/quiz-app/static/uploads" ]; then
    echo "❌ uploads/ Verzeichnis nicht beschreibbar"
    echo "Reparatur: sudo chmod 775 /var/www/quiz-app/static/uploads/"
fi

echo "✅ Diagnose abgeschlossen"
```

## 📋 Verwendung der Skripte

1. **Skripte ausführbar machen:**
```bash
chmod +x *.sh
```

2. **Apache Deployment:**
```bash
sudo ./apache_deploy.sh
```

3. **Nginx Deployment:**
```bash
sudo ./nginx_deploy.sh
```

4. **App Updates:**
```bash
./update_app.sh
```

5. **Status überprüfen:**
```bash
./check_status.sh
```

6. **Probleme diagnostizieren:**
```bash
./troubleshoot.sh
``` 