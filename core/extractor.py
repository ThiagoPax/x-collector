"""Extrator de dados dos posts do X."""
from __future__ import annotations
import re
from datetime import datetime
from typing import Optional, List
from playwright.async_api import Page, Locator
from core.models import Post, PostMetrics


class PostExtractor:
    """Extrai dados estruturados dos posts do X."""
    
    # Seletores (podem precisar de atualização se o X mudar o layout)
    # Usamos múltiplas estratégias para maior resiliência
    ARTICLE_SELECTOR = 'article[data-testid="tweet"]'
    FALLBACK_ARTICLE = 'article'
    
    @staticmethod
    def parse_metric(text: str) -> Optional[int]:
        """
        Converte texto de métrica para número.
        Ex: "1.2K" -> 1200, "5M" -> 5000000
        """
        if not text or text.strip() == "":
            return None
        
        text = text.strip().upper().replace(",", "").replace(".", "")
        
        try:
            # Números simples
            if text.isdigit():
                return int(text)
            
            # Com sufixos
            multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}
            for suffix, mult in multipliers.items():
                if suffix in text:
                    num = float(text.replace(suffix, ""))
                    return int(num * mult)
            
            return int(float(text))
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def extract_post_id_from_url(url: str) -> Optional[str]:
        """Extrai o ID do post de uma URL."""
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_handle_from_url(url: str) -> str:
        """Extrai o handle do autor de uma URL de post."""
        match = re.search(r'x\.com/([^/]+)/status/', url)
        if match:
            return match.group(1)
        match = re.search(r'twitter\.com/([^/]+)/status/', url)
        return match.group(1) if match else ""
    
    @staticmethod
    async def extract_from_article(article: Locator) -> Optional[Post]:
        """
        Extrai dados de um elemento article (post).
        
        Args:
            article: Locator do Playwright para o elemento article
            
        Returns:
            Post extraído ou None se falhar
        """
        try:
            # 1. Encontrar link do post (identificador principal)
            post_url = None
            post_id = None
            
            # Procurar links que contenham /status/
            links = await article.locator('a[href*="/status/"]').all()
            for link in links:
                href = await link.get_attribute("href")
                if href and "/status/" in href:
                    # Normalizar URL
                    if href.startswith("/"):
                        href = f"https://x.com{href}"
                    elif not href.startswith("http"):
                        href = f"https://x.com/{href}"
                    
                    post_id = PostExtractor.extract_post_id_from_url(href)
                    if post_id:
                        post_url = href.replace("twitter.com", "x.com")
                        break
            
            if not post_id or not post_url:
                return None
            
            # 2. Extrair handle do autor
            author_handle = PostExtractor.extract_handle_from_url(post_url)
            
            # 3. Extrair nome do autor
            author_name = ""
            try:
                # Tentar pelo data-testid primeiro
                user_name_el = article.locator('[data-testid="User-Name"]').first
                if await user_name_el.count() > 0:
                    name_span = user_name_el.locator('span').first
                    if await name_span.count() > 0:
                        author_name = await name_span.inner_text()
            except Exception:
                pass
            
            # Fallback: usar o handle como nome
            if not author_name:
                author_name = f"@{author_handle}"
            
            # 4. Extrair data/hora
            post_datetime = None
            try:
                time_el = article.locator('time').first
                if await time_el.count() > 0:
                    datetime_str = await time_el.get_attribute("datetime")
                    if datetime_str:
                        post_datetime = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            except Exception:
                pass
            
            # 5. Extrair texto do post
            text = ""
            try:
                # Tentar pelo data-testid
                text_el = article.locator('[data-testid="tweetText"]').first
                if await text_el.count() > 0:
                    text = await text_el.inner_text()
            except Exception:
                pass
            
            # 6. Extrair métricas
            metrics = PostMetrics()
            try:
                # Likes
                like_el = article.locator('[data-testid="like"]').first
                if await like_el.count() > 0:
                    like_text = await like_el.inner_text()
                    metrics.likes = PostExtractor.parse_metric(like_text)
                
                # Retweets/Reposts
                retweet_el = article.locator('[data-testid="retweet"]').first
                if await retweet_el.count() > 0:
                    rt_text = await retweet_el.inner_text()
                    metrics.reposts = PostExtractor.parse_metric(rt_text)
                
                # Replies
                reply_el = article.locator('[data-testid="reply"]').first
                if await reply_el.count() > 0:
                    reply_text = await reply_el.inner_text()
                    metrics.replies = PostExtractor.parse_metric(reply_text)
                
                # Views - abordagem robusta com múltiplos métodos
                views_found = False
                
                # Método 1: Procurar link de analytics no grupo de métricas
                if not views_found:
                    try:
                        metrics_group = article.locator('[role="group"]').last
                        if await metrics_group.count() > 0:
                            # Procurar todos os links no grupo
                            all_links = await metrics_group.locator('a').all()
                            for link in all_links:
                                href = await link.get_attribute('href') or ''
                                if '/analytics' in href:
                                    views_text = await link.inner_text()
                                    parsed = PostExtractor.parse_metric(views_text)
                                    if parsed and parsed > 0:
                                        metrics.views = parsed
                                        views_found = True
                                        break
                    except:
                        pass
                
                # Método 2: Procurar pelo aria-label que contém "views"
                if not views_found:
                    try:
                        views_el = article.locator('[aria-label*="view"], [aria-label*="View"]').first
                        if await views_el.count() > 0:
                            aria = await views_el.get_attribute('aria-label')
                            if aria:
                                import re
                                match = re.search(r'([\d,.\s]+[KMB]?)\s*views?', aria, re.IGNORECASE)
                                if match:
                                    val = PostExtractor.parse_metric(match.group(1).strip())
                                    if val and val > 0:
                                        metrics.views = val
                                        views_found = True
                    except:
                        pass
                
                # Método 3: Seletor direto de analytics
                if not views_found:
                    try:
                        analytics_el = article.locator('a[href*="/analytics"]').first
                        if await analytics_el.count() > 0:
                            views_text = await analytics_el.inner_text()
                            parsed = PostExtractor.parse_metric(views_text)
                            if parsed and parsed > 0:
                                metrics.views = parsed
                                views_found = True
                    except:
                        pass
                
                # Método 4: Procurar por span com número grande (geralmente é views)
                if not views_found:
                    try:
                        # No X, views geralmente é o último número no grupo de métricas
                        spans = await article.locator('[role="group"] span').all()
                        for span in reversed(spans):  # Começar do final
                            text = await span.inner_text()
                            parsed = PostExtractor.parse_metric(text)
                            # Views geralmente são maiores que likes
                            if parsed and parsed > 0:
                                current_likes = metrics.likes or 0
                                # Se o número for significativamente maior que likes, provavelmente é views
                                if parsed > current_likes * 2 and parsed > 100:
                                    metrics.views = parsed
                                    views_found = True
                                    break
                    except:
                        pass
                        
            except Exception:
                pass
            
            # 7. Extrair links externos
            links_list = []
            try:
                card_links = await article.locator('a[href*="t.co"]').all()
                for link in card_links:
                    href = await link.get_attribute("href")
                    # Tentar pegar a URL expandida do título
                    title = await link.get_attribute("title")
                    if title and title.startswith("http"):
                        links_list.append(title)
                    elif href and "t.co" in href:
                        links_list.append(href)
            except Exception:
                pass
            
            # 8. Extrair hashtags
            hashtags = re.findall(r'#\w+', text)
            
            # 9. Extrair mentions
            mentions = re.findall(r'@\w+', text)
            
            # 10. Extrair URLs de mídia
            media_urls = []
            try:
                # Imagens
                images = await article.locator('img[src*="pbs.twimg.com/media"]').all()
                for img in images:
                    src = await img.get_attribute("src")
                    if src:
                        media_urls.append(src)
                
                # Vídeos (poster ou thumbnail)
                videos = await article.locator('video').all()
                for video in videos:
                    poster = await video.get_attribute("poster")
                    if poster:
                        media_urls.append(poster)
            except Exception:
                pass
            
            # 11. Detectar tipo de post
            is_repost = False
            is_reply = False
            is_quote = False
            
            try:
                # Repost: tem indicador "Reposted" ou "retweeted"
                repost_indicator = article.locator('[data-testid="socialContext"]')
                if await repost_indicator.count() > 0:
                    social_text = await repost_indicator.inner_text()
                    if "repost" in social_text.lower() or "retweeted" in social_text.lower():
                        is_repost = True
                
                # Reply: começa com "Replying to"
                reply_indicator = article.locator('text="Replying to"')
                if await reply_indicator.count() > 0:
                    is_reply = True
                
                # Quote: tem outro tweet embutido
                quote_container = article.locator('[data-testid="quoteTweet"]')
                if await quote_container.count() > 0:
                    is_quote = True
            except Exception:
                pass
            
            return Post(
                post_id=post_id,
                url=post_url,
                datetime=post_datetime,
                author_name=author_name.strip(),
                author_handle=author_handle,
                text=text.strip(),
                metrics=metrics,
                links=list(set(links_list)),
                hashtags=list(set(hashtags)),
                mentions=list(set(mentions)),
                media_urls=list(set(media_urls)),
                is_reply=is_reply,
                is_repost=is_repost,
                is_quote=is_quote,
            )
        
        except Exception as e:
            # Log do erro mas não propaga - retorna None
            print(f"Erro ao extrair post: {e}")
            return None
    
    @staticmethod
    async def extract_all_from_page(page: Page) -> list[Post]:
        """
        Extrai todos os posts visíveis na página.
        
        Args:
            page: Página do Playwright
            
        Returns:
            Lista de posts extraídos
        """
        posts = []
        seen_ids = set()
        
        # Tentar seletor principal
        articles = await page.locator(PostExtractor.ARTICLE_SELECTOR).all()
        
        # Fallback se não encontrar
        if not articles:
            articles = await page.locator(PostExtractor.FALLBACK_ARTICLE).all()
        
        for article in articles:
            try:
                post = await PostExtractor.extract_from_article(article)
                if post and post.post_id not in seen_ids:
                    posts.append(post)
                    seen_ids.add(post.post_id)
            except Exception:
                continue
        
        return posts
