#!/bin/bash
# ===========================================
# X COLLECTOR - INSTALAÇÃO E EXECUÇÃO
# ===========================================

set -e

echo "🐦 X Posts Collector - Setup Automático"
echo "========================================"
echo ""

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Verificar Python
echo "1️⃣ Verificando Python..."
if command -v /usr/bin/python3 &> /dev/null; then
    PYTHON=/usr/bin/python3
    echo "   ✅ Python encontrado: $($PYTHON --version)"
else
    echo "   ❌ Python não encontrado!"
    exit 1
fi

# 2. Criar/verificar venv
echo ""
echo "2️⃣ Configurando ambiente virtual..."
if [ ! -d "venv" ]; then
    echo "   📦 Criando venv..."
    $PYTHON -m venv venv
fi
echo "   ✅ Venv OK"

# 3. Instalar dependências
echo ""
echo "3️⃣ Instalando dependências (pode demorar)..."
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt
echo "   ✅ Dependências instaladas"

# 4. Instalar Playwright browsers
echo ""
echo "4️⃣ Instalando Chromium para Playwright..."
./venv/bin/playwright install chromium --quiet 2>/dev/null || ./venv/bin/playwright install chromium
echo "   ✅ Chromium instalado"

# 5. Fechar Chrome existente
echo ""
echo "5️⃣ Preparando Chrome..."
pkill -x "Google Chrome" 2>/dev/null || true
sleep 2

# 6. Preparar perfil do Chrome
CHROME_PROFILE="$HOME/Library/Application Support/Google/Chrome"
DEBUG_PROFILE="$HOME/.x-collector-chrome-profile"

if [ -d "$CHROME_PROFILE" ]; then
    echo "   📂 Copiando seu perfil do Chrome..."
    rm -rf "$DEBUG_PROFILE"
    mkdir -p "$DEBUG_PROFILE"
    cp -R "$CHROME_PROFILE/Default" "$DEBUG_PROFILE/" 2>/dev/null || true
    cp "$CHROME_PROFILE/Local State" "$DEBUG_PROFILE/" 2>/dev/null || true
    echo "   ✅ Perfil copiado"
else
    echo "   ⚠️ Perfil Chrome não encontrado, criando novo..."
    mkdir -p "$DEBUG_PROFILE"
fi

# 7. Iniciar Chrome
echo ""
echo "6️⃣ Iniciando Chrome em modo debug..."
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9222 \
    --user-data-dir="$DEBUG_PROFILE" \
    --no-first-run \
    --no-default-browser-check \
    "https://x.com" &

CHROME_PID=$!
sleep 4

# 8. Verificar Chrome
if lsof -i :9222 > /dev/null 2>&1; then
    echo "   ✅ Chrome rodando na porta 9222"
else
    echo "   ❌ Chrome não iniciou corretamente"
    exit 1
fi

# 9. Testar conexão
echo ""
echo "7️⃣ Testando conexão..."
./venv/bin/python -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.connect_over_cdp('http://127.0.0.1:9222', timeout=5000)
        print('   ✅ Conexão com Chrome OK!')
        contexts = browser.contexts
        if contexts and contexts[0].pages:
            url = contexts[0].pages[0].url
            if 'x.com' in url:
                print('   ✅ Página do X aberta!')
    except Exception as e:
        print(f'   ⚠️ Erro: {e}')
    finally:
        await pw.stop()

asyncio.run(test())
"

echo ""
echo "========================================"
echo "✅ SETUP COMPLETO!"
echo "========================================"
echo ""
echo "📋 O Chrome abriu com seu perfil. Se necessário, faça login no X."
echo ""
echo "🚀 AGORA ABRA OUTRO TERMINAL e execute:"
echo ""
echo "   cd ~/Desktop/x-collector"
echo "   ./venv/bin/python collect.py \"sua pesquisa\" 50"
echo ""
echo "   Ou para a interface gráfica:"
echo "   ./venv/bin/python -m streamlit run app/main.py"
echo ""
echo "⚠️ Mantenha ESTA janela aberta enquanto coleta!"
echo ""

# Manter o script rodando
wait $CHROME_PID
