# 🧪 Como Testar o X-Collector - Guia Passo a Passo

## 📋 Visão Geral

Este guia vai te orientar **do zero** até a primeira coleta de posts funcionando!

**Tempo estimado:** 10-15 minutos
**Dificuldade:** ⭐ Fácil (mesmo para iniciantes)

---

## 🎯 Pré-requisitos

Antes de começar, certifique-se de ter:

- ✅ Python 3.11 ou superior instalado
- ✅ Conta no X (Twitter) ativa
- ✅ Navegador Chrome, Edge ou Firefox
- ✅ Conexão com internet

---

## 📥 Passo 1: Instalar o Projeto

### 1.1. Clonar o Repositório

```bash
# Abra o terminal e execute:
git clone https://github.com/ThiagoPax/x-collector.git
cd x-collector
```

✅ **Resultado esperado:** Você deve estar dentro da pasta `x-collector`

### 1.2. Instalar Dependências do Python

```bash
# Instalar bibliotecas Python
pip install -r requirements.txt

# Instalar Chromium do Playwright
playwright install chromium
```

✅ **Resultado esperado:** Mensagem "Successfully installed..." e "Chromium downloaded"

### 1.3. (Opcional) Instalar Dependências do Sistema

**Somente se você estiver em um servidor Linux sem interface gráfica:**

```bash
sudo bash install_dependencies.sh
```

**Se você está no Windows ou Mac, pule este passo!**

✅ **Resultado esperado:** Mensagem "✅ Dependências instaladas com sucesso!"

---

## 🍪 Passo 2: Exportar Cookies do X

### 2.1. Instalar Extensão de Cookies

**Chrome/Edge:**
1. Acesse: https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
2. Clique em "Adicionar ao Chrome/Edge"
3. Confirme a instalação

**Firefox:**
1. Acesse: https://addons.mozilla.org/pt-BR/firefox/addon/cookie-editor/
2. Clique em "Adicionar ao Firefox"
3. Confirme a instalação

✅ **Resultado esperado:** Ícone da extensão aparece ao lado da barra de endereço

### 2.2. Fazer Login no X

