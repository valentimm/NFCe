@echo off
REM Script de inicialização rápida do NFCe Web Reader
REM Para Windows

echo.
echo ========================================
echo   NFCe Web Reader - Inicializacao
echo ========================================
echo.

REM Verificar se o ambiente virtual existe
if not exist ".nfce\Scripts\activate.bat" (
    echo [!] Ambiente virtual nao encontrado!
    echo [*] Criando ambiente virtual...
    python -m venv .nfce
    
    if errorlevel 1 (
        echo [X] Erro ao criar ambiente virtual
        pause
        exit /b 1
    )
    
    echo [OK] Ambiente virtual criado!
)

REM Ativar ambiente virtual
echo [*] Ativando ambiente virtual...
call .nfce\Scripts\activate.bat

REM Verificar se as dependências estão instaladas
echo [*] Verificando dependencias...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [!] Dependencias nao encontradas!
    echo [*] Instalando dependencias...
    pip install -r requirements.txt
    
    if errorlevel 1 (
        echo [X] Erro ao instalar dependencias
        pause
        exit /b 1
    )
    
    echo [OK] Dependencias instaladas!
)

REM Iniciar aplicação
echo.
echo ========================================
echo   Iniciando NFCe Web Reader...
echo ========================================
echo.
echo Acesse: http://localhost:5000
echo Pressione Ctrl+C para parar
echo.

python app.py

pause
