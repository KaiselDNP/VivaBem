@echo off
set "VIVABEM_DEBUG=false"
set "VIVABEM_ALLOWED_HOSTS=localhost,127.0.0.1,.trycloudflare.com"
set "VIVABEM_CSRF_TRUSTED_ORIGINS=https://*.trycloudflare.com"
set "VIVABEM_BEHIND_HTTPS_PROXY=true"
set "VIVABEM_SECURE_SSL_REDIRECT=true"
set "VIVABEM_SECURE_HSTS_SECONDS=0"

cd /d "%~dp0.."
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
