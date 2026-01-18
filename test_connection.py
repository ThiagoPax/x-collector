#!/usr/bin/env python3
"""Script de teste de conexão ao Chrome."""
import asyncio
import sys

async def test_chrome_connection():
    """Testa conexão ao Chrome via CDP."""
    from playwright.async_api import async_playwright
    
    print("🔍 Testando conexão ao Chrome na porta 9222...")
    
    pw = await async_playwright().start()
    
    try:
        browser = await pw.chromium.connect_over_cdp(
            "http://127.0.0.1:9222",
            timeout=5000,
        )
        print("✅ Conectado ao browser!")
        
        contexts = browser.contexts
        print(f"📁 Contextos encontrados: {len(contexts)}")
        
        if contexts:
            context = contexts[0]
            pages = context.pages
            print(f"📄 Páginas abertas: {len(pages)}")
            
            for i, page in enumerate(pages):
                print(f"   [{i}] {page.url}")
            
            # Verificar se está no X
            for page in pages:
                if "x.com" in page.url or "twitter.com" in page.url:
                    print(f"\n✅ Página do X encontrada: {page.url}")
                    
                    # Verificar login
                    try:
                        await page.wait_for_selector(
                            '[data-testid="SideNav_AccountSwitcher_Button"]',
                            timeout=5000
                        )
                        print("✅ Usuário está LOGADO no X!")
                    except:
                        print("⚠️ Usuário NÃO está logado no X")
                    
                    break
            else:
                print("\n⚠️ Nenhuma página do X aberta. Navegue para x.com no Chrome.")
        
        print("\n🎉 Teste de conexão passou! O sistema está pronto.")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {e}")
        print("\n📋 Soluções:")
        print("   1. Feche TODAS as janelas do Chrome")
        print("   2. Execute: ./start_chrome.sh")
        print("   3. Rode este teste novamente")
        return False
        
    finally:
        await pw.stop()


if __name__ == "__main__":
    success = asyncio.run(test_chrome_connection())
    sys.exit(0 if success else 1)
