# 🐦 X Posts Collector v2.0

Coletor automatizado de posts do X (Twitter) com análise inteligente usando OpenAI.

## ✨ Funcionalidades

- ✅ Coleta até **10.000 posts** por pesquisa
- ✅ **Top 5 posts** com maior engajamento destacados
- ✅ **Total de visualizações** e métricas completas
- ✅ **Relatório diagnóstico** com IA (OpenAI)
- ✅ Exportação para DOCX, JSON, CSV
- ✅ Envio automático por e-mail
- ✅ Agendamentos recorrentes
- ✅ Interface 100% em português

---

## 🚀 Instalação Rápida (macOS)

```bash
cd ~/Desktop
unzip x-collector.zip
cd x-collector
chmod +x *.sh
bash setup_and_run.sh
```

---

## 🖥️ Opção 1: Uso Manual (dois terminais)

### Terminal 1 - Chrome:
```bash
cd ~/Desktop/x-collector
./start_chrome.sh
```

### Terminal 2 - Streamlit:
```bash
cd ~/Desktop/x-collector
./venv/bin/python -m streamlit run app/main.py
```

Acesse: http://localhost:8501

---

## 🔄 Opção 2: Serviço em Background (um comando)

Inicia tudo automaticamente e fica rodando em background:

```bash
cd ~/Desktop/x-collector
chmod +x service.sh
./service.sh start
```

**Comandos:**
- `./service.sh start` - Inicia em background
- `./service.sh stop` - Para o serviço
- `./service.sh status` - Verifica status
- `./service.sh restart` - Reinicia

---

## 🚀 Opção 3: Auto-Start (inicia com o Mac)

Para que o X Collector inicie automaticamente quando você ligar o Mac:

```bash
cd ~/Desktop/x-collector
chmod +x install_autostart.sh
./install_autostart.sh
```

Depois de instalar, o serviço inicia sozinho no login!

---

## 🌐 Opção 4: Deploy em Servidor (online 24/7)

Para deixar acessível via domínio (ex: tssouza.com):

### Requisitos:
- VPS (DigitalOcean, Linode, AWS, etc.)
- Domínio apontando para o IP do servidor

### Deploy:
```bash
# No servidor
git clone [seu-repo] x-collector
cd x-collector
chmod +x deploy.sh
./deploy.sh
```

### Configurar DNS:
No Google Workspace (ou seu provedor DNS):
- Tipo: A
- Nome: @ ou collector
- Valor: IP do seu servidor

---

## ⚙️ Configuração

### Arquivo .env:
```env
# E-mail (AOL já configurado)
SMTP_HOST=smtp.aol.com
SMTP_PORT=587
SMTP_USER=seu_email@aol.com
SMTP_PASS=sua_senha_app
FROM_EMAIL=seu_email@aol.com

# OpenAI (para análise com IA)
OPENAI_API_KEY=sk-proj-xxx...
```

---

## 📊 Relatório de Diagnóstico

O sistema gera automaticamente um relatório com:

| Seção | Descrição |
|-------|-----------|
| 📈 Métricas | Total de posts, curtidas, reposts, **VIEWS** |
| 🏆 Top 5 Posts | Os 5 posts com mais engajamento |
| 💎 Valor Percebido | Análise do valor para o público |
| 📌 Mensagem Principal | Tema central identificado |
| ✅ Pontos Positivos | O que funcionou bem |
| ❌ Pontos Negativos | Limitações identificadas |
| 💡 Observações | Recomendações para decisão |

---

## 📁 Estrutura do Projeto

```
x-collector/
├── app/main.py           # Interface Streamlit
├── core/
│   ├── collector.py      # Motor de coleta
│   ├── analyzer.py       # Análise com OpenAI
│   └── models.py         # Modelos de dados
├── exporters/            # Exportação DOCX/JSON/CSV
├── email_service/        # Envio de e-mails
├── scheduler/            # Agendamentos
├── service.sh            # Gerenciador de serviço
├── deploy.sh             # Script de deploy
├── Dockerfile            # Container Docker
└── docker-compose.yml    # Orquestração
```

---

## 🔧 Solução de Problemas

### "Chrome não conecta"
```bash
./service.sh restart
```

### "Módulo não encontrado"
```bash
./venv/bin/pip install -r requirements.txt
```

### Ver logs:
```bash
tail -f collector.log
```

---

## 📞 Suporte

Para dúvidas ou problemas, verifique os logs em `collector.log`.
