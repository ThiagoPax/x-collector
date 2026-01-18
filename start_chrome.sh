#!/bin/bash
# Inicia o Chromium em modo debug para Linux
# Versão adaptada para funcionar em ambiente Docker/Linux

set -e

echo "🚀 Preparando Chromium em modo debug..."
echo ""

# Encontrar executável do Chromium do Playwright
CHROME_EXEC="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome"

# Fallback: tentar encontrar automaticamente
if [ ! -f "$CHROME_EXEC" ]; then
    echo "🔍 Procurando Chromium do Playwright..."
    CHROME_EXEC=$(find /root/.cache/ms-playwright -name "chrome" -type f 2>/dev/null | grep "chrome-linux/chrome" | head -1)
fi

if [ ! -f "$CHROME_EXEC" ]; then
    echo "❌ Chromium não encontrado!"
    echo "Tentando instalar com Playwright..."
    playwright install chromium
    CHROME_EXEC=$(find /root/.cache/ms-playwright -name "chrome" -type f 2>/dev/null | grep "chrome-linux/chrome" | head -1)
fi

if [ ! -f "$CHROME_EXEC" ]; then
    echo "❌ Erro: Não foi possível encontrar ou instalar o Chromium"
    exit 1
fi

echo "✅ Chromium encontrado em: $CHROME_EXEC"
echo ""

# Fechar Chromium se estiver aberto
echo "🛑 Fechando instâncias anteriores do Chromium..."
pkill -f "chrome.*--remote-debugging-port=9222" 2>/dev/null || true
sleep 2

# Diretório de perfil
PROFILE_DIR="/app/browser_data/chrome-profile"

# Criar diretório se não existir
mkdir -p "$PROFILE_DIR"

echo "✅ Perfil criado/verificado em: $PROFILE_DIR"
echo ""

# Iniciar Chromium com debug port
echo "🌐 Iniciando Chromium em modo debug..."

# Usar display virtual se necessário (para ambientes headless)
export DISPLAY=:99

# Tentar iniciar Xvfb se não estiver rodando
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "🖥️  Iniciando display virtual (Xvfb)..."
    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
    sleep 2
fi

# Iniciar Chromium
"$CHROME_EXEC" \
    --remote-debugging-port=9222 \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-dev-shm-usage \
    --disable-gpu \
    --no-sandbox \
    --disable-setuid-sandbox \
    --disable-web-security \
    --disable-features=IsolateOrigins,site-per-process \
    --window-size=1920,1080 \
    "about:blank" > /tmp/chrome.log 2>&1 &

CHROME_PID=$!

sleep 3

# Verificar se a porta está aberta
if lsof -i :9222 > /dev/null 2>&1; then
    echo ""
    echo "✅ Chromium iniciado com sucesso na porta 9222!"
    echo "   PID: $CHROME_PID"
    echo ""
    echo "📋 Chromium está rodando em background"
    echo "   Acesse a interface web para conectar e coletar dados"
    echo ""
    echo "⚠️  Logs em: /tmp/chrome.log"
    exit 0
else
    echo ""
    echo "❌ Erro: Chromium não iniciou corretamente."
    echo ""
    echo "📋 Verifique os logs em /tmp/chrome.log"
    cat /tmp/chrome.log
    exit 1
fi
