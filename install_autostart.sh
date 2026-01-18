#!/bin/bash
# ===========================================
# INSTALAR AUTO-START NO macOS
# ===========================================
# Este script configura o X Collector para iniciar
# automaticamente quando você ligar o Mac

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.tssouza.xcollector.plist"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

echo "🔧 Configurando Auto-Start do X Collector"
echo "=========================================="
echo ""

# Criar diretório LaunchAgents se não existir
mkdir -p "$LAUNCH_AGENTS"

# Parar serviço se existir
launchctl unload "$LAUNCH_AGENTS/$PLIST_NAME" 2>/dev/null || true

# Copiar plist
sed "s|~/Desktop/x-collector|$SCRIPT_DIR|g" "$SCRIPT_DIR/$PLIST_NAME" > "$LAUNCH_AGENTS/$PLIST_NAME"

# Dar permissão
chmod 644 "$LAUNCH_AGENTS/$PLIST_NAME"

# Carregar serviço
launchctl load "$LAUNCH_AGENTS/$PLIST_NAME"

echo "✅ Auto-start configurado!"
echo ""
echo "📋 O X Collector agora iniciará automaticamente quando você:"
echo "   - Ligar o Mac"
echo "   - Fazer login"
echo ""
echo "🌐 Acesse: http://localhost:8501"
echo ""
echo "📋 Comandos úteis:"
echo "   Iniciar agora:    ./service.sh start"
echo "   Parar:            ./service.sh stop"
echo "   Status:           ./service.sh status"
echo "   Remover auto-start: launchctl unload ~/Library/LaunchAgents/$PLIST_NAME"
