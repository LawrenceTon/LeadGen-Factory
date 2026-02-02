from playwright_stealth import stealth_sync

USER_AGENTS = {
    "Chrome": None, # Default Playwright User-Agent
    "Edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mobile": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
}

def setup_stealth(page):
    """
    Applies stealth settings to the page.
    Attempts to use playwright-stealth, falls back to manual injection if it fails.
    """
    try:
        stealth_sync(page)
    except Exception as e:
        print(f"Stealth Import Error (Fallback Activated): {e}")
        # Manual Fallback
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def nuke_popups(page):
    """
    Attempts to close or hide common cookie/popup modals.
    """
    try:
        # 1. Click common allow/close buttons
        selectors = [
            '#accept-cookies', 
            '#onetrust-accept-btn-handler',
            'button[class*="cookie"][class*="accept"]',
            'button[class*="agree"]',
            '[aria-label="Close"]', 
            '.modal-close',
            'button[name="agree"]'
        ]
        
        for sel in selectors:
            try:
                if page.locator(sel).first.is_visible(timeout=200):
                    page.locator(sel).first.click(timeout=200)
            except:
                pass

        # 2. Inject CSS to hide sticky footers/modals
        page.add_style_tag(content="""
            div[class*='cookie'], 
            div[class*='modal'], 
            div[id*='cookie'], 
            #onetrust-banner-sdk,
            .cookie-banner { 
                display: none !important; 
                visibility: hidden !important;
                z-index: -9999 !important;
            }
        """)
    except Exception:
        pass

def block_media(route):
    """Abort requests for heavy media to speed up scraping."""
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        route.abort()
    else:
        route.continue_()