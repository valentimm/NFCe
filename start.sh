#!/bin/bash
# Script de inicialização rápida do NFCe Web Reader
# Para Linux/Mac

echo ""
echo "========================================"
echo "  NFCe Web Reader - Inicialização"
echo "========================================"
echo ""

# Verificar se o ambiente virtual existe
if [ ! -d ".nfce" ]; then
    echo "[!] Ambiente virtual não encontrado!"
    echo "[*] Criando ambiente virtual..."
    python3 -m venv .nfce
    
    if [ $? -ne 0 ]; then
        echo "[X] Erro ao criar ambiente virtual"
        exit 1
    fi
    
    echo "[OK] Ambiente virtual criado!"
fi

# Ativar ambiente virtual
echo "[*] Ativando ambiente virtual..."
source .nfce/bin/activate

# Verificar se as dependências estão instaladas
echo "[*] Verificando dependências..."
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[!] Dependências não encontradas!"
    echo "[*] Instalando dependências..."
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "[X] Erro ao instalar dependências"
        exit 1
    fi
    
    echo "[OK] Dependências instaladas!"
fi

# Iniciar aplicação
echo ""
echo "========================================"
echo "  Iniciando NFCe Web Reader..."
echo "========================================"
echo ""
echo "Acesse: http://localhost:5000"
echo "Pressione Ctrl+C para parar"
echo ""

python app.py