1. Abra uma nova aba no navegador
2. Acesse: https://x.com
3. Faça login com seu usuário e senha
4. Certifique-se de estar na página inicial (https://x.com/home)

✅ **Resultado esperado:** Você está logado e vendo sua timeline

### 2.3. Exportar os Cookies

1. **Clique no ícone da extensão Cookie-Editor** (ao lado da barra de endereço)
2. **Clique em "Export"** (canto inferior direito)
3. **Selecione "JSON"** como formato
4. **Clique em "Export all"**
5. O JSON será exibido - **clique em "Copy"** ou selecione tudo (Ctrl+A) e copie (Ctrl+C)

✅ **Resultado esperado:** JSON copiado para a área de transferência. Deve parecer com:

```json
[
    {
        "domain": ".x.com",
        "name": "auth_token",
        "value": "abc123...",
        ...
    },
    ...
]
```

⚠️ **IMPORTANTE:**
- Não compartilhe esses cookies com ninguém!
- Eles dão acesso total à sua conta do X
- Guarde-os em segurança

---

## 🖥️ Passo 3: Iniciar a Interface Web

### 3.1. Abrir o Terminal

Volte ao terminal onde você clonou o projeto.

### 3.2. Iniciar o Streamlit

```bash
streamlit run app/main.py
```

✅ **Resultado esperado:**
- Mensagens no terminal dizendo "You can now view your Streamlit app..."
- Navegador abre automaticamente em `http://localhost:8501`
- Interface do X-Collector aparece

**Se o navegador não abrir automaticamente, acesse manualmente:**
http://localhost:8501

---

## 🔑 Passo 4: Importar Cookies na Interface

### 4.1. Localizar a Seção de Cookies

1. Na interface web, **role a página para baixo**
2. Encontre a seção **"🍪 Login no X via Cookies"**
3. Clique em **"📥 Importar Cookies do X"** para expandir

✅ **Resultado esperado:** Formulário de importação aparece com textarea

### 4.2. Colar os Cookies

1. **Clique na textarea grande** (onde diz "Cole o JSON dos cookies aqui:")
2. **Cole o JSON** que você copiou antes (Ctrl+V ou Cmd+V)
3. **Clique no botão "💾 Importar Cookies"**

✅ **Resultado esperado:**
- Mensagem "✅ Importação concluída! X cookies salvos"
- Mensagem "🎉 Login validado com sucesso! Você está logado no X."
- Página recarrega automaticamente

### 4.3. Verificar Importação

Após o recarregamento, você deve ver:

```
✅ Cookies importados: 12 cookies (em 18/01/2026 às 15:05:06)
```

E dois botões:
- 🔍 Verificar Login
- 🗑️ Deletar

**Teste o botão "🔍 Verificar Login":**
- Clique nele
- Aguarde alguns segundos
- Deve aparecer: **"🎉 Você está logado no X!"**

✅ **Resultado esperado:** Login confirmado!

---

## 🚀 Passo 5: Fazer sua Primeira Coleta

### 5.1. Role para o Topo da Página

Você verá a seção **"📥 Coleta Manual de Posts"**

### 5.2. Configurar a Busca

**📝 Pesquisa (Query):**
- Digite: `python`
  (Ou qualquer palavra-chave que você quiser)

**⚙️ Parâmetros de Coleta:**
- **Ordenação:** 🕐 Mais recentes (deixe marcado)
- **Quantidade máxima de posts:** 10
  (Para o primeiro teste, use apenas 10!)
- **Período de tempo:** Sem limite de tempo
- **Idioma:** 🌍 Todos os idiomas

**📄 Formatos de Exportação:**
- Marque: ☑️ JSON
- (Para o teste, só JSON é suficiente)

**📧 Envio por E-mail:**
- Deixe em branco por enquanto

✅ **Resultado esperado:** Formulário preenchido

### 5.3. Iniciar a Coleta

1. **Clique no botão "🚀 Iniciar Coleta"** (botão verde grande)
2. Aguarde... você verá:
   - "🚀 Iniciando navegador headless..."
   - "✅ Navegador iniciado!"
   - "🔍 Verificando login..."
   - "✅ Login confirmado!"
   - "📥 Iniciando coleta..."
   - "Scroll #1 - Posts coletados: X"
   - "Scroll #2 - Posts coletados: X"
   - ...

3. Acompanhe o progresso no **"📋 Log de Execução"**

✅ **Resultado esperado:**
- Coleta completa em 20-40 segundos
- Mensagem final: "✅ Coleta finalizada! Total: 10 posts"

### 5.4. Ver os Resultados

Após a coleta, você verá:

**📊 Resultado: 10 posts coletados**

Com métricas:
- Total de Posts: 10
- Tempo de Coleta: X.Xs
- Motivo da Parada: Limite atingido
- Erros: 0

**📈 Engajamento Total:**
- ❤️ Curtidas: XXX
- 🔁 Reposts: XXX
- 👁️ Visualizações: XXX
- 💬 Respostas: XXX

**📝 Posts Coletados:**
- Lista com os 10 posts
- Autor, data, conteúdo, métricas

**📥 Download dos Arquivos:**
- Botão: **📊 Baixar JSON**

✅ **Resultado esperado:** Todos os dados aparecem corretamente!

### 5.5. Baixar o Arquivo JSON

1. Role até **"📥 Download dos Arquivos"**
2. Clique em **"📊 Baixar JSON"**
3. O arquivo `posts_YYYYMMDD_HHMMSS.json` será baixado

✅ **Resultado esperado:** Arquivo JSON baixado na pasta de Downloads

### 5.6. Verificar o Arquivo

1. Abra o arquivo JSON em um editor de texto
2. Você deve ver algo como:

```json
{
  "posts": [
    {
      "id": "123...",
      "author": {
        "username": "usuario123",
        "display_name": "Nome do Usuário",
        ...
      },
      "content": "Texto do post sobre python...",
      "created_at": "2026-01-18T...",
      "metrics": {
        "likes": 42,
        "reposts": 5,
        ...
      }
    },
    ...
  ],
  "total_collected": 10,
  ...
}
```

✅ **Resultado esperado:** JSON válido com 10 posts!

---

## 🎉 Parabéns! Você completou o teste!

Se você chegou até aqui com sucesso, significa que:

- ✅ O sistema está instalado corretamente
- ✅ Os cookies foram importados com sucesso
- ✅ O navegador headless está funcionando
- ✅ A coleta de posts está operacional
- ✅ Os dados estão sendo exportados corretamente

---

## 🧪 Próximos Testes (Opcional)

### Teste 2: Busca por Usuário

```
Busca: from:elonmusk
Posts: 20
```

Resultado esperado: 20 posts de @elonmusk

### Teste 3: Busca com Data

```
Busca: bitcoin since:2024-01-01 until:2024-12-31
Posts: 50
```

Resultado esperado: Posts sobre Bitcoin em 2024

### Teste 4: Exportar em Múltiplos Formatos

```
Busca: AI
Posts: 30
Formatos: ☑️ DOCX ☑️ JSON ☑️ CSV
```

Resultado esperado: 3 arquivos baixados

### Teste 5: Verificar Login Expirado

1. No X, faça logout
2. Na interface, clique em "🔍 Verificar Login"
3. Resultado esperado: "❌ Sessão expirada"
4. Importe novos cookies
5. Teste novamente

---

## ❓ Troubleshooting

### Problema: "Você precisa importar seus cookies do X antes de coletar posts!"

**Solução:**
1. Volte ao Passo 2 e exporte novos cookies
2. Importe-os na seção "🍪 Login no X via Cookies"

### Problema: "Não está logado no X. Seus cookies podem estar expirados."

**Solução:**
1. No X, faça logout e login novamente
2. Exporte novos cookies
3. Importe na interface
4. Teste com "Verificar Login"

### Problema: "Erro ao iniciar navegador"

**Solução:**
```bash
# Reinstalar Chromium
playwright install chromium

# Se ainda não funcionar (apenas Linux):
sudo bash install_dependencies.sh
```

### Problema: "Nenhum post coletado"

**Soluções:**
1. Tente uma busca mais ampla (ex: apenas "python")
2. Aumente o número de posts (ex: 50)
3. Verifique se não há bloqueio (aguarde 15 minutos e tente novamente)

### Problema: Streamlit não abre

**Solução:**
1. Verifique se a porta 8501 está livre
2. Ou acesse manualmente: http://localhost:8501
3. Ou use outra porta:
```bash
streamlit run app/main.py --server.port 8502
```

---

## 📚 Próximos Passos

Agora que você testou e o sistema está funcionando, você pode:

1. **Explorar Recursos Avançados:**
   - Leia o [GUIA_DE_USO.md](GUIA_DE_USO.md) completo
   - Configure agendamentos automáticos
   - Configure envio por email

2. **Fazer Buscas Mais Complexas:**
   - Consulte exemplos em [README.md](README.md)
   - Aprenda operadores avançados do X

3. **Integrar com seus Projetos:**
   - Use os arquivos JSON/CSV exportados
   - Analise os dados com pandas/python
   - Crie dashboards

---

## 🆘 Precisa de Ajuda?

Se você encontrou algum problema não listado aqui:

1. **Consulte a documentação:**
   - [README.md](README.md)
   - [GUIA_DE_USO.md](GUIA_DE_USO.md)
   - [ESTRATEGIAS.md](ESTRATEGIAS.md)

2. **Verifique os logs:**
   - Veja o "📋 Log de Execução" na interface
   - Veja o terminal onde você rodou `streamlit run`

3. **Abra uma issue:**
   - https://github.com/ThiagoPax/x-collector/issues

---

**✨ Divirta-se coletando dados do X!**
