#!/usr/bin/env python3
"""Script de coleta simples via linha de comando."""
import asyncio
import sys
from pathlib import Path

# Adicionar diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

from core import XCollector, CollectionParams, SearchType
from exporters import export_to_docx


async def simple_collect(query: str, max_posts: int = 50):
    """Executa coleta simples."""
    from playwright.async_api import async_playwright
    
    print(f"🔍 Coletando posts para: {query}")
    print(f"📊 Limite: {max_posts} posts")
    print()
    
    pw = await async_playwright().start()
    
    try:
        # Conectar ao Chrome
        print("🔗 Conectando ao Chrome...")
        browser = await pw.chromium.connect_over_cdp(
            "http://127.0.0.1:9222",
            timeout=10000,
        )
        
        contexts = browser.contexts
        if not contexts:
            raise Exception("Nenhum contexto encontrado")
        
        context = contexts[0]
        page = await context.new_page()
        print("✅ Conectado!")
        
        # Configurar coletor
        collector = XCollector(headless=False)
        collector._playwright = pw
        collector.browser = browser
        collector.context = context
        collector.page = page
        
        # Parâmetros
        params = CollectionParams(
            search_type=SearchType.LATEST,
            max_posts=max_posts,
        )
        
        # Callback de progresso
        def progress(count: int, msg: str):
            print(f"  [{count}] {msg}")
        
        # Coletar
        result = await collector.collect(
            query_or_url=query,
            params=params,
            is_url=False,
            progress_callback=progress,
        )
        
        # Fechar aba
        await page.close()
        
        # Resultado
        print()
        print("=" * 50)
        print(f"✅ Coleta finalizada!")
        print(f"📊 Posts coletados: {result.total_collected}")
        print(f"⏱️ Tempo: {(result.finished_at - result.started_at).total_seconds():.1f}s")
        print(f"🛑 Motivo parada: {result.stop_reason}")
        
        if result.posts:
            # Exportar para DOCX
            filepath = export_to_docx(result)
            print(f"📄 Arquivo salvo: {filepath}")
            
            # Mostrar preview
            print()
            print("📝 Preview dos posts:")
            for i, post in enumerate(result.posts[:5], 1):
                text = post.text[:100] + "..." if len(post.text) > 100 else post.text
                print(f"  {i}. @{post.author_handle}: {text}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\n📋 Certifique-se de que:")
        print("   1. Chrome está rodando (./start_chrome.sh)")
        print("   2. Você está logado no X")
        raise
        
    finally:
        await pw.stop()


if __name__ == "__main__":
    # Query padrão ou argumento
    query = sys.argv[1] if len(sys.argv) > 1 else "python lang:pt"
    max_posts = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    asyncio.run(simple_collect(query, max_posts))
