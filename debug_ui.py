import asyncio
import os
import json
from playwright.async_api import async_playwright
from pathlib import Path

async def debug_svg_flow():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # Listen to console errors
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: [{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: print(f"BROWSER EXCEPTION: {exc}"))

        print("Navigating to http://localhost:5173...")
        try:
            await page.goto("http://localhost:5173", timeout=10000)
        except Exception as e:
            print(f"Failed to connect to frontend: {e}")
            await browser.close()
            return

        # 1. Input prompt
        prompt = "一个人体模型，标注着12导联心电图的电极位置"
        print(f"Entering prompt: {prompt}")
        await page.fill("textarea", prompt)
        
        # 2. Click Generate
        print("Clicking Generate...")
        await page.click("button.generate-btn")

        # 3. Wait for progress
        print("Waiting for generation to start and iterations to appear...")
        # Wait for the first iteration to appear in the filmstrip
        try:
            # The filmstrip items have class .filmstrip-item
            await page.wait_for_selector(".filmstrip-item", timeout=60000)
            print("Iteration detected in filmstrip.")
            
            # Wait a bit more for the SVG to render in the stage
            await asyncio.sleep(5)
            
            # 4. Capture state
            print("Taking screenshot...")
            await page.screenshot(path="debug_screenshot.png")
            
            # 5. Inspect DOM
            svg_content = await page.inner_html(".svg-content")
            print(f"--- SVG Content Start ---\n{svg_content[:500]}...\n--- SVG Content End ---")
            
            # Check for empty or broken SVG
            if not svg_content.strip():
                print("CRITICAL: .svg-content is EMPTY!")
            elif "<svg" not in svg_content.lower():
                print("CRITICAL: .svg-content does not contain an <svg> tag!")
            
            # Check dimensions
            stage_rect = await page.eval_on_selector(".svg-wrapper", "el => el.getBoundingClientRect()")
            print(f"Stage wrapper dimensions: {stage_rect}")
            
        except Exception as e:
            print(f"Timed out or failed during generation: {e}")
            await page.screenshot(path="debug_error.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_svg_flow())
