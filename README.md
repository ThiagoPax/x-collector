# 🐦 X-Collector - Coletor de Posts do X (Twitter)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.48.0-green.svg)](https://playwright.dev/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.40.0-red.svg)](https://streamlit.io/)

> Sistema profissional de coleta de posts do X (Twitter) com interface web, coleta via cookies e exportação múltipla.

## ✨ Características

- 🍪 **Login via Cookies** - Autenticação simples exportando cookies do navegador
- 🌐 **100% Headless** - Funciona sem interface gráfica
- 📊 **Interface Web Intuitiva** - Painel Streamlit completo
- 📥 **Exportação Múltipla** - DOCX, JSON e CSV
- ⏰ **Agendamento** - Coletas automáticas programadas
- 📧 **Email** - Envio automático de resultados
- 🔍 **Busca Avançada** - Suporte completo a operadores do X
- 🚀 **Alto Desempenho** - Coleta rápida via Playwright

## 🎯 O Que Foi Implementado

### ✅ Sistema de Login Via Cookies (100% Funcional)

- Importação de cookies do navegador (EditThisCookie/Cookie-Editor)
- Validação automática de sessão
- Persistência de cookies entre execuções
- Verificação de login em tempo real
- Interface web completa para gerenciamento

### ✅ Modo Headless Simplificado

- **Removido:** CDP (Chrome DevTools Protocol)
- **Removido:** start_chrome.sh e gerenciamento manual do Chrome
- **Removido:** Xvfb e dependências de display virtual
- **Novo:** Playwright puro em modo headless
- **Novo:** Inicialização automática do navegador
- **Novo:** Carregamento automático de cookies

### ✅ Interface Simplificada

- Removido gerenciamento manual do Chromium
- Removido botões de "Conectar/Desconectar"
- Novo fluxo: Importar Cookies → Iniciar Coleta
- Mensagens claras e intuitivas
- Validação em tempo real

## 📋 Pré-requisitos

- Python 3.11+
- pip (gerenciador de pacotes Python)
- Conta no X (Twitter)

## 🚀 Instalação Rápida

### 1. Clonar o Repositório

```bash
git clone https://github.com/ThiagoPax/x-collector.git
cd x-collector
```

### 2. Instalar Dependências Python

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. (Opcional) Instalar Dependências do Sistema

Apenas se estiver em um servidor Linux sem interface gráfica:

```bash
sudo bash install_dependencies.sh
```

### 4. Iniciar a Interface Web

```bash
streamlit run app/main.py
```

Acesse: http://localhost:8501

## 📖 Guia de Uso Completo

Consulte o [GUIA_DE_USO.md](GUIA_DE_USO.md) para:
- Como exportar cookies do X
- Como usar a interface web
- Exemplos de pesquisas
- Solução de problemas
- Configurações avançadas

## 🍪 Login Via Cookies (Passo a Passo)

### 1. Exportar Cookies do X

