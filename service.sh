#!/bin/bash
# ===========================================
# X COLLECTOR - INICIAR COMO SERVIÇO (macOS)
# ===========================================
# Este script inicia o X Collector em background
# e fica rodando mesmo após fechar o terminal

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Arquivo de PID
PID_FILE="$SCRIPT_DIR/.collector.pid"
LOG_FILE="$SCRIPT_DIR/collector.log"

start_service() {
    echo "🚀 Iniciando X Collector em background..."
    
    # Verificar se já está rodando
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "⚠️  X Collector já está rodando (PID: $OLD_PID)"
            echo "   Use: $0 stop   para parar"
            echo "   Use: $0 restart   para reiniciar"
            exit 1
        fi
    fi
    
    # Verificar venv
    if [ ! -d "venv" ]; then
        echo "📦 Criando ambiente virtual..."
        /usr/bin/python3 -m venv venv
        ./venv/bin/pip install -q -r requirements.txt
        ./venv/bin/playwright install chromium
    fi
    
    # Matar Chrome debug existente se houver
    pkill -f "remote-debugging-port=9222" 2>/dev/null || true
    sleep 1
    
    # Copiar perfil do Chrome
    CHROME_PROFILE="$HOME/Library/Application Support/Google/Chrome"
    DEBUG_PROFILE="$HOME/.x-collector-chrome-profile"
    
    if [ -d "$CHROME_PROFILE" ]; then
        echo "📂 Preparando perfil do Chrome..."
        rm -rf "$DEBUG_PROFILE"
        mkdir -p "$DEBUG_PROFILE"
        cp -R "$CHROME_PROFILE/Default" "$DEBUG_PROFILE/" 2>/dev/null || true
        cp "$CHROME_PROFILE/Local State" "$DEBUG_PROFILE/" 2>/dev/null || true
    fi
    
    # Iniciar Chrome em background
    echo "🌐 Iniciando Chrome..."
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
        --remote-debugging-port=9222 \
        --user-data-dir="$DEBUG_PROFILE" \
        --no-first-run \
        --no-default-browser-check \
        --headless=new \
        > /dev/null 2>&1 &
    
    CHROME_PID=$!
    sleep 3
    
    # Iniciar Streamlit em background
    echo "📊 Iniciando Streamlit..."
    nohup ./venv/bin/python -m streamlit run app/main.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        > "$LOG_FILE" 2>&1 &
    
    STREAMLIT_PID=$!
    echo "$STREAMLIT_PID" > "$PID_FILE"
    
    sleep 3
    
    # Verificar se está rodando
    if ps -p $STREAMLIT_PID > /dev/null 2>&1; then
        echo ""
        echo "✅ X Collector iniciado com sucesso!"
        echo ""
        echo "🌐 Acesse: http://localhost:8501"
        echo "🌐 Ou na rede: http://$(ipconfig getifaddr en0):8501"
        echo ""
        echo "📋 Comandos:"
        echo "   Ver logs:   tail -f $LOG_FILE"
        echo "   Parar:      $0 stop"
        echo "   Status:     $0 status"
        echo ""
    else
        echo "❌ Falha ao iniciar. Verifique os logs: $LOG_FILE"
        exit 1
    fi
}

stop_service() {
    echo "🛑 Parando X Collector..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            echo "✅ Streamlit parado (PID: $PID)"
        fi
        rm "$PID_FILE"
    fi
    
    # Parar Chrome debug
    pkill -f "remote-debugging-port=9222" 2>/dev/null && echo "✅ Chrome parado" || true
    
    echo "✅ Serviço parado!"
}

status_service() {
    echo "📊 Status do X Collector:"
    echo ""
    
    # Verificar Streamlit
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Streamlit: Rodando (PID: $PID)"
        else
            echo "❌ Streamlit: Parado (PID antigo: $PID)"
        fi
    else
        echo "❌ Streamlit: Parado"
    fi
    
    # Verificar Chrome
    if pgrep -f "remote-debugging-port=9222" > /dev/null; then
        echo "✅ Chrome Debug: Rodando"
    else
        echo "❌ Chrome Debug: Parado"
    fi
    
    # Verificar porta
    if lsof -i :8501 > /dev/null 2>&1; then
        echo "✅ Porta 8501: Em uso"
        echo ""
        echo "🌐 Acesse: http://localhost:8501"
    else
        echo "❌ Porta 8501: Livre"
    fi
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 2
        start_service
        ;;
    status)
        status_service
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status}"
        echo ""
        echo "Comandos:"
        echo "  start   - Inicia o X Collector em background"
        echo "  stop    - Para o serviço"
        echo "  restart - Reinicia o serviço"
        echo "  status  - Mostra status do serviço"
        exit 1
        ;;
esac
