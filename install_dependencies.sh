#!/bin/bash
set -e

echo "🔧 Instalando dependências do Chromium para X-Collector..."
echo ""

# Verificar se é root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script precisa ser executado como root"
    echo "   Use: sudo bash install_dependencies.sh"
    exit 1
fi

echo "📦 Atualizando lista de pacotes..."
apt-get update -qq

echo ""
echo "📦 Instalando dependências do Chromium..."
apt-get install -y -qq \
    libxfixes3 \
    libgbm1 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libxshmfence1 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb-dri3-0

echo ""
echo "✅ Dependências instaladas com sucesso!"
echo ""
echo "🎯 Próximo passo:"
echo "   Execute: playwright install chromium"
echo "   Para instalar o Chromium do Playwright"
