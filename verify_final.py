import asyncio
import httpx
import json
from playwright.async_api import async_playwright

async def verify_streaming():
    print("Step 1: Verifying Backend SSE Stream directly...")
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("POST", "http://localhost:8000/generate-stream", 
                                   json={"prompt": "一个人体模型，标注着12导联心电图的电极位置"},
                                   timeout=120) as response:
                count = 0
                has_svg = False
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            print("  [SSE] Received [DONE] marker.")
                            break
                        
                        try:
                            payload = json.loads(data)
                            count += 1
                            if payload.get("svg_code"):
                                # Check for sanitization
                                if "```" in payload["svg_code"]:
                                    print("  [ERROR] SVG Code is NOT sanitized (found ```)!")
                                    return False
                                has_svg = True
                            
                            print(f"  [SSE] Received chunk {count}: Iteration {payload.get('iteration')} (Status: {payload.get('vqa_results', {}).get('status')})")
                            
                            if has_svg:
                                print("  [SSE] Successfully received first sanitized SVG iteration.")
                                break
                        except Exception as e:
                            print(f"  [ERROR] Parse error: {e}")
                
                if count == 0:
                    print("  [ERROR] No data received from stream!")
                    return False
        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")
            return False
    
    print("\nStep 2: Verifying Frontend UI via Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("http://localhost:5173", timeout=20000)
            await page.fill("textarea", "一個人體模型，標註著12導聯心電圖的電極位置")
            await page.click("button.generate-btn")
            
            # Wait for first indicator
            await page.wait_for_selector(".filmstrip-item", timeout=30000)
            print("  [UI] Iteration appeared in filmstrip.")
            
            # Wait for SVG rendering
            await page.wait_for_selector(".svg-content svg", timeout=90000)
            print("  [UI] SVG successfully rendered in the stage.")
            
            await page.screenshot(path="final_delivery_verification.png")
            print("  [UI] Verification screenshot saved to final_delivery_verification.png")
            return True
        except Exception as e:
            print(f"  [ERROR] UI Verification failed: {e}")
            await page.screenshot(path="final_error.png")
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    success = asyncio.run(verify_streaming())
    if not success:
        exit(1)
