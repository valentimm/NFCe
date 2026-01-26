# 📋 NFCe Web Reader

> Sistema web moderno e acessível para ler e processar notas fiscais NFCe, simplificando seu controle financeiro.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

## ✨ Funcionalidades

- 🌐 **Interface Web Moderna** - Design responsivo e acessível (WCAG 2.1)
- � **Scanner de QR Code Integrado** - Use a câmera do celular/computador
- 🔄 **Processamento Automático** - Cole URL ou escaneie QR code
- 📊 **Dashboard Inteligente** - Estatísticas em tempo real
- 💾 **Exportação de Dados** - Download em formato CSV
- 📱 **100% Responsivo** - Funciona em qualquer dispositivo
- ⚡ **Performance Otimizada** - Carregamento rápido e fluido
- ☁️ **Deploy Fácil** - Railway, Render, Heroku (pronto para produção)

## 🚀 Início Rápido

### Método 1: Script Automático (Recomendado)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### Método 2: Manual

1. **Crie o ambiente virtual:**
```bash
python -m venv .nfce
```

2. **Ative o ambiente virtual:**

Windows:
```bash
.\.nfce\Scripts\activate
```

Linux/Mac:
```bash
source .nfce/bin/activate
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Execute a aplicação:**
```bash
python app.py
```

5. **Acesse no navegador:**
```
http://localhost:5000
```

## 📖 Como Usar

### Aplicação Web (Recomendado)

1. Abra a aplicação no navegador
2. **Opção 1 - Scanner QR**: 
   - Clique em "Escanear QR Code"
   - Permita acesso à câmera
   - Aponte para o QR Code da nota
   - Processamento automático! ✨
3. **Opção 2 - Manual**:
   - Copie a URL da NFCe
   - Cole no campo de entrada
   - Clique em "Processar"
4. ✅ Dados salvos e estatísticas atualizadas!

### Modo Webcam (Original)

Para usar o modo original com webcam:
```bash
python main.py
```

Para usar o modo webcam melhorado:
```bash
python main_improved.py
```

## 📁 Estrutura do Projeto

```
NFCe/
├── app.py                      # Backend Flask (API REST)
├── main.py                     # Script original (webcam)
├── main_improved.py            # Script webcam melhorado
├── requirements.txt            # Dependências Python
├── start.bat / start.sh        # Scripts de inicialização
│
├── templates/
│   └── index.html             # Interface web
│
├── static/
│   ├── style.css              # Estilos CSS
│   └── script.js              # JavaScript
│
├── nfceReader/                # Scrapy spider
│   ├── scrapy.cfg
│   └── nfceReader/
│       └── spiders/
│           └── nfcedata.py    # Spider de extração
│
└── docs/
    ├── WEB_README.md          # Documentação da aplicação web
    ├── DESIGN_GUIDE.md        # Guia de design visual
    └── DEPLOY_GUIDE.md        # Guia de deploy
```

## 🛠️ Tecnologias

### Backend
- **Flask 3.0** - Framework web Python
- **Scrapy 2.11** - Web scraping robusto
- **Python 3.11+** - Linguagem principal

### Frontend
- **HTML5** - Estrutura semântica
- **CSS3** - Design moderno e responsivo
- **JavaScript** - Vanilla JS (sem frameworks)

### Extras
- **OpenCV** - Processamento de imagem (modo webcam)
- **pyzbar** - Leitura de QR codes

## 📊 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/process` | Processa URL da NFCe |
| `GET` | `/api/data` | Retorna dados salvos |
| `GET` | `/api/stats` | Retorna estatísticas |
| `GET` | `/api/download` | Download do CSV |
| `POST` | `/api/clear` | Limpa todos os dados |

Veja [WEB_README.md](WEB_README.md) para detalhes da API.

## 🎨 Design

Interface moderna com:
- ✅ Design Material
- ✅ Animações suaves
- ✅ Gradientes vibrantes
- ✅ Feedback visual
- ✅ Acessibilidade total
⚡ Deploy Rápido (Railway - Recomendado)

1. **Push para GitHub**:
```bash
git add .
git commit -m "Deploy NFCe Web Reader"
git push
```

2. **Deploy no Railway**:
   - Acesse [railway.app](https://railway.app)
   - Login com GitHub
   - New Project → Deploy from GitHub
   - Selecione NFCe
   - **Pronto!** ✨ URL: `https://seu-app.up.railway.app`

**Tempo total**: ~3 minutos

### 📚 Outras Opções:
- **Render** - Grátis e fácil
- **Heroku** - $5/mês, muito estável
- **DigitalOcean** - Profissional
- **VPS Próprio** - Controle total

Veja [DEPLOY_FACIL.md](DEPLOY_FACIL.md) para guia completo e passo a passo!
- **Render** - Fácil configuração
- **DigitalOcean** - VPS com Docker
- **Local** - Seu próprio servidor

Veja [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) para instruções detalhadas.

## 🔧 Requisitos do Sistema

- **Python**: 3.11 ou superior
- **pip**: Última versão
- **RAM**: Mínimo 512MB
- **Disco**: ~200MB para dependências
- **Navegador**: Chrome, Firefox, Safari, Edge (moderno)

### Opcional (para modo webcam):
- **Câmera**: Webcam ou [Iriun Webcam](https://iriun.com/)

## 🐛 Troubleshooting

### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

### Erro: "Port already in use"
Mude a porta em `app.py`:
```python
app.run(debug=True, port=5001)  # Mudou de 5000 para 5001
```

### Erro ao processar NFCe
- Verifique se a URL é válida
- Confirme conexão com internet
- Tente novamente

## ✨ Melhorias vs Script Original

| Recurso | Script Original | Aplicação Web |
|---------|----------------|---------------|
| Interface | Terminal | Web moderna |
| Entrada | Webcam + QR Code | Cole URL diretamente |
| Dispositivos | Apenas desktop | Qualquer dispositivo |
| Visualização | CSV externo | Dashboard integrado |
| Estatísticas | Nenhuma | Tempo real |
| Acessibilidade | Limitada | WCAG 2.1 |
| UX | Básica | Profissional |

## 🎯 Roadmap

- [ ] Autenticação de usuários
- [ ] PWA (Progressive Web App)
- [ ] Gráficos e relatórios
- [ ] Exportação em Excel/PDF
- [ ] Modo escuro
- [ ] Categorização automática

## 📧 Suporte

Abra uma issue no repositório para reportar bugs ou sugerir melhorias.

---

**Desenvolvido com ❤️ para facilitar seu controle financeiro**
