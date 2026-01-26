# 🚀 Deploy e Produção - NFCe Web Reader

## 📦 Preparação para Produção

### 1. Configurações de Segurança

#### app.py - Mudanças necessárias:

```python
# Trocar de:
app.config['SECRET_KEY'] = 'nfce-reader-secret-key-2024'

# Para:
import os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24)
```

#### Remover debug mode:
```python
# Trocar de:
app.run(debug=True, host='0.0.0.0', port=5000)

# Para:
app.run(debug=False, host='0.0.0.0', port=5000)
```

### 2. Servidor WSGI (Gunicorn)

#### Instalar Gunicorn:
```bash
pip install gunicorn
```

#### Criar arquivo wsgi.py:
```python
from app import app

if __name__ == "__main__":
    app.run()
```

#### Rodar com Gunicorn:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 wsgi:app
```

### 3. Variáveis de Ambiente

#### Criar arquivo .env:
```bash
SECRET_KEY=sua-chave-secreta-super-segura-aqui
FLASK_ENV=production
CSV_FILE=nfc_data.csv
```

#### Instalar python-dotenv:
```bash
pip install python-dotenv
```

#### Usar no app.py:
```python
from dotenv import load_dotenv
load_dotenv()
```

## ☁️ Opções de Deploy

### Opção 1: Heroku (Fácil - Free Tier)

#### 1. Criar Procfile:
```
web: gunicorn wsgi:app
```

#### 2. Criar runtime.txt:
```
python-3.11.7
```

#### 3. Deploy:
```bash
heroku login
heroku create nfce-reader
git push heroku main
```

### Opção 2: Railway (Fácil - Free Tier)

#### 1. Conectar repositório GitHub
#### 2. Railway detecta automaticamente
#### 3. Adicionar variáveis de ambiente
#### 4. Deploy automático!

### Opção 3: Render (Fácil - Free Tier)

#### 1. Conectar repositório
#### 2. Configurar:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app`
#### 3. Deploy!

### Opção 4: DigitalOcean App Platform

#### 1. Conectar repositório
#### 2. Escolher plano
#### 3. Configurar variáveis
#### 4. Deploy!

### Opção 5: VPS/Cloud (Avançado)

#### Setup completo com Nginx:

```bash
# 1. Atualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python e dependências
sudo apt install python3-pip python3-venv nginx -y

# 3. Clonar projeto
git clone seu-repositorio
cd NFCe

# 4. Criar ambiente virtual
python3 -m venv .nfce
source .nfce/bin/activate

# 5. Instalar dependências
pip install -r requirements.txt
pip install gunicorn

# 6. Criar serviço systemd
sudo nano /etc/systemd/system/nfce.service
```

#### Conteúdo do nfce.service:
```ini
[Unit]
Description=NFCe Web Reader
After=network.target

[Service]
User=seu-usuario
WorkingDirectory=/caminho/para/NFCe
Environment="PATH=/caminho/para/NFCe/.nfce/bin"
ExecStart=/caminho/para/NFCe/.nfce/bin/gunicorn --workers 3 --bind unix:nfce.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

#### Configurar Nginx:
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://unix:/caminho/para/NFCe/nfce.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /caminho/para/NFCe/static;
    }
}
```

#### Ativar serviço:
```bash
sudo systemctl start nfce
sudo systemctl enable nfce
sudo systemctl restart nginx
```

#### SSL com Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

## 🐳 Docker (Recomendado)

### Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

# Expor porta
EXPOSE 5000

# Comando de inicialização
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:app"]
```

### docker-compose.yml:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
    volumes:
      - ./nfc_data.csv:/app/nfc_data.csv
    restart: unless-stopped
```

### Comandos Docker:
```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📊 Monitoramento

### Opção 1: Sentry (Erros)
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="seu-dsn-aqui",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### Opção 2: New Relic (Performance)
```bash
pip install newrelic
newrelic-admin run-program gunicorn wsgi:app
```

## 🔒 Segurança Adicional

### 1. CORS (se necessário):
```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "https://seu-dominio.com"}})
```

### 2. Rate Limiting:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/process', methods=['POST'])
@limiter.limit("10 per minute")
def process_nfce():
    # ...
```

### 3. HTTPS Redirect:
```python
from flask_talisman import Talisman

if not app.debug:
    Talisman(app, force_https=True)
```

## 💾 Backup e Persistência

### Backup automático do CSV:
```python
import shutil
from datetime import datetime

def backup_csv():
    if os.path.exists(CSV_FILE):
        backup_name = f"backup_nfc_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        shutil.copy(CSV_FILE, f"backups/{backup_name}")
```

### Usar banco de dados (opcional):
```python
# SQLite para produção pequena
import sqlite3

# PostgreSQL para produção maior
from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/nfce'
```

## 📈 Escalabilidade

### Redis para cache:
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@app.route('/api/stats')
@cache.cached(timeout=60)
def get_stats():
    # ...
```

### Celery para tarefas assíncronas:
```python
from celery import Celery

celery = Celery(app.name, broker='redis://localhost:6379/0')

@celery.task
def process_nfce_async(url):
    # Processamento em background
    pass
```

## 🔧 Manutenção

### Logs estruturados:
```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

### Health check endpoint:
```python
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })
```

## 📱 PWA (Progressive Web App)

### manifest.json:
```json
{
  "name": "NFCe Reader",
  "short_name": "NFCe",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#667eea",
  "theme_color": "#6366f1",
  "icons": [
    {
      "src": "/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

### Service Worker básico:
```javascript
// sw.js
self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open('nfce-v1').then(cache => {
            return cache.addAll([
                '/',
                '/static/style.css',
                '/static/script.js'
            ]);
        })
    );
});
```

## 📊 Analytics

### Google Analytics:
```html
<!-- No head do index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

## ✅ Checklist de Deploy

- [ ] Remover debug mode
- [ ] Configurar SECRET_KEY segura
- [ ] Configurar variáveis de ambiente
- [ ] Testar em ambiente staging
- [ ] Configurar HTTPS
- [ ] Configurar backup automático
- [ ] Adicionar rate limiting
- [ ] Configurar logs
- [ ] Adicionar monitoramento de erros
- [ ] Testar responsividade
- [ ] Testar performance
- [ ] Documentar processo de deploy
- [ ] Configurar CI/CD (opcional)

---

**Recomendação**: Para começar, use Railway ou Render (free tier). Para produção séria, use DigitalOcean + Docker + Nginx.
