# 🎯 Guia de Uso - X-Collector

## 📋 Índice
1. [Instalação](#instalação)
2. [Como Exportar Cookies do X](#como-exportar-cookies-do-x)
3. [Como Usar a Interface Web](#como-usar-a-interface-web)
4. [Testando o Sistema](#testando-o-sistema)
5. [Soluç ão de Problemas](#solução-de-problemas)

---

## 🚀 Instalação

### 1. Instalar Dependências do Python

```bash
# Navegar para o diretório do projeto
cd x-collector

# Instalar dependências
pip install -r requirements.txt

# Instalar Playwright browsers
playwright install chromium
```

### 2. (Opcional) Instalar Dependências do Sistema

Se você estiver em um servidor Linux sem interface gráfica, pode precisar instalar as bibliotecas do sistema:

```bash
# Executar como root
sudo bash install_dependencies.sh
```

---

## 🍪 Como Exportar Cookies do X

### Passo 1: Instalar Extensão de Cookies

Escolha uma das extensões abaixo para o seu navegador:

**Chrome/Edge:**
- [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
- [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)

**Firefox:**
- [Cookie-Editor](https://addons.mozilla.org/pt-BR/firefox/addon/cookie-editor/)

### Passo 2: Fazer Login no X

1. Abra https://x.com no seu navegador
2. Faça login normalmente com suas credenciais
3. Certifique-se de estar na página inicial (https://x.com/home)

### Passo 3: Exportar os Cookies

#### Usando EditThisCookie:

1. Clique no ícone da extensão EditThisCookie
2. Clique no botão de "Export" (ícone de documento com seta)
3. Os cookies serão copiados automaticamente para a área de transferência
4. Cole em um arquivo de texto temporário

#### Usando Cookie-Editor:

1. Clique no ícone da extensão Cookie-Editor
2. Clique no botão "Export" (canto inferior direito)
3. Selecione "JSON" como formato
4. Clique em "Export all" ou "Export current domain"
5. Copie o JSON exibido

### Exemplo de JSON de Cookies

O JSON exportado terá este formato:

```json
[
    {
        "domain": ".x.com",
        "expirationDate": 1803302661.040502,
        "hostOnly": false,
        "httpOnly": true,
        "name": "auth_token",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": true,
        "session": false,
        "value": "abc123def456..."
    },
    {
        "domain": ".x.com",
        "name": "ct0",
        "value": "xyz789...",
        ...
    }
]
```

⚠️ **IMPORTANTE:**
- Exporte TODOS os cookies do domínio `.x.com`
- Não compartilhe seus cookies com ninguém!
- Eles dão acesso total à sua conta do X

---

## 🖥️ Como Usar a Interface Web

### 1. Iniciar o Servidor Streamlit

```bash
# No diretório do projeto
streamlit run app/main.py
```

Isso abrirá automaticamente o navegador em `http://localhost:8501`

### 2. Importar Cookies

1. Na interface web, vá até a seção **"🍪 Login no X via Cookies"**
2. Clique em **"📥 Importar Cookies do X"** para expandir o formulário
3. Cole o JSON dos cookies que você exportou
4. Clique no botão **"💾 Importar Cookies"**
5. Aguarde a validação automática
6. Se tudo estiver correto, você verá: **"🎉 Login validado com sucesso!"**

### 3. Configurar a Coleta

1. Volte ao topo da página
2. Em **"📝 Pesquisa (Query)"**, digite sua busca. Exemplos:
   - `elon musk` - Buscar posts mencionando "elon musk"
   - `from:elonmusk` - Posts do usuário @elonmusk
   - `#python` - Posts com a hashtag #python
   - `bitcoin since:2024-01-01` - Posts sobre Bitcoin desde 01/01/2024

3. Configure os parâmetros:
   - **Ordenação:** Mais recentes ou Mais relevantes
   - **Quantidade máxima:** Número de posts para coletar (ex: 100)
   - **Período:** Opcional, limita por tempo
   - **Idioma:** Opcional, filtra por idioma

4. Escolha os formatos de exportação:
   - ☑️ DOCX (Word)
   - ☑️ JSON
   - ☑️ CSV

### 4. Iniciar a Coleta

1. Clique no botão **"🚀 Iniciar Coleta"**
2. Aguarde enquanto o sistema:
   - Inicia o navegador headless
   - Carrega seus cookies
   - Verifica o login
   - Navega para a busca
   - Coleta os posts via scroll
3. Acompanhe o progresso no **"📋 Log de Execução"**

### 5. Baixar os Resultados

Após a coleta:

1. Veja as estatísticas na seção **"📊 Resultado"**
2. Role até **"📥 Download dos Arquivos"**
3. Clique nos botões para baixar nos formatos escolhidos:
   - **📄 Baixar DOCX**
   - **📊 Baixar JSON**
   - **📊 Baixar CSV**

---

## 🧪 Testando o Sistema

### Teste Básico

1. **Importar cookies:**
   ```
   - Acesse x.com e faça login
   - Exporte cookies com extensão
   - Cole no formulário da interface
   - Clique em "Importar Cookies"
   - Verifique mensagem de sucesso
   ```

2. **Fazer uma busca simples:**
   ```
   Busca: python
   Quantidade: 10 posts
   Formato: JSON

   Clique em "Iniciar Coleta"
   ```

3. **Verificar resultados:**
   ```
   - Ver log de execução
   - Verificar número de posts coletados
   - Baixar arquivo JSON
   - Abrir e verificar conteúdo
   ```

### Teste de Login

Para verificar se seus cookies estão funcionando:

1. Vá até **"🍪 Login no X via Cookies"**
2. Se você já importou cookies, clique em **"🔍 Verificar Login"**
3. Aguarde a verificação
4. Resultado esperado: **"🎉 Você está logado no X!"**

Se aparecer **"❌ Sessão expirada"**:
- Seus cookies expiraram
- Faça logout e login novamente no X
- Exporte novos cookies
- Importe no sistema

---

## 🔧 Solução de Problemas

### Problema: "Erro ao importar cookies"

**Possíveis causas:**
- JSON inválido
- Cookies de domínio errado

**Solução:**
1. Verifique se copiou TODO o JSON
2. Certifique-se de que os cookies são do domínio `.x.com`
3. Tente exportar novamente

### Problema: "Sessão expirada"

**Causa:**
- Os cookies importados expiraram

**Solução:**
1. No X, faça logout e login novamente
2. Exporte novos cookies
3. Importe no sistema
4. Teste com "Verificar Login"

### Problema: "Erro ao iniciar navegador"

**Causa:**
- Faltam dependências do sistema

**Solução:**
```bash
# Linux/Ubuntu
sudo bash install_dependencies.sh

# Reinstalar Chromium do Playwright
playwright install chromium
```

### Problema: "Nenhum post coletado"

**Possíveis causas:**
- Busca muito específica
- Filtros muito restritivos
- Bloqueio do X (rate limit)

**Solução:**
1. Tente uma busca mais ampla
2. Remova filtros (replies, reposts)
3. Aguarde alguns minutos e tente novamente
4. Verifique se não há CAPTCHA ou bloqueio

### Problema: "Rate limit detected"

**Causa:**
- Você fez muitas requisições em pouco tempo

**Solução:**
1. Aguarde 15-30 minutos
2. Reduza a quantidade de posts por coleta
3. Aumente o intervalo entre coletas
4. Use com moderação

---

## 📚 Exemplos de Pesquisas

### Busca por Palavra-chave
```
python
```

### Busca por Usuário
```
from:elonmusk
```

### Busca com Data
```
bitcoin since:2024-01-01 until:2024-12-31
```

### Busca Avançada
```
from:elonmusk since:2024-01-01 -filter:replies
```

### Busca por Hashtag
```
#AI OR #MachineLearning
```

### Busca com Filtros
```
python (tutorial OR guide) -retweets
```

---

## ⚙️ Configurações Avançadas

### Variáveis de Ambiente

Crie um arquivo `.env` no diretório do projeto:

```env
# Diretório para dados do browser
BROWSER_DATA_DIR=./browser_data

# Configurações de email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
```

### Agendamento de Coletas

1. Acesse a aba **"📅 Agendamentos"**
2. Configure coletas automáticas:
   - Uma vez (data/hora específica)
   - Recorrente (ex: todo dia às 9h)
3. Escolha formatos e destinatários de email
4. Ative o agendamento

---

## 🎉 Pronto!

Agora você está pronto para usar o X-Collector!

**Dicas finais:**
- ✅ Mantenha seus cookies atualizados
- ✅ Use buscas específicas para melhores resultados
- ✅ Respeite os limites do X (não abuse)
- ✅ Faça backup dos seus dados coletados

**Precisa de ajuda?**
- Abra uma issue no GitHub
- Consulte a documentação completa
- Veja os logs de execução para detalhes de erros