1. Acesse https://x.com e faça login
2. Instale a extensão [Cookie-Editor](https://cookie-editor.cgagnier.ca/)
3. Clique na extensão e exporte os cookies como JSON
4. Copie o JSON

### 2. Importar na Interface Web

1. Abra a interface: `streamlit run app/main.py`
2. Vá até **"🍪 Login no X via Cookies"**
3. Cole o JSON na textarea
4. Clique em **"💾 Importar Cookies"**
5. Aguarde a validação (será testado automaticamente!)

### 3. Começar a Coletar

1. Digite uma busca (ex: `python`)
2. Configure quantidade de posts (ex: 100)
3. Escolha formatos de exportação
4. Clique em **"🚀 Iniciar Coleta"**

Pronto! O navegador headless será iniciado automaticamente com seus cookies.

## 📊 Exemplos de Uso

### Busca Simples

```
Busca: python
Posts: 100
Resultado: 100 posts sobre Python
```

### Busca por Usuário

```
Busca: from:elonmusk
Posts: 50
Resultado: 50 posts de @elonmusk
```

### Busca com Data

```
Busca: bitcoin since:2024-01-01 until:2024-12-31
Posts: 200
Resultado: Posts sobre Bitcoin em 2024
```

### Busca Avançada

```
Busca: from:elonmusk since:2024-01-01 -filter:replies
Posts: 100
Resultado: Posts originais de @elonmusk em 2024
```

## 🗂️ Estrutura do Projeto

```
x-collector/
├── app/
│   └── main.py              # Interface Streamlit
├── core/
│   ├── collector.py         # Coletor simplificado (headless puro)
│   ├── cookie_manager.py    # Gerenciamento de cookies
│   ├── models.py            # Modelos de dados
│   ├── extractor.py         # Extração de posts
│   └── url_builder.py       # Construção de URLs
├── exporters/
│   ├── docx_exporter.py     # Exportação para Word
│   ├── json_exporter.py     # Exportação para JSON
│   └── csv_exporter.py      # Exportação para CSV
├── scheduler/
│   └── runner.py            # Agendamento de coletas
├── browser_data/            # Cookies e dados do browser (gitignored)
├── install_dependencies.sh  # Script de instalação
├── requirements.txt         # Dependências Python
├── GUIA_DE_USO.md          # Guia completo
├── ESTRATEGIAS.md          # Análise de estratégias implementadas
└── README.md               # Este arquivo
```

## 🔧 Arquitetura

### Modo Headless Puro (Atual)

```
Interface Web (Streamlit)
    ↓
XCollector (Playwright headless)
    ↓
1. Carrega cookies salvos
2. Cria contexto do navegador
3. Navega para o X
4. Coleta posts via scroll
5. Retorna resultados
```

### Fluxo de Login

```
Usuário exporta cookies → Importa na UI → Cookies salvos em browser_data/cookies.json
                                              ↓
                                     Carregados automaticamente
                                     em todas as execuções
```

## 📈 Análise de Estratégias

Foram avaliadas **5 estratégias** diferentes. Veja detalhes completos em [ESTRATEGIAS.md](ESTRATEGIAS.md).

**Estratégia Escolhida:** Playwright Headless Puro + Login via Cookies

**Por quê?**
- ✅ Código mais simples e limpo
- ✅ Menos dependências
- ✅ Mais fácil de manter
- ✅ Funciona em qualquer ambiente
- ✅ Não depende de Chrome externo ou Xvfb

## 🛡️ Segurança

- ⚠️ **NUNCA compartilhe seus cookies!**
- ⚠️ Cookies dão acesso total à sua conta
- ⚠️ Use apenas em máquinas confiáveis
- ✅ Cookies são salvos localmente em `browser_data/cookies.json`
- ✅ Arquivo `browser_data/` está no `.gitignore`

## 📝 Limitações e Boas Práticas

### Limitações do X

- Rate limits: Não abuse das coletas
- Bloqueios: X pode bloquear atividade suspeita
- Cookies expiram: Reimporte periodicamente

### Boas Práticas

- ✅ Use intervalos entre coletas
- ✅ Limite a quantidade de posts por coleta
- ✅ Mantenha cookies atualizados
- ✅ Respeite os termos de uso do X

## 🔄 Atualização de Cookies

Se aparecer "Sessão expirada":

1. No X, faça logout e login novamente
2. Exporte novos cookies
3. Importe na interface
4. Teste com "Verificar Login"

## 📧 Configuração de Email (Opcional)

Crie um arquivo `.env`:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
```

Agora você pode receber resultados por email automaticamente!

## 🐛 Solução de Problemas

### "Erro ao importar cookies"
- Verifique se o JSON está completo
- Certifique-se de exportar do domínio `.x.com`

### "Sessão expirada"
- Reimporte cookies atualizados

### "Erro ao iniciar navegador"
- Execute: `sudo bash install_dependencies.sh`
- Reinstale Chromium: `playwright install chromium`

### "Nenhum post coletado"
- Verifique a busca (pode ser muito específica)
- Teste com busca mais ampla
- Aguarde se houver rate limit

## 🤝 Contribuindo

Contribuições são bem-vindas!

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📜 Licença

Este projeto é fornecido "como está", sem garantias. Use por sua conta e risco.

## ⚠️ Aviso Legal

Este projeto é apenas para fins educacionais. Respeite:
- Termos de Uso do X (Twitter)
- Leis de privacidade e proteção de dados
- Direitos autorais

O uso inadequado é de responsabilidade do usuário.

## 👨‍💻 Autor

Desenvolvido com ❤️ por [ThiagoPax](https://github.com/ThiagoPax)

---

**⭐ Se este projeto foi útil, deixe uma estrela no GitHub!**
