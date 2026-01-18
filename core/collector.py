"""Coletor de posts do X usando Playwright."""
from __future__ import annotations
import asyncio
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncGenerator, Callable, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from core.models import Post, CollectionParams, CollectionResult
from core.extractor import PostExtractor
from core.url_builder import URLBuilder


def utc_now() -> datetime:
    """Retorna datetime atual em UTC."""
    return datetime.now(timezone.utc)


class CollectorConfig:
    """Configurações do coletor."""
    # Diretório para dados persistentes do browser
    BROWSER_DATA_DIR = os.getenv("BROWSER_DATA_DIR", "./browser_data")
    
    # Timeouts
    PAGE_LOAD_TIMEOUT = 60000  # 60s
    SCROLL_WAIT = 2000  # 2s entre scrolls
    NO_NEW_POSTS_LIMIT = 5  # Scrolls sem novos posts antes de parar
    
    # Rate limiting conservador
    MIN_SCROLL_INTERVAL = 1.5  # segundos
    MAX_SCROLLS_PER_MINUTE = 20
    
    # Porta para debug do Chrome
    CHROME_DEBUG_PORT = 9222


def get_chrome_path() -> str:
    """Retorna o caminho do Chrome baseado no OS."""
    import platform
    system = platform.system()
    
    if system == "Darwin":  # macOS
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    elif system == "Windows":
        paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
    else:  # Linux
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return "google-chrome"  # Fallback


def get_chrome_user_data_dir() -> str:
    """Retorna o diretório de dados do usuário do Chrome."""
    import platform
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif system == "Windows":
        return os.path.expandvars(r"%LocalAppData%\Google\Chrome\User Data")
    else:  # Linux
        return os.path.expanduser("~/.config/google-chrome")


