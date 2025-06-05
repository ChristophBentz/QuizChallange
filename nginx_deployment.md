# Nginx + Gunicorn Deployment Anleitung

## 🚀 Nginx als Reverse Proxy zu Gunicorn

### Voraussetzungen
- Ubuntu/Debian Server mit Root-Zugriff
- Python 3.8+
- Nginx installiert

## Schritt 1: System vorbereiten

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Nginx und Python installieren
sudo apt install nginx python3 python3-pip python3-venv

# Nginx starten und aktivieren
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Schritt 2: Projekt einrichten

```bash
# Projekt-Verzeichnis erstellen
sudo mkdir -p /var/www/quiz-app
sudo chown $USER:$USER /var/www/quiz-app

# Projekt-Dateien kopieren
cd /var/www/quiz-app
# Hier alle Projektdateien hochladen

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
pip install gunicorn

# Datenbank initialisieren
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Schritt 3: Gunicorn konfigurieren

Gunicorn-Konfiguration: `/var/www/quiz-app/gunicorn.conf.py`

```python
# Gunicorn Konfiguration
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

## Schritt 4: Systemd Service erstellen

Service-Datei: `/etc/systemd/system/quiz-app.service`

## Schritt 5: Nginx konfigurieren

Nginx-Konfiguration: `/etc/nginx/sites-available/quiz-app`

## Schritt 6: Berechtigungen setzen

```bash
# Ordner-Berechtigungen
sudo chown -R $USER:www-data /var/www/quiz-app
sudo chmod -R 755 /var/www/quiz-app

# Upload-Ordner beschreibbar machen
sudo chmod -R 775 /var/www/quiz-app/static/uploads/
sudo chmod -R 775 /var/www/quiz-app/instance/
```

## Schritt 7: Services starten

```bash
# Systemd Service aktivieren
sudo systemctl daemon-reload
sudo systemctl start quiz-app
sudo systemctl enable quiz-app

# Nginx Site aktivieren
sudo ln -s /etc/nginx/sites-available/quiz-app /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Nginx neustarten
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart nginx
```

## Schritt 8: SSL-Zertifikat (Let's Encrypt)

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx

# SSL-Zertifikat erstellen
sudo certbot --nginx -d ihre-domain.de
```

## Monitoring und Logs

```bash
# Gunicorn Service Status
sudo systemctl status quiz-app

# Gunicorn Logs
sudo journalctl -u quiz-app -f

# Nginx Logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Quiz-App spezifische Logs
sudo tail -f /var/log/nginx/quiz-app_access.log
sudo tail -f /var/log/nginx/quiz-app_error.log
```

## Performance-Optimierung

### Gunicorn Worker anpassen
```bash
# Worker-Anzahl berechnen: (2 x CPU-Kerne) + 1
# Für 2 CPU-Kerne: 5 Worker
# Für 4 CPU-Kerne: 9 Worker

# In gunicorn.conf.py anpassen:
workers = 5  # Für 2 CPU-Kerne
```

### Nginx Caching aktivieren
```nginx
# In /etc/nginx/sites-available/quiz-app hinzufügen:
location /static/ {
    expires 1M;
    access_log off;
    add_header Cache-Control "public, immutable";
}
```

## Troubleshooting

### 502 Bad Gateway
1. Überprüfen Sie, ob Gunicorn läuft: `sudo systemctl status quiz-app`
2. Prüfen Sie die Gunicorn-Logs: `sudo journalctl -u quiz-app -f`
3. Testen Sie Gunicorn manuell: `gunicorn --bind 127.0.0.1:8000 wsgi:application`

### Permission Denied
```bash
sudo chown -R $USER:www-data /var/www/quiz-app
sudo chmod -R 755 /var/www/quiz-app
```

### High Load
- Erhöhen Sie die Worker-Anzahl in Gunicorn
- Aktivieren Sie Nginx-Caching
- Überwachen Sie mit `htop` und `nginx -s reload` 