"""Coletor de posts do X usando Playwright - Versão Simplificada Headless."""
from __future__ import annotations
import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Callable, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from core.models import Post, CollectionParams, CollectionResult
from core.extractor import PostExtractor
from core.url_builder import URLBuilder
from core.cookie_manager import CookieManager


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


class XCollector:
    """Coletor de posts do X com Playwright - Modo Headless Simplificado."""

    def __init__(self, headless: bool = True):
        """
        Inicializa o coletor.

        Args:
            headless: Se True, roda em modo headless (sem interface gráfica)
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
        self.cookie_manager = CookieManager(CollectorConfig.BROWSER_DATA_DIR)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """
        Inicia o navegador Playwright em modo headless.
        Carrega cookies automaticamente se existirem.
        """
        print("🚀 Iniciando Playwright...")
        self._playwright = await async_playwright().start()

        # Criar diretório de dados se não existir
        browser_data_path = Path(CollectorConfig.BROWSER_DATA_DIR)
        browser_data_path.mkdir(parents=True, exist_ok=True)

        # Iniciar browser headless
        print("🌐 Iniciando Chromium headless...")
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
            ]
        )

        # Criar contexto com configurações realistas
        print("📝 Criando contexto do navegador...")
        self.context = await self.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
        )

        # Carregar cookies salvos se existirem
        if self.cookie_manager.has_cookies():
            print("🍪 Carregando cookies salvos...")
            await self.load_cookies_to_context()
        else:
            print("⚠️  Nenhum cookie salvo encontrado. Você precisará importar cookies para fazer login.")

        # Criar página
        self.page = await self.context.new_page()
        print("✅ Navegador iniciado com sucesso!")

    async def stop(self):
        """Para o navegador e libera recursos."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        print("👋 Navegador finalizado")

    async def import_cookies_from_json(self, cookies_json: str) -> tuple[bool, str]:
        """
        Importa cookies a partir de um JSON.

        Args:
            cookies_json: String JSON com cookies exportados do navegador

        Returns:
            Tupla (sucesso, mensagem)
        """
        return self.cookie_manager.import_cookies(cookies_json)

    async def load_cookies_to_context(self) -> bool:
        """
        Carrega cookies salvos no contexto do Playwright.

        Returns:
            True se cookies foram carregados com sucesso
        """
        if not self.context:
            print("⚠️  Contexto do browser não iniciado")
            return False

        cookies = self.cookie_manager.load_cookies()
        if not cookies:
            print("⚠️  Nenhum cookie salvo encontrado")
            return False

        try:
            await self.context.add_cookies(cookies)
            print(f"✅ {len(cookies)} cookies carregados no contexto")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar cookies no contexto: {e}")
            return False

    def has_saved_cookies(self) -> bool:
        """Verifica se existem cookies salvos."""
        return self.cookie_manager.has_cookies()

    def get_cookies_info(self):
        """Retorna informações sobre os cookies salvos."""
        return self.cookie_manager.get_cookies_info()

    def delete_saved_cookies(self) -> tuple[bool, str]:
        """Remove os cookies salvos."""
        return self.cookie_manager.delete_cookies()

    async def is_logged_in(self) -> bool:
        """
        Verifica se há sessão ativa no X.

        Returns:
            True se estiver logado, False caso contrário
        """
        if not self.page:
            return False

        try:
            print("🔍 Verificando login no X...")
            await self.page.goto("https://x.com/home", timeout=CollectorConfig.PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
            await asyncio.sleep(3)

            # Verificar elementos de usuário logado
            logged = await self.page.query_selector('[data-testid="SideNav_AccountSwitcher_Button"]')

            if logged:
                print("✅ Login confirmado!")
                return True
            else:
                print("❌ Não está logado")
                return False

        except Exception as e:
            print(f"❌ Erro ao verificar login: {e}")
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

            return False, "Sem bloqueios detectados"

        except Exception as e:
            return False, f"Erro ao verificar bloqueios: {e}"

    async def collect_posts(
        self,
        params: CollectionParams,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> CollectionResult:
        """
        Coleta posts do X baseado nos parâmetros fornecidos.

        Args:
            params: Parâmetros da coleta
            progress_callback: Função chamada com mensagens de progresso

        Returns:
            Resultado da coleta com posts e metadados
        """
        def log(msg: str):
            print(msg)
            if progress_callback:
                progress_callback(msg)

        log("🎯 Iniciando coleta de posts...")

        # Verificar login antes de coletar
        if not await self.is_logged_in():
            raise Exception("❌ Você precisa estar logado no X para coletar posts. Importe seus cookies primeiro!")

        # Verificar bloqueios
        has_block, block_msg = await self.check_for_blocks()
        if has_block:
            raise Exception(f"❌ {block_msg}")

        # Construir URL de busca
        url = URLBuilder.build_search_url(params)
        log(f"🔗 URL de busca: {url}")

        # Navegar para a busca
        log("🌐 Navegando para a página de busca...")
        await self.page.goto(url, timeout=CollectorConfig.PAGE_LOAD_TIMEOUT, wait_until="networkidle")
        await asyncio.sleep(3)

        # Coletar posts via scroll
        posts = []
        seen_ids = set()
        no_new_posts_count = 0
        scroll_count = 0

        log("📜 Iniciando scroll para coletar posts...")

        while len(posts) < params.max_posts and no_new_posts_count < CollectorConfig.NO_NEW_POSTS_LIMIT:
            scroll_count += 1
            log(f"Scroll #{scroll_count} - Posts coletados: {len(posts)}")

            # Extrair posts da página atual
            new_posts = await PostExtractor.extract_posts(self.page)

            # Filtrar posts já vistos
            new_unique_posts = [p for p in new_posts if p.id not in seen_ids]

            if len(new_unique_posts) == 0:
                no_new_posts_count += 1
                log(f"⚠️  Nenhum post novo encontrado ({no_new_posts_count}/{CollectorConfig.NO_NEW_POSTS_LIMIT})")
            else:
                no_new_posts_count = 0
                posts.extend(new_unique_posts)
                seen_ids.update(p.id for p in new_unique_posts)
                log(f"✅ {len(new_unique_posts)} posts novos encontrados")

            # Verificar se atingiu o limite
            if len(posts) >= params.max_posts:
                posts = posts[:params.max_posts]
                log(f"🎉 Limite de {params.max_posts} posts atingido!")
                break

            # Scroll suave
            await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(CollectorConfig.MIN_SCROLL_INTERVAL)

        # Criar resultado
        result = CollectionResult(
            posts=posts,
            query_or_url=params.query or params.url or "",
            params=params,
            started_at=utc_now(),
            finished_at=utc_now(),
            total_collected=len(posts),
            stop_reason="max_posts" if len(posts) >= params.max_posts else "no_new_posts",
            errors=[],
        )

        log(f"✅ Coleta finalizada! Total: {len(posts)} posts")
        return result


# Manter compatibilidade com código existente
__all__ = ['XCollector', 'CollectorConfig']
