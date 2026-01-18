"""Interface principal do Coletor de Posts do X - Streamlit."""
from __future__ import annotations
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import time
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

from core import (
    XCollector,
    CollectionParams,
    SearchType,
    URLBuilder,
    build_example_queries,
    is_chrome_running,
    get_chrome_status,
    start_chrome,
    stop_chrome,
    restart_chrome,
    get_chrome_log,
)
from exporters import export_to_docx, export_to_json, export_to_csv
from scheduler import start_scheduler, get_runner
from email_service import test_email_config, send_collection_email

# Configuração da página
st.set_page_config(
    page_title="Coletor de Posts do X",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Iniciar scheduler em background
if "scheduler_started" not in st.session_state:
    start_scheduler()
    st.session_state.scheduler_started = True

# Estado da sessão
if "collection_result" not in st.session_state:
    st.session_state.collection_result = None
if "logs" not in st.session_state:
    st.session_state.logs = []
if "collecting" not in st.session_state:
    st.session_state.collecting = False


def add_log(msg: str):
    """Adiciona mensagem ao log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {msg}")


# === BARRA LATERAL ===
with st.sidebar:
    st.title("🐦 Coletor de Posts do X")
    st.markdown("---")
    
    # Navegação
    page = st.radio(
        "Navegação",
        ["📥 Coleta Manual", "📅 Agendamentos", "📊 Histórico", "⚙️ Configurações"],
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    
    # Status do sistema
    st.subheader("📡 Status do Sistema")
    
    # E-mail
    email_ok, email_msg = test_email_config()
    if email_ok:
        st.success("✉️ E-mail: Configurado")
    else:
        st.warning(f"✉️ E-mail: {email_msg}")
    
    # Scheduler
    runner = get_runner()
    if runner._running:
        st.success("⏰ Agendador: Ativo")
    else:
        st.error("⏰ Agendador: Parado")


# === PÁGINA: COLETA MANUAL ===
if page == "📥 Coleta Manual":
    st.title("📥 Coleta Manual de Posts")
    
    # Tipo de entrada
    input_type = st.radio(
        "Tipo de entrada",
        ["📝 Pesquisa (Query)", "🔗 URL do X"],
        horizontal=True,
        label_visibility="collapsed",
    )
    
    is_url = input_type == "🔗 URL do X"
    
    if not is_url:
        query_input = st.text_area(
            "Pesquisa avançada",
            placeholder="Ex: from:elonmusk since:2024-01-01 -filter:replies",
            height=100,
            help="Use operadores avançados do X para filtrar posts",
        )
        input_value = query_input
        
        # Mostrar exemplos
        with st.expander("📚 Ver exemplos de pesquisa"):
            examples = build_example_queries()
            for desc, query in examples.items():
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.write(f"**{desc}**")
                with col2:
                    st.code(query, language=None)
    else:
        url_input = st.text_input(
            "URL do X (página de busca ou perfil)",
            placeholder="https://x.com/search?q=...",
        )
        input_value = url_input
    
    st.markdown("---")
    
    # Parâmetros
    st.subheader("⚙️ Parâmetros de Coleta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_type = st.selectbox(
            "Ordenação",
            options=["latest", "top"],
            format_func=lambda x: "🕐 Mais recentes" if x == "latest" else "⭐ Mais relevantes",
        )
        
        max_posts = st.number_input(
            "Quantidade máxima de posts",
            min_value=10,
            max_value=10000,
            value=3000,
            step=100,
        )
    
    with col2:
        # Período em minutos (com opções pré-definidas)
        periodo_opcoes = {
            "Sem limite de tempo": 0,
            "Últimos 10 minutos": 10,
            "Última hora": 60,
            "Últimas 6 horas": 360,
            "Últimas 12 horas": 720,
            "Último dia (24h)": 1440,
            "Últimos 3 dias": 4320,
            "Última semana": 10080,
            "Personalizado (em minutos)": -1,
        }
        
        periodo_selecionado = st.selectbox(
            "⏱️ Período de tempo",
            options=list(periodo_opcoes.keys()),
            index=0,
            help="Filtrar posts por período de publicação",
        )
        
        max_minutes = periodo_opcoes[periodo_selecionado]
        
        # Se personalizado, mostrar campo de input
        if max_minutes == -1:
            max_minutes = st.number_input(
                "Minutos personalizados",
                min_value=1,
                max_value=525600,  # 1 ano em minutos
                value=60,
                help="Digite o número de minutos (ex: 30 = última meia hora)",
            )
        
        # Converter para None se for 0
        if max_minutes == 0:
            max_minutes = None
        
        language = st.selectbox(
            "Idioma dos posts",
            options=["", "pt", "en", "es", "fr", "de", "it", "ja"],
            format_func=lambda x: "🌍 Todos os idiomas" if x == "" else {
                "pt": "🇧🇷 Português",
                "en": "🇺🇸 Inglês", 
                "es": "🇪🇸 Espanhol",
                "fr": "🇫🇷 Francês",
                "de": "🇩🇪 Alemão",
                "it": "🇮🇹 Italiano",
                "ja": "🇯🇵 Japonês",
            }.get(x, x),
        )
    
    # Filtros
    st.subheader("🔍 Filtros de Conteúdo")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_reposts = st.checkbox("Incluir reposts/retweets", value=True)
    with col2:
        include_replies = st.checkbox("Incluir respostas", value=True)
    with col3:
        include_quotes = st.checkbox("Incluir citações", value=True)
    
    # Exportação
    st.subheader("📄 Formatos de Exportação")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_docx = st.checkbox("📄 Documento Word (DOCX)", value=True)
    with col2:
        export_json = st.checkbox("📋 JSON", value=False)
    with col3:
        export_csv = st.checkbox("📊 Planilha CSV", value=False)
    
    # Envio por e-mail
    st.subheader("📧 Envio por E-mail (opcional)")
    
    email_recipients = st.text_input(
        "Destinatários",
        placeholder="email1@exemplo.com, email2@exemplo.com",
        help="Separe múltiplos e-mails por vírgula. Deixe em branco para apenas baixar.",
    )
    
    st.markdown("---")

    # Gerenciamento do Chrome
    st.subheader("🌐 Gerenciamento do Chromium")

    # Status do Chrome
    chrome_running, chrome_status = get_chrome_status()

    if chrome_running:
        st.success(f"✅ Chromium está rodando - {chrome_status}")
    else:
        st.warning(f"⚠️ Chromium não está rodando - {chrome_status}")

    st.info("""
    **💡 Como funciona:**
    1. **FAÇA LOGIN NO X:** Importe seus cookies do X usando a seção "🍪 Login no X via Cookies" abaixo
    2. Clique em **"🚀 Iniciar Chromium"** para iniciar o navegador em modo headless
    3. O Chromium iniciará em background e carregará seus cookies automaticamente
    4. Clique em **"🔗 Conectar ao Chromium"** para verificar a conexão
    5. Agora você pode iniciar a coleta de dados!

    **⚠️ Nota:** O login só precisa ser feito uma vez. Os cookies ficam salvos permanentemente.
    """)

    # Botões de controle do Chrome
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🚀 Iniciar Chromium", use_container_width=True, type="primary", disabled=chrome_running):
            with st.spinner("Iniciando Chromium..."):
                success, msg = start_chrome()
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    # Mostrar log se houver erro
                    with st.expander("📋 Ver log do Chromium"):
                        st.code(get_chrome_log(), language="text")

    with col2:
        if st.button("🔄 Reiniciar Chromium", use_container_width=True, disabled=not chrome_running):
            with st.spinner("Reiniciando Chromium..."):
                success, msg = restart_chrome()
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with col3:
        if st.button("🛑 Parar Chromium", use_container_width=True, disabled=not chrome_running):
            with st.spinner("Parando Chromium..."):
                success, msg = stop_chrome()
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with col4:
        if st.button("🔍 Atualizar Status", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Login via Cookies
    st.subheader("🍪 Login no X via Cookies")

    # Verificar status dos cookies
    from core.collector import XCollector
    collector = XCollector(headless=True)
    cookies_info = collector.get_cookies_info()

    if cookies_info['exists']:
        from datetime import datetime
        imported_at = cookies_info.get('imported_at', 'desconhecido')
        try:
            # Formatar a data
            if imported_at != 'desconhecido':
                dt = datetime.fromisoformat(imported_at)
                imported_at_str = dt.strftime("%d/%m/%Y às %H:%M:%S")
            else:
                imported_at_str = 'desconhecido'
        except:
            imported_at_str = imported_at

        st.success(f"✅ Cookies importados: **{cookies_info['count']} cookies** (em {imported_at_str})")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col2:
            if st.button("🔍 Verificar Login", use_container_width=True):
                with st.spinner("Verificando sessão no X..."):
                    async def check_login():
                        temp_collector = XCollector(headless=True)
                        try:
                            await temp_collector.start()
                            is_logged = await temp_collector.is_logged_in()
                            await temp_collector.stop()
                            return is_logged
                        except Exception as e:
                            return None

                    try:
                        is_logged = asyncio.run(check_login())
                        if is_logged is True:
                            st.success("🎉 **Você está logado no X!**")
                        elif is_logged is False:
                            st.error("❌ **Sessão expirada.** Por favor, importe novos cookies.")
                        else:
                            st.warning("⚠️ Não foi possível verificar o login. Tente conectar ao Chromium.")
                    except Exception as e:
                        st.error(f"❌ Erro ao verificar login: {e}")

        with col3:
            if st.button("🗑️ Deletar", use_container_width=True):
                success, msg = collector.delete_saved_cookies()
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("ℹ️ Nenhum cookie importado. Use o formulário abaixo para importar seus cookies do X.")

    # Formulário de importação
    with st.expander("📥 Importar Cookies do X", expanded=not cookies_info['exists']):
        st.markdown("""
        **Como exportar cookies do X (Twitter):**

        1. Acesse https://x.com no seu navegador (já logado)
        2. Instale uma extensão de exportação de cookies:
           - [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg) (Chrome/Edge)
           - [Cookie-Editor](https://cookie-editor.cgagnier.ca/) (Chrome/Firefox/Edge)
        3. Clique na extensão e exporte todos os cookies do domínio **x.com**
        4. Copie o JSON exportado
        5. Cole no campo abaixo e clique em "💾 Importar Cookies"

        **⚠️ Importante:**
        - Exporte cookies apenas do domínio **x.com** ou **.twitter.com**
        - Os cookies devem estar em formato JSON (lista de objetos)
        - Mantenha seus cookies em segurança (não compartilhe!)
        """)

        cookies_json = st.text_area(
            "Cole o JSON dos cookies aqui:",
            height=200,
            placeholder='[{"name":"auth_token","value":"...","domain":".x.com",...}, ...]',
            help="Cole o JSON exportado pela extensão de cookies"
        )

        if st.button("💾 Importar Cookies", use_container_width=True, type="primary"):
            if not cookies_json.strip():
                st.error("❌ Por favor, cole o JSON dos cookies antes de importar")
            else:
                with st.spinner("Importando e validando cookies..."):
                    async def import_and_validate_cookies():
                        collector_temp = XCollector(headless=True)

                        # 1. Importar cookies
                        success, msg = await collector_temp.import_cookies_from_json(cookies_json)
                        if not success:
                            return False, msg, False

                        # 2. Validar sessão
                        try:
                            await collector_temp.start()
                            is_logged = await collector_temp.is_logged_in()
                            await collector_temp.stop()

                            return True, msg, is_logged
                        except Exception as e:
                            return True, msg, None  # Cookies importados mas validação falhou

                    try:
                        success, msg, logged_in = asyncio.run(import_and_validate_cookies())

                        if success:
                            st.success(msg)

                            if logged_in is True:
                                st.success("🎉 **Login validado com sucesso!** Você está logado no X.")
                            elif logged_in is False:
                                st.warning("⚠️ Cookies importados, mas a sessão não está ativa. Os cookies podem estar expirados. Tente exportar novos cookies.")
                            else:
                                st.info("✅ Cookies importados! Conecte ao Chromium para verificar o login.")

                            # Aguardar 2 segundos e recarregar
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(msg)
                    except Exception as e:
                        st.error(f"❌ Erro ao importar cookies: {e}")

    st.markdown("---")

    # Conexão e teste
    st.subheader("🔐 Conectar ao Chromium")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔗 Conectar ao Chromium", use_container_width=True, type="primary", disabled=not chrome_running):
            with st.spinner("Conectando ao Chromium..."):
                async def test_connection():
                    from playwright.async_api import async_playwright
                    pw = await async_playwright().start()
                    try:
                        browser = await pw.chromium.connect_over_cdp(
                            "http://127.0.0.1:9222",
                            timeout=5000,
                        )
                        contexts = browser.contexts
                        if contexts and contexts[0].pages:
                            page = contexts[0].pages[0]
                            # Verificar se está no X
                            url = page.url
                            if "x.com" in url or "twitter.com" in url:
                                # Tentar verificar se está logado
                                try:
                                    await page.wait_for_selector(
                                        '[data-testid="SideNav_AccountSwitcher_Button"]',
                                        timeout=3000
                                    )
                                    return True, "Conectado e LOGADO no X! 🎉"
                                except:
                                    return True, "Conectado ao X, mas NÃO logado. Por favor, faça login!"
                            return True, f"Conectado! (mas não está no X - URL: {url})"
                        return True, "Conectado ao Chromium!"
                    except Exception as e:
                        return False, str(e)
                    finally:
                        await pw.stop()

                try:
                    success, msg = asyncio.run(test_connection())
                    if success:
                        st.success(f"✅ {msg}")
                        st.session_state['chrome_connected'] = True
                    else:
                        st.error(f"❌ Não conectou: {msg}")
                        st.info("Certifique-se de que o Chromium está rodando!")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")

    with col2:
        if st.button("📋 Ver Logs do Chromium", use_container_width=True):
            logs = get_chrome_log()
            with st.expander("📋 Logs do Chromium", expanded=True):
                st.code(logs, language="text")

    # Informação adicional sobre login
    with st.expander("ℹ️ Outras opções de login (avançado)"):
        st.markdown("""
        ### ✅ Recomendado: Importar Cookies (seção acima)

        Use a seção **"🍪 Login no X via Cookies"** acima para importar cookies do seu navegador.
        Esta é a forma mais simples e segura de fazer login!

        ---

        ### Opção 2: Copiar perfil existente

        Se você já tem um Chromium/Chrome logado em outro lugar:

        1. Copie a pasta de perfil do Chrome
        2. Cole em `/app/browser_data/chrome-profile`
        3. Reinicie o Chromium pelo botão acima

        ### Opção 3: VNC (não recomendado)

        Apenas se as outras opções não funcionarem:

        1. Configure VNC para acessar o display :99
        2. Conecte-se e faça login manualmente no X
        3. Feche o VNC - o Chromium continuará rodando

        **⚠️ IMPORTANTE:** Após o login, os cookies ficam salvos permanentemente.
        Você só precisa fazer isso uma vez!
        """)

    st.markdown("---")
    
    # Botões de coleta
    col1, col2 = st.columns([3, 1])
    
    with col1:
        collect_button = st.button(
            "🚀 Iniciar Coleta",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.collecting,
        )
    
    with col2:
        if st.button("🗑️ Limpar", use_container_width=True):
            st.session_state.collection_result = None
            st.session_state.logs = []
            st.rerun()
    
    # Executar coleta
    if collect_button:
        # Validar entrada
        if not input_value or not input_value.strip():
            st.error("❌ Por favor, informe uma pesquisa ou URL!")
        else:
            st.session_state.collecting = True
            st.session_state.logs = []
            
            params = CollectionParams(
                search_type=SearchType.LATEST if search_type == "latest" else SearchType.TOP,
                max_posts=max_posts,
                max_minutes=max_minutes,
                include_reposts=include_reposts,
                include_replies=include_replies,
                include_quotes=include_quotes,
                language=language if language else None,
            )
            
            async def run_collection():
                from playwright.async_api import async_playwright
                
                playwright = await async_playwright().start()
                
                try:
                    # Conectar ao Chrome do usuário via CDP
                    add_log("🔗 Conectando ao Chrome...")
                    browser = await playwright.chromium.connect_over_cdp(
                        "http://127.0.0.1:9222",
                        timeout=10000,
                    )
                    
                    contexts = browser.contexts
                    if not contexts:
                        raise Exception("Nenhum contexto encontrado no Chrome")
                    
                    context = contexts[0]
                    
                    # Criar nova aba para a coleta
                    page = await context.new_page()
                    add_log("✅ Conectado ao Chrome!")
                    
                    # Criar coletor manual
                    collector = XCollector(headless=False)
                    collector._playwright = playwright
                    collector.browser = browser
                    collector.context = context
                    collector.page = page
                    
                    def progress_callback(count: int, msg: str):
                        add_log(msg)
                    
                    result = await collector.collect(
                        query_or_url=input_value.strip(),
                        params=params,
                        is_url=is_url,
                        progress_callback=progress_callback,
                    )
                    
                    # Fechar aba que criamos, mas não o browser
                    await page.close()
                    
                    return result
                    
                except Exception as e:
                    await playwright.stop()
                    raise Exception(f"Não foi possível conectar ao Chrome. Certifique-se de iniciá-lo com --remote-debugging-port=9222. Erro: {e}")
            
            with st.spinner("🔄 Coletando posts... Aguarde..."):
                try:
                    result = asyncio.run(run_collection())
                    st.session_state.collection_result = result
                    add_log(f"✅ Coleta finalizada: {result.total_collected} posts coletados")
                except Exception as e:
                    add_log(f"❌ Erro: {e}")
                    st.error(f"Erro durante a coleta: {e}")
            
            st.session_state.collecting = False
            st.rerun()
    
    # Exibir logs
    if st.session_state.logs:
        with st.expander("📋 Log de Execução", expanded=True):
            for log in st.session_state.logs[-20:]:
                st.text(log)
    
    # Exibir resultados
    if st.session_state.collection_result:
        result = st.session_state.collection_result
        
        st.markdown("---")
        st.subheader(f"📊 Resultado: {result.total_collected} posts coletados")
        
        # Métricas básicas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Posts", result.total_collected)
        with col2:
            duration = (result.finished_at - result.started_at).total_seconds() if result.finished_at else 0
            st.metric("Tempo de Coleta", f"{duration:.1f}s")
        with col3:
            stop_reasons = {
                "max_posts": "Limite atingido",
                "max_days": "Período atingido",
                "no_new_posts": "Sem mais posts",
                "error": "Erro",
            }
            st.metric("Motivo da Parada", stop_reasons.get(result.stop_reason, result.stop_reason))
        with col4:
            errors = len(result.errors)
            st.metric("Erros", errors)
        
        # Métricas de engajamento
        total_likes = sum(p.metrics.likes or 0 for p in result.posts)
        total_reposts = sum(p.metrics.reposts or 0 for p in result.posts)
        total_views = sum(p.metrics.views or 0 for p in result.posts)
        total_replies = sum(p.metrics.replies or 0 for p in result.posts)
        
        st.markdown("#### 📈 Engajamento Total")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("❤️ Curtidas", f"{total_likes:,}".replace(",", "."))
        with col2:
            st.metric("🔁 Reposts", f"{total_reposts:,}".replace(",", "."))
        with col3:
            st.metric("👁️ Views", f"{total_views:,}".replace(",", "."))
        with col4:
            st.metric("💬 Respostas", f"{total_replies:,}".replace(",", "."))
        
        # Botões de download e envio
        st.subheader("⬇️ Download e Envio")
        
        exported_files = []
        
        col1, col2, col3 = st.columns(3)
        
        if export_docx:
            filepath = export_to_docx(result)
            exported_files.append(filepath)
            with col1:
                with open(filepath, "rb") as f:
                    st.download_button(
                        "📄 Baixar DOCX",
                        f,
                        file_name=Path(filepath).name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
        
        if export_json:
            filepath = export_to_json(result)
            exported_files.append(filepath)
            with col2:
                with open(filepath, "rb") as f:
                    st.download_button(
                        "📋 Baixar JSON",
                        f,
                        file_name=Path(filepath).name,
                        mime="application/json",
                        use_container_width=True,
                    )
        
        if export_csv:
            filepath = export_to_csv(result)
            exported_files.append(filepath)
            with col3:
                with open(filepath, "rb") as f:
                    st.download_button(
                        "📊 Baixar CSV",
                        f,
                        file_name=Path(filepath).name,
                        mime="text/csv",
                        use_container_width=True,
                    )
        
        # Botão de envio por e-mail
        if email_recipients and email_recipients.strip():
            st.markdown("---")
            recipients_list = [e.strip() for e in email_recipients.split(",") if e.strip()]
            
            if st.button("📧 Enviar por E-mail", use_container_width=True, type="secondary"):
                with st.spinner("Enviando e-mail..."):
                    try:
                        success = asyncio.run(send_collection_email(
                            recipients=recipients_list,
                            result=result,
                            query_or_url=input_value,
                            attachments=exported_files,
                        ))
                        if success:
                            st.success(f"✅ E-mail enviado com sucesso para: {', '.join(recipients_list)}")
                        else:
                            st.error("❌ Falha ao enviar e-mail. Verifique as configurações.")
                    except Exception as e:
                        st.error(f"❌ Erro ao enviar e-mail: {e}")
        
        # Preview dos posts
        st.subheader("👁️ Prévia dos Posts")
        for i, post in enumerate(result.posts[:10], 1):
            preview_text = post.text[:50] + "..." if len(post.text) > 50 else post.text
            with st.expander(f"#{i} @{post.author_handle} - {preview_text}"):
                st.markdown(f"**Autor:** {post.author_name} (@{post.author_handle})")
                if post.datetime:
                    st.markdown(f"**Data:** {post.datetime.strftime('%d/%m/%Y às %H:%M')}")
                st.markdown(f"**Texto:** {post.text}")
                st.markdown(f"**Link:** [{post.url}]({post.url})")
                
                # Métricas incluindo views
                metrics = []
                if post.metrics.likes:
                    metrics.append(f"❤️ {post.metrics.likes:,} curtidas".replace(",", "."))
                if post.metrics.reposts:
                    metrics.append(f"🔁 {post.metrics.reposts:,} reposts".replace(",", "."))
                if post.metrics.replies:
                    metrics.append(f"💬 {post.metrics.replies:,} respostas".replace(",", "."))
                if post.metrics.views:
                    metrics.append(f"👁️ {post.metrics.views:,} views".replace(",", "."))
                
                if metrics:
                    st.markdown(" | ".join(metrics))


# === PÁGINA: AGENDAMENTOS ===
elif page == "📅 Agendamentos":
    st.title("📅 Agendamentos Automáticos")
    
    from scheduler import JobManager, validate_cron, cron_examples
    from core.models import Job, Schedule, ScheduleType, JobStatus
    
    job_manager = JobManager()
    
    # Formulário para novo job
    with st.expander("➕ Criar Novo Agendamento", expanded=False):
        with st.form("new_job_form"):
            job_name = st.text_input("Nome do agendamento", placeholder="Ex: Coleta Diária de Tech")
            
            col1, col2 = st.columns(2)
            with col1:
                job_query = st.text_area(
                    "Pesquisa ou URL",
                    placeholder="from:openai OR from:anthropic",
                    height=100,
                )
            with col2:
                job_is_url = st.checkbox("É uma URL")
                job_max_posts = st.number_input("Limite de posts", value=3000, min_value=10, max_value=10000)
                
                # Período em minutos para agendamento
                job_periodo_opcoes = {
                    "Sem limite de tempo": 0,
                    "Últimos 10 minutos": 10,
                    "Última hora": 60,
                    "Últimas 6 horas": 360,
                    "Últimas 12 horas": 720,
                    "Último dia (24h)": 1440,
                    "Últimos 3 dias": 4320,
                    "Última semana": 10080,
                }
                
                job_periodo = st.selectbox(
                    "⏱️ Período de tempo",
                    options=list(job_periodo_opcoes.keys()),
                    index=0,
                    help="Filtrar posts por período",
                )
                job_max_minutes = job_periodo_opcoes[job_periodo] or None
            
            # Agendamento
            st.subheader("⏰ Quando Executar")
            schedule_type = st.radio(
                "Frequência",
                ["once", "recurring"],
                format_func=lambda x: "📆 Apenas uma vez" if x == "once" else "🔄 Recorrente (diário/semanal)",
                horizontal=True,
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if schedule_type == "once":
                    run_date = st.date_input("Data", datetime.now().date())
                    run_time = st.time_input("Horário", datetime.now().time())
                else:
                    cron_input = st.text_input(
                        "Expressão Cron",
                        value="0 7 * * *",
                        help="Formato: minuto hora dia mês dia_da_semana",
                    )
                    st.caption("**Exemplos:**")
                    for desc, expr in list(cron_examples().items())[:3]:
                        st.caption(f"`{expr}` = {desc}")
            
            with col2:
                job_timezone = st.selectbox(
                    "Fuso Horário",
                    ["America/Sao_Paulo", "UTC", "America/New_York"],
                    format_func=lambda x: {
                        "America/Sao_Paulo": "🇧🇷 Brasília",
                        "UTC": "🌍 UTC",
                        "America/New_York": "🇺🇸 Nova York",
                    }.get(x, x),
                )
            
            # E-mail
            st.subheader("📧 Destinatários do Relatório")
            job_emails = st.text_input(
                "E-mails (separados por vírgula)",
                placeholder="email1@exemplo.com, email2@exemplo.com",
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                job_export_docx = st.checkbox("📄 DOCX", value=True)
            with col2:
                job_export_json = st.checkbox("📋 JSON")
            with col3:
                job_export_csv = st.checkbox("📊 CSV")
            
            job_dry_run = st.checkbox("🔄 Modo teste (não enviar e-mail)")
            
            submitted = st.form_submit_button("💾 Criar Agendamento", type="primary")
            
            if submitted:
                if not job_name or not job_query:
                    st.error("❌ Nome e Pesquisa são obrigatórios!")
                else:
                    # Validar cron se recorrente
                    if schedule_type == "recurring":
                        valid, msg = validate_cron(cron_input)
                        if not valid:
                            st.error(f"❌ Expressão Cron inválida: {msg}")
                            st.stop()
                    
                    # Criar job
                    export_formats = []
                    if job_export_docx:
                        export_formats.append("docx")
                    if job_export_json:
                        export_formats.append("json")
                    if job_export_csv:
                        export_formats.append("csv")
                    
                    schedule = Schedule(
                        type=ScheduleType.ONCE if schedule_type == "once" else ScheduleType.RECURRING,
                        run_at=datetime.combine(run_date, run_time) if schedule_type == "once" else None,
                        cron=cron_input if schedule_type == "recurring" else None,
                        timezone=job_timezone,
                    )
                    
                    params = CollectionParams(max_posts=job_max_posts, max_minutes=job_max_minutes)
                    
                    recipients = [e.strip() for e in job_emails.split(",") if e.strip()]
                    
                    job = job_manager.create_job(
                        name=job_name,
                        query_or_url=job_query,
                        is_url=job_is_url,
                        params=params,
                        schedule=schedule,
                        email_recipients=recipients,
                        export_formats=export_formats,
                        dry_run=job_dry_run,
                    )
                    
                    st.success(f"✅ Agendamento criado: {job.name}")
                    st.rerun()
    
    # Lista de jobs
    st.subheader("📋 Agendamentos Existentes")
    
    jobs = job_manager.list_jobs()
    
    if not jobs:
        st.info("Nenhum agendamento criado ainda. Clique em '➕ Criar Novo Agendamento' acima.")
    else:
        for job in jobs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    status_icon = "✅" if job.status == JobStatus.ACTIVE else "⏸️" if job.status == JobStatus.PAUSED else "✔️"
                    status_text = "Ativo" if job.status == JobStatus.ACTIVE else "Pausado" if job.status == JobStatus.PAUSED else "Concluído"
                    st.markdown(f"**{status_icon} {job.name}** ({status_text})")
                    query_preview = job.query_or_url[:50] + "..." if len(job.query_or_url) > 50 else job.query_or_url
                    st.caption(query_preview)
                
                with col2:
                    if job.schedule.type == ScheduleType.ONCE:
                        st.markdown(f"📆 {job.schedule.run_at.strftime('%d/%m/%Y às %H:%M') if job.schedule.run_at else 'N/A'}")
                    else:
                        st.markdown(f"🔄 `{job.schedule.cron}`")
                
                with col3:
                    if job.last_run:
                        st.markdown(f"⏱️ Última: {job.last_run.strftime('%d/%m às %H:%M')}")
                    else:
                        st.markdown("⏱️ Nunca executou")
                
                with col4:
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    
                    with btn_col1:
                        if job.status == JobStatus.ACTIVE:
                            if st.button("⏸️", key=f"pause_{job.job_id}", help="Pausar"):
                                job_manager.pause_job(job.job_id)
                                st.rerun()
                        else:
                            if st.button("▶️", key=f"resume_{job.job_id}", help="Retomar"):
                                job_manager.resume_job(job.job_id)
                                st.rerun()
                    
                    with btn_col2:
                        if st.button("🗑️", key=f"delete_{job.job_id}", help="Excluir"):
                            job_manager.delete_job(job.job_id)
                            st.rerun()
                    
                    with btn_col3:
                        if st.button("▶️", key=f"run_{job.job_id}", help="Executar agora"):
                            with st.spinner("Executando..."):
                                runner = get_runner()
                                asyncio.run(runner.run_job_now(job.job_id))
                            st.success("✅ Executado!")
                            st.rerun()
                
                st.markdown("---")


# === PÁGINA: HISTÓRICO ===
elif page == "📊 Histórico":
    st.title("📊 Histórico de Execuções")
    
    from scheduler.persistence import get_db
    
    db = get_db()
    runs = db.get_all_runs(limit=50)
    
    if not runs:
        st.info("Nenhuma execução registrada ainda.")
    else:
        for run in runs:
            status_icons = {
                "success": "✅",
                "failed": "❌",
                "running": "🔄",
                "partial": "⚠️",
            }
            status_icon = status_icons.get(run.status.value, "❓")
            
            with st.expander(
                f"{status_icon} {run.job_name} - {run.started_at.strftime('%d/%m/%Y às %H:%M')} - "
                f"{run.posts_collected} posts"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Agendamento:** {run.job_name}")
                    status_text = {
                        "success": "✅ Sucesso",
                        "failed": "❌ Falhou",
                        "running": "🔄 Em execução",
                        "partial": "⚠️ Parcial",
                    }.get(run.status.value, run.status.value)
                    st.markdown(f"**Status:** {status_text}")
                    st.markdown(f"**Posts coletados:** {run.posts_collected}")
                    st.markdown(f"**E-mail:** {'✅ Enviado' if run.email_sent else '❌ Não enviado'}")
                
                with col2:
                    st.markdown(f"**Início:** {run.started_at.strftime('%d/%m/%Y às %H:%M:%S')}")
                    if run.finished_at:
                        duration = (run.finished_at - run.started_at).total_seconds()
                        st.markdown(f"**Duração:** {duration:.1f} segundos")
                    
                    if run.export_files:
                        st.markdown("**Arquivos gerados:**")
                        for f in run.export_files:
                            st.markdown(f"- `{Path(f).name}`")
                
                if run.error_message:
                    st.error(f"**Erro:** {run.error_message}")
                
                if run.logs:
                    st.markdown("**Log de execução:**")
                    for log in run.logs[-10:]:
                        st.text(log)


# === PÁGINA: CONFIGURAÇÕES ===
elif page == "⚙️ Configurações":
    st.title("⚙️ Configurações")
    
    st.subheader("📧 Configuração de E-mail (SMTP)")
    
    email_ok, email_msg = test_email_config()
    
    if email_ok:
        st.success(f"✅ {email_msg}")
    else:
        st.error(f"❌ {email_msg}")
    
    st.markdown("""
    Configure as variáveis de ambiente no arquivo `.env`:
    
    ```env
    # Configuração para AOL
    SMTP_HOST=smtp.aol.com
    SMTP_PORT=587
    SMTP_USER=seu_email@aol.com
    SMTP_PASS=sua_senha_de_app
    FROM_EMAIL=seu_email@aol.com
    
    # Ou para Gmail
    # SMTP_HOST=smtp.gmail.com
    # SMTP_PORT=587
    # SMTP_USER=seu_email@gmail.com
    # SMTP_PASS=sua_app_password
    # FROM_EMAIL=seu_email@gmail.com
    ```
    
    **Para AOL:**
    1. Acesse as configurações de segurança da conta AOL
    2. Gere uma senha de aplicativo
    3. Use essa senha no `SMTP_PASS`
    
    **Para Gmail:**
    1. Ative a verificação em duas etapas
    2. Crie uma "Senha de App" em: Conta Google > Segurança > Senhas de app
    3. Use essa senha no `SMTP_PASS`
    """)
    
    st.markdown("---")
    
    st.subheader("🗄️ Estatísticas")
    
    from scheduler.persistence import get_db
    
    db = get_db()
    jobs = db.get_all_jobs()
    runs = db.get_all_runs()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Agendamentos criados", len(jobs))
    with col2:
        st.metric("Execuções registradas", len(runs))
    
    st.markdown("---")
    
    st.subheader("📂 Diretórios e Arquivos")
    
    st.markdown(f"- **Dados do navegador:** `{os.getenv('BROWSER_DATA_DIR', './browser_data')}`")
    st.markdown(f"- **Arquivos exportados:** `{os.getenv('EXPORTS_DIR', './exports')}`")
    st.markdown(f"- **Banco de dados:** `{os.getenv('DB_PATH', './data/scheduler.db')}`")
    
    st.markdown("---")
    
    st.subheader("🔧 Ações de Manutenção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Limpar dados do navegador", use_container_width=True):
            import shutil
            browser_dir = os.getenv('BROWSER_DATA_DIR', './browser_data')
            if os.path.exists(browser_dir):
                shutil.rmtree(browser_dir)
                st.success("✅ Dados do navegador limpos. Você precisará fazer login novamente.")
            else:
                st.info("Não há dados do navegador para limpar.")
    
    with col2:
        if st.button("🗑️ Limpar histórico de execuções", use_container_width=True):
            st.warning("Esta função ainda não foi implementada.")
