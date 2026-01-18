#!/bin/bash
# ===========================================
# X COLLECTOR - DEPLOY PARA SERVIDOR
# ===========================================
# Este script configura o X Collector em um servidor
# para ficar online 24/7 no domínio tssouza.com

set -e

echo "🐦 X Posts Collector - Deploy para Servidor"
echo "============================================"
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "📦 Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker instalado! Faça logout e login novamente, depois rode este script de novo."
    exit 0
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Instalando Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "✅ Docker e Docker Compose instalados!"
echo ""

# Criar diretório SSL
mkdir -p ssl

# Verificar se tem certificados SSL
if [ ! -f "ssl/fullchain.pem" ]; then
    echo "⚠️  Certificados SSL não encontrados."
    echo ""
    echo "Para usar HTTPS com seu domínio, instale o Certbot:"
    echo ""
    echo "  sudo apt install certbot"
    echo "  sudo certbot certonly --standalone -d tssouza.com -d www.tssouza.com"
    echo ""
    echo "Depois copie os certificados:"
    echo "  sudo cp /etc/letsencrypt/live/tssouza.com/fullchain.pem ssl/"
    echo "  sudo cp /etc/letsencrypt/live/tssouza.com/privkey.pem ssl/"
    echo ""
    echo "Por enquanto, vou iniciar apenas com HTTP na porta 8501..."
    echo ""
    
    USE_NGINX=false
else
    echo "✅ Certificados SSL encontrados!"
    USE_NGINX=true
fi

# Verificar arquivo .env
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "Copie o .env.example e configure suas credenciais."
    exit 1
fi

echo ""
echo "🚀 Iniciando build e deploy..."
echo ""

# Build da imagem
docker-compose build

# Iniciar serviços
if [ "$USE_NGINX" = true ]; then
    docker-compose --profile with-nginx up -d
    echo ""
    echo "✅ Deploy completo!"
    echo ""
    echo "🌐 Acesse: https://tssouza.com"
else
    docker-compose up -d
    echo ""
    echo "✅ Deploy completo!"
    echo ""
    echo "🌐 Acesse: http://SEU_IP:8501"
fi

echo ""
echo "📋 Comandos úteis:"
echo "  Ver logs:        docker-compose logs -f"
echo "  Parar:           docker-compose down"
echo "  Reiniciar:       docker-compose restart"
echo "  Atualizar:       git pull && docker-compose up -d --build"
echo ""

# Configurar para iniciar no boot
echo "🔄 Configurando para iniciar automaticamente no boot..."
sudo systemctl enable docker

echo ""
echo "✅ Tudo pronto! O X Collector está rodando online."
