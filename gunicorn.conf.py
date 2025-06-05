# Gunicorn Konfigurationsdatei für Quiz-App
# Speichern unter: /var/www/quiz-app/gunicorn.conf.py

import multiprocessing

# Server Socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1  # Automatische Berechnung
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart Workers
max_requests = 1000
max_requests_jitter = 100
restart_command = "restart"

# Logging
loglevel = "info"
accesslog = "/var/log/gunicorn/quiz-app-access.log"
errorlog = "/var/log/gunicorn/quiz-app-error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process Naming
proc_name = "quiz-app"

# Performance
preload_app = True
enable_stdio_inheritance = True

# Security
user = "www-data"
group = "www-data"

# Environment
raw_env = [
    'FLASK_ENV=production',
]

# SSL (falls verwendet)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Debugging (nur für Development)
# reload = True
# reload_extra_files = ["/var/www/quiz-app/app.py"] 