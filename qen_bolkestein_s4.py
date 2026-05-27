#!/usr/bin/env python3
# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
"""QEN Bolkestein S4 - Nginx Deployment"""
import os, sys, json, logging, subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("/root/qen-framework")
NGINX_AVAILABLE = Path("/etc/nginx/sites-available")
NGINX_ENABLED = Path("/etc/nginx/sites-enabled")
SYSTEMD_PATH = Path("/etc/systemd/system")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

NGINX_TEMPLATE = """upstream qen_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}
server {
    listen 80;
    server_name api.cognitivelogic.it;
    return 301 https://$server_name$request_uri;
}
server {
    listen 443 ssl http2;
    server_name api.cognitivelogic.it;
    ssl_certificate /etc/letsencrypt/live/api.cognitivelogic.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.cognitivelogic.it/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    add_header Strict-Transport-Security "max-age=31536000" always;
    access_log /var/log/nginx/qen_access.log;
    error_log /var/log/nginx/qen_error.log;
    location /health {
        access_log off;
        return 200 "ok";
        add_header Content-Type text/plain;
    }
    location /agents/ {
        proxy_pass http://qen_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
    location / {
        proxy_pass http://qen_backend/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}"""

SYSTEMD_TEMPLATE = """[Unit]
Description=QEN Bolkestein FastAPI Backend
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=/root/qen-framework
Environment="PATH=/root/qen-framework/venv/bin"
ExecStart=/root/qen-framework/venv/bin/python3 -m uvicorn qen_bolkestein_main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=10
[Install]
WantedBy=multi-user.target"""

def main():
    logger.info("=" * 70)
    logger.info("QEN BOLKESTEIN SESSION 4 - NGINX DEPLOYMENT")
    logger.info("=" * 70)
    
    (PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    
    # Nginx config
    logger.info("→ Deploying Nginx configuration...")
    config_path = NGINX_AVAILABLE / "api.cognitivelogic.it"
    with open(config_path, "w") as f:
        f.write(NGINX_TEMPLATE)
    
    symlink_path = NGINX_ENABLED / "api.cognitivelogic.it"
    if symlink_path.exists():
        symlink_path.unlink()
    symlink_path.symlink_to(config_path)
    logger.info(f"  ✓ Config deployed to {config_path}")
    
    # Test nginx
    result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("  ✓ Nginx config valid")
    else:
        logger.error(f"  ✗ Nginx error: {result.stderr}")
    
    # Systemd service
    logger.info("→ Deploying systemd service...")
    service_path = SYSTEMD_PATH / "qen-backend.service"
    with open(service_path, "w") as f:
        f.write(SYSTEMD_TEMPLATE)
    logger.info(f"  ✓ Service created at {service_path}")
    
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    logger.info("  ✓ systemd reloaded")
    
    # Restart services
    logger.info("→ Restarting services...")
    subprocess.run(["systemctl", "restart", "nginx"], check=True)
    logger.info("  ✓ Nginx restarted")
    
    subprocess.run(["systemctl", "stop", "qen-backend"], capture_output=True)
    subprocess.run(["systemctl", "start", "qen-backend"], check=True)
    logger.info("  ✓ QEN backend started")
    
    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("✓ DEPLOYMENT COMPLETE")
    logger.info("=" * 70)
    logger.info("API Endpoint: https://api.cognitivelogic.it")
    logger.info("Health Check: https://api.cognitivelogic.it/health")
    logger.info("Agents:")
    logger.info("  • compliance-auditor")
    logger.info("  • territorial-mapper")
    logger.info("  • advisory-council")
    logger.info("  • intelligence-feed")
    logger.info("")
    logger.info("Next: journalctl -u qen-backend -f")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
