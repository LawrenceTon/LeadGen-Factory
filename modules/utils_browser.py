# modules/utils_browser.py

# Dictionary of Browser Masks
USER_AGENTS = {
    "Chrome": None, # Default
    "Edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mobile": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
}

def setup_stealth(page):
    """
    Applies stealth settings to the page.
    Uses a 'Safe Import' to prevent crashing if the library is missing.
    """
    try:
        # We import INSIDE the function so the app launches even if this fails
        from playwright_stealth import stealth_sync
        stealth_sync(page)
    except (ImportError, ModuleNotFoundError, AttributeError):
        print("⚠️ Stealth Library not compatible. Using Manual Stealth Mode.")
        
        # --- Manual Fallback (The "Mask") ---
        # 1. Hide the "I am a Robot" flag
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 2. Fake Plugins (Bots usually have 0 plugins)
        page.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")

def nuke_popups(page):
    """
    The 'Pop-up Assassin': Closes cookie banners and modals.
    """
    selectors = [
        '#accept-cookies', 'button[id*="cookie"]', 'button[class*="cookie"]', 
        'button[class*="accept"]', '[aria-label="Close"]', '.modal-close'
    ]
    
    # 1. Click Buttons
    for sel in selectors:
        try:
            if page.is_visible(sel, timeout=200):
                page.click(sel)
                print(f"   ⚔️ Nuked popup: {sel}")
        except: pass

    # 2. Hide Overlays (CSS Injection)
    try:
        page.add_style_tag(content="div[class*='cookie'], div[class*='modal'] { display: none !important; }")
    except: pass