class XCollector:
    """Coletor de posts do X com Playwright - Modo Elon Musk."""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
        self._chrome_process = None
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
    
    async def start(self):
        """Inicia conexão com Chrome."""
        self._playwright = await async_playwright().start()
        
        # Tentar conectar a um Chrome já rodando com debug
        try:
            self.browser = await self._playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{CollectorConfig.CHROME_DEBUG_PORT}"
            )
            
            # Usar contexto existente
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                if self.context.pages:
                    self.page = self.context.pages[0]
                else:
                    self.page = await self.context.new_page()
            else:
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
            
            print("✅ Conectado ao Chrome existente!")
            return
            
        except Exception as e:
            print(f"⚠️ Chrome não está em modo debug. Iniciando novo...")
        
        # Se não conseguiu conectar, iniciar Chrome com perfil do usuário
        await self._start_chrome_with_profile()
    
    async def _start_chrome_with_profile(self):
        """Inicia Chrome usando o perfil real do usuário (com login salvo)."""
        chrome_path = get_chrome_path()
        user_data_dir = get_chrome_user_data_dir()
        
        print(f"🚀 Iniciando Chrome com seu perfil...")
        print(f"   Chrome: {chrome_path}")
        print(f"   Perfil: {user_data_dir}")
        
        # Verificar se Chrome já está rodando
        # Se estiver, precisamos usar uma cópia do perfil ou pedir para fechar
        
        # Usar diretório temporário baseado no perfil original
        temp_profile = Path(CollectorConfig.BROWSER_DATA_DIR) / "chrome_profile"
        temp_profile.mkdir(parents=True, exist_ok=True)
        
        # Iniciar Chrome com debug port
        args = [
            chrome_path,
            f"--remote-debugging-port={CollectorConfig.CHROME_DEBUG_PORT}",
            f"--user-data-dir={temp_profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
        ]
        
        if self.headless:
            args.append("--headless=new")
        
        try:
            self._chrome_process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            
            # Aguardar Chrome iniciar
            await asyncio.sleep(2)
            
            # Conectar via CDP
            for attempt in range(5):
                try:
                    self.browser = await self._playwright.chromium.connect_over_cdp(
                        f"http://127.0.0.1:{CollectorConfig.CHROME_DEBUG_PORT}"
                    )
                    break
                except Exception:
                    await asyncio.sleep(1)
            
            if not self.browser:
                raise Exception("Não foi possível conectar ao Chrome")
            
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                if self.context.pages:
                    self.page = self.context.pages[0]
                else:
                    self.page = await self.context.new_page()
            else:
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
            
            print("✅ Chrome iniciado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar Chrome: {e}")
            # Fallback para Playwright puro
            await self._start_playwright_browser()
    
    async def _start_playwright_browser(self):
        """Fallback: inicia browser Playwright normal."""
        browser_data_path = Path(CollectorConfig.BROWSER_DATA_DIR)
        browser_data_path.mkdir(parents=True, exist_ok=True)
        
        self.context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(browser_data_path),
            headless=self.headless,
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
    
    async def stop(self):
        """Para o browser."""
        if self.context and not self.browser:
            # Contexto persistente
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        if self._chrome_process:
            self._chrome_process.terminate()
    
    async def start_chrome_debug_mode(self) -> str:
        """
        Inicia o Chrome do usuário em modo debug.
        Retorna instruções para o usuário.
        """
        chrome_path = get_chrome_path()
        port = CollectorConfig.CHROME_DEBUG_PORT
        
        # Comando para o usuário executar
        if os.name == "nt":  # Windows
            cmd = f'"{chrome_path}" --remote-debugging-port={port}'
        else:
            cmd = f'"{chrome_path}" --remote-debugging-port={port}'
        
        return cmd
    
    async def connect_to_user_chrome(self) -> bool:
        """
        Tenta conectar ao Chrome do usuário rodando em modo debug.
        """
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        try:
            self.browser = await self._playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{CollectorConfig.CHROME_DEBUG_PORT}",
                timeout=5000,
            )
            
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                pages = self.context.pages
                
                # Procurar página do X já aberta
                for p in pages:
                    if "x.com" in p.url or "twitter.com" in p.url:
                        self.page = p
                        print(f"✅ Encontrada página do X: {p.url}")
                        return True
                
                # Se não tem página do X, usar primeira página
                if pages:
                    self.page = pages[0]
                else:
                    self.page = await self.context.new_page()
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Não foi possível conectar: {e}")
            return False
    
    async def is_logged_in(self) -> bool:
        """Verifica se há sessão ativa."""
        if not self.page:
            return False
        
        try:
            await self.page.goto("https://x.com/home", timeout=CollectorConfig.PAGE_LOAD_TIMEOUT)
            await asyncio.sleep(3)
            
            # Verificar elementos de usuário logado
            logged = await self.page.query_selector('[data-testid="SideNav_AccountSwitcher_Button"]')
            return logged is not None
            
        except Exception:
            return False
    
    async def open_for_login(self) -> bool:
        """Abre o X para login."""
        if not self.page:
            await self.start()
        
        try:
            await self.page.goto("https://x.com/login", timeout=CollectorConfig.PAGE_LOAD_TIMEOUT)
            
            print("🔐 Faça login no X. O navegador ficará aberto por até 5 minutos...")
            
            # Aguardar login
            for _ in range(150):  # 5 minutos
                await asyncio.sleep(2)
                try:
                    if "/home" in self.page.url or self.page.url == "https://x.com/":
                        logged = await self.page.query_selector('[data-testid="SideNav_AccountSwitcher_Button"]')
                        if logged:
                            print("✅ Login detectado!")
                            return True
                except Exception:
                    pass
            
            print("⏰ Tempo limite atingido")
            return False
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    async def import_chrome_cookies(self) -> bool:
        """Placeholder - não mais necessário com nova abordagem."""
        return False
    
    async def check_for_blocks(self) -> tuple[bool, str]:
        """
        Verifica se há bloqueios ou verificações pendentes.
        
        Returns:
            (tem_bloqueio, mensagem)
        """
        if not self.page:
            return True, "Browser não iniciado"
        
        try:
            page_content = await self.page.content()
            
            # Verificar diferentes tipos de bloqueio
            block_indicators = [
                ("Verify your identity", "Verificação de identidade necessária"),
                ("Verify your phone", "Verificação de telefone necessária"),
                ("Something went wrong", "Erro detectado - possível rate limit"),
                ("Rate limit exceeded", "Rate limit excedido"),
                ("Suspicious activity", "Atividade suspeita detectada"),
                ("CAPTCHA", "CAPTCHA detectado"),
                ("Are you a robot", "Verificação anti-bot detectada"),
            ]
            
            for indicator, message in block_indicators:
                if indicator.lower() in page_content.lower():
                    return True, message
            
            return False, ""
        except Exception as e:
            return True, f"Erro ao verificar bloqueios: {e}"
    
    async def collect(
        self,
        query_or_url: str,
        params: CollectionParams,
        is_url: bool = False,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> CollectionResult:
        """
        Coleta posts baseado em query ou URL.
        
        Args:
            query_or_url: Query de busca ou URL completa
            params: Parâmetros de coleta
            is_url: Se True, query_or_url é uma URL
            progress_callback: Função chamada com (posts_count, log_message)
            
        Returns:
            CollectionResult com todos os posts coletados
        """
        result = CollectionResult(
            query_or_url=query_or_url,
            params=params,
            started_at=utc_now(),
        )
        
        if not self.page:
            result.errors.append("Browser não iniciado")
            result.stop_reason = "error"
            return result
        
        def log(msg: str):
            if progress_callback:
                progress_callback(len(result.posts), msg)
            print(msg)
        
        try:
            # Construir URL
            if is_url:
                url = URLBuilder.normalize_url(query_or_url)
            else:
                url = URLBuilder.build_search_url(query_or_url, params)
            
            log(f"🔍 Navegando para: {url}")
            
            # Navegar para a página
            await self.page.goto(url, timeout=CollectorConfig.PAGE_LOAD_TIMEOUT)
            await asyncio.sleep(3)  # Aguardar carregamento inicial
            
            # Verificar bloqueios
            has_block, block_msg = await self.check_for_blocks()
            if has_block:
                log(f"🚫 {block_msg}")
                result.errors.append(block_msg)
                result.stop_reason = "blocked"
                return result
            
            # Coletar posts com scroll
            collected_ids = set()
            no_new_posts_count = 0
            scroll_count = 0
            last_scroll_time = datetime.now()
            
            # Calcular data limite se max_days definido
            date_limit = None
            if params.max_days:
                date_limit = utc_now() - timedelta(days=params.max_days)
            
            while True:
                # Rate limiting
                time_since_last = (datetime.now() - last_scroll_time).total_seconds()
                if time_since_last < CollectorConfig.MIN_SCROLL_INTERVAL:
                    await asyncio.sleep(CollectorConfig.MIN_SCROLL_INTERVAL - time_since_last)
                
                # Extrair posts da página atual
                new_posts = await PostExtractor.extract_all_from_page(self.page)
                new_count = 0
                
                for post in new_posts:
                    if post.post_id in collected_ids:
                        continue
                    
                    # Aplicar filtros
                    if not params.include_reposts and post.is_repost:
                        continue
                    if not params.include_replies and post.is_reply:
                        continue
                    if not params.include_quotes and post.is_quote:
                        continue
                    
                    # Verificar limite de data
                    if date_limit and post.datetime and post.datetime < date_limit:
                        log(f"📅 Atingido limite de data ({params.max_days} dias)")
                        result.stop_reason = "date_limit"
                        break
                    
                    result.posts.append(post)
                    collected_ids.add(post.post_id)
                    new_count += 1
                    
                    # Verificar limite de posts
                    if params.max_posts and len(result.posts) >= params.max_posts:
                        log(f"✅ Atingido limite de {params.max_posts} posts")
                        result.stop_reason = "max_posts"
                        break
                
                log(f"📊 Scroll #{scroll_count + 1}: {len(result.posts)} posts ({new_count} novos)")
                
                # Verificar condições de parada
                if result.stop_reason:
                    break
                
                if new_count == 0:
                    no_new_posts_count += 1
                    if no_new_posts_count >= CollectorConfig.NO_NEW_POSTS_LIMIT:
                        log(f"⏹️ Sem novos posts por {no_new_posts_count} scrolls")
                        result.stop_reason = "no_new_posts"
                        break
                else:
                    no_new_posts_count = 0
                
                # Fazer scroll
                scroll_count += 1
                last_scroll_time = datetime.now()
                
                await self.page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
                await asyncio.sleep(CollectorConfig.SCROLL_WAIT / 1000)
                
                # Verificar bloqueios periodicamente
                if scroll_count % 10 == 0:
                    has_block, block_msg = await self.check_for_blocks()
                    if has_block:
                        log(f"🚫 {block_msg}")
                        result.errors.append(block_msg)
                        result.stop_reason = "blocked"
                        break
            
            result.finished_at = utc_now()
            result.total_collected = len(result.posts)
            
            if not result.stop_reason:
                result.stop_reason = "completed"
            
            log(f"✅ Coleta finalizada: {result.total_collected} posts")
            
        except Exception as e:
            result.errors.append(str(e))
            result.stop_reason = "error"
            result.finished_at = utc_now()
        
        return result
    
    async def collect_generator(
        self,
        query_or_url: str,
        params: CollectionParams,
        is_url: bool = False,
    ) -> AsyncGenerator[Post, None]:
        """
        Versão generator que yield posts conforme são coletados.
        Útil para streaming/atualização em tempo real.
        """
        # Implementação simplificada - usar collect() para MVP
        result = await self.collect(query_or_url, params, is_url)
        for post in result.posts:
            yield post


async def quick_collect(
    query_or_url: str,
    max_posts: int = 100,
    is_url: bool = False,
    headless: bool = False,
) -> list[Post]:
    """
    Função helper para coleta rápida.
    
    Args:
        query_or_url: Query ou URL
        max_posts: Máximo de posts
        is_url: Se é URL
        headless: Se roda sem janela
        
    Returns:
        Lista de posts
    """
    params = CollectionParams(max_posts=max_posts)
    
    async with XCollector(headless=headless) as collector:
        result = await collector.collect(query_or_url, params, is_url)
        return result.posts
