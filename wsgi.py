#!/usr/bin/env python3
# WSGI Entry Point für Plesk/Apache/Nginx Deployment

import sys
import os

# Pfad zum Projektverzeichnis hinzufügen
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application

if __name__ == "__main__":
    application.run() 