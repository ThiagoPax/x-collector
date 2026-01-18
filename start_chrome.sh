#!/bin/bash
# Inicia o Chrome em modo debug com CÓPIA do perfil do usuário

echo "🚀 Preparando Chrome em modo debug..."
echo ""

# Fechar Chrome se estiver aberto
pkill -x "Google Chrome" 2>/dev/null
sleep 2

# Diretórios
CHROME_PROFILE="$HOME/Library/Application Support/Google/Chrome"
DEBUG_PROFILE="$HOME/.x-collector-chrome-profile"

# Verificar se perfil original existe
if [ ! -d "$CHROME_PROFILE" ]; then
    echo "❌ Perfil do Chrome não encontrado em: $CHROME_PROFILE"
    exit 1
fi

# Criar/atualizar cópia do perfil
echo "📂 Copiando perfil do Chrome (pode demorar alguns segundos)..."

# Remover cópia antiga se existir
rm -rf "$DEBUG_PROFILE"

# Criar diretório
mkdir -p "$DEBUG_PROFILE"

# Copiar apenas arquivos essenciais (cookies, login, etc) - mais rápido
cp -R "$CHROME_PROFILE/Default" "$DEBUG_PROFILE/" 2>/dev/null || true
cp "$CHROME_PROFILE/Local State" "$DEBUG_PROFILE/" 2>/dev/null || true

echo "✅ Perfil copiado!"
echo ""

# Iniciar Chrome com perfil copiado e debug port
echo "🌐 Iniciando Chrome..."
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9222 \
    --user-data-dir="$DEBUG_PROFILE" \
    --no-first-run \
    --no-default-browser-check \
    "https://x.com" &

sleep 3

# Verificar se a porta está aberta
if lsof -i :9222 > /dev/null 2>&1; then
    echo ""
    echo "✅ Chrome iniciado com sucesso na porta 9222!"
    echo ""
    echo "📋 Agora:"
    echo "   1. Verifique se você está logado no X na janela do Chrome"
    echo "   2. Em OUTRO terminal, rode: ./venv/bin/python -m streamlit run app/main.py"
    echo "   3. No Streamlit, clique 'Conectar ao Chrome' e 'Iniciar Coleta'"
    echo ""
    echo "⚠️  Mantenha esta janela aberta durante a coleta."
else
    echo ""
    echo "❌ Erro: Chrome não iniciou corretamente."
    echo "   Tente fechar manualmente todas as janelas do Chrome e rodar novamente."
fi
