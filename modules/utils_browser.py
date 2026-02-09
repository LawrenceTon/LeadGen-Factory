import asyncio
import random
import os
from playwright.async_api import async_playwright

# --- STEALTH SETUP (MANUAL MODE ONLY) ---
async def setup_stealth(page):
    """
    Applies stealth settings manually.
    Removed dependency on 'playwright-stealth' to fix Python 3.14 errors.
    """
    # 1. Mask WebDriver
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # 2. Mock Chrome
    await page.add_init_script("window.chrome = { runtime: {} };")
    
    # 3. Mock Plugins
    await page.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});")
    
    # 4. Mock Languages
    await page.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});")

# --- BROWSER LAUNCHER ---
async def launch_browser(headless=False, playwright_instance=None):
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()

    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

    browser = await playwright_instance.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=headless,
        channel="chrome", 
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--start-maximized"
        ],
        viewport=None 
    )

    page = browser.pages[0] if browser.pages else await browser.new_page()
    return playwright_instance, browser, browser, page

# --- HUMAN INTERACTION ---
async def human_click(page, selector, timeout=5000):
    try:
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=timeout)
        box = await element.bounding_box()
        if box:
            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2
            await page.mouse.move(x + random.randint(-5, 5), y + random.randint(-5, 5), steps=5)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await element.click()
        return True
    except:
        return False

async def perform_manual_intervention(page, message, style=0):
    from tkinter import messagebox
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    if style == 0x04:
        result = messagebox.askyesno("LeadGen Factory", message)
        root.destroy()
        return 6 if result else 7 
    else:
        messagebox.showinfo("LeadGen Factory", message)
        root.destroy()
        return True

async def check_active_session(page, log_callback=None):
    try:
        await page.goto("https://www.linkedin.com/feed/", timeout=15000)
        await asyncio.sleep(2)
        if "login" in page.url:
            await perform_manual_intervention(page, "Please Log In to LinkedIn, then click OK.")
    except: pass