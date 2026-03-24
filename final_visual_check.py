import asyncio
from playwright.async_api import async_playwright

async def run_visual_check():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1440, 'height': 900})
        
        print("Navigating to http://localhost:5173...")
        await page.goto("http://localhost:5173", timeout=30000)
        
        prompt = "一个人体模型，标注着12导联心电图的电极位置"
        print(f"Submitting prompt: {prompt}")
        await page.fill("textarea", prompt)
        await page.click("button.generate-btn")
        
        print("Waiting for Agent to start (detecting filmstrip item)...")
        await page.wait_for_selector(".filmstrip-item", timeout=30000)
        print("Agent is active. Now waiting for SVG rendering (this may take up to 2 mins)...")
        
        # Wait for actual SVG tag inside the content area
        try:
            await page.wait_for_selector(".svg-content svg", timeout=180000)
            print("✅ SVG successfully rendered on screen!")
            
            # Additional wait to ensure it's fully painted
            await asyncio.sleep(2)
            
            screenshot_path = "final_visual_proof.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot captured: {screenshot_path}")
            
            # Check if SVG has actual content
            svg_html = await page.inner_html(".svg-content")
            print(f"SVG length: {len(svg_html)} characters.")
            
        except Exception as e:
            print(f"❌ Timed out waiting for SVG: {e}")
            await page.screenshot(path="debug_timeout_state.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_visual_check())
