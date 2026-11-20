import asyncio
import os
import time
from playwright.async_api import async_playwright

FRONTEND_URL = "https://fitcoach-frontend-1043820773342.us-east1.run.app"
RECORD_DIR = "/config/Desktop/BuildWithGemini/demo_recording"

async def record_demo():
    os.makedirs(RECORD_DIR, exist_ok=True)
    async with async_playwright() as p:
        # Launch browser with recording enabled
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        context = await browser.new_context(
            record_video_dir=RECORD_DIR,
            record_video_size={"width": 1280, "height": 800},
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        print("Navigating to frontend...")
        await page.goto(FRONTEND_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        # 1. First interaction: Workout logging & calories burn estimation
        print("Sending prompt 1: Workout logging...")
        prompt_1 = "我今天深蹲做了 4 組 80kg 各 10 下，請幫我記錄運動並估算熱量消耗與提供訓練解析！"
        await page.fill("#input", prompt_1)
        await asyncio.sleep(1)
        await page.click("button[type='submit']")

        # Wait for agent response to finish rendering
        print("Waiting for prompt 1 response...")
        start_time = time.time()
        while time.time() - start_time < 90:
            agent_bubbles = await page.query_selector_all(".msg-row.agent .bubble")
            if agent_bubbles:
                last_bubble = agent_bubbles[-1]
                text = await last_bubble.inner_text()
                if text and text.strip() != "…" and len(text.strip()) > 10:
                    print(f"Prompt 1 response received: {text[:80]}...")
                    break
            await asyncio.sleep(2)
        
        await asyncio.sleep(6)  # Let viewer read prompt 1 response

        # 2. Second interaction: Rich tool call + image generation
        print("Sending prompt 2: Milestone celebration badge image...")
        prompt_2 = "太棒了！我已經連續堅持運動一整週，請為我生成一張專屬的健身里程碑金色榮譽獎章圖！"
        await page.fill("#input", prompt_2)
        await asyncio.sleep(1)
        await page.click("button[type='submit']")

        print("Waiting for prompt 2 response with generated image...")
        start_time = time.time()
        while time.time() - start_time < 120:
            agent_bubbles = await page.query_selector_all(".msg-row.agent .bubble")
            if len(agent_bubbles) >= 2:
                last_bubble = agent_bubbles[-1]
                text = await last_bubble.inner_text()
                images = await last_bubble.query_selector_all("img")
                if (text and text.strip() != "…" and len(text.strip()) > 10) or images:
                    print(f"Prompt 2 response received with {len(images)} images!")
                    break
            await asyncio.sleep(2)

        # Scroll to bottom smoothly to showcase cards and images
        await asyncio.sleep(8)
        await page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        await asyncio.sleep(6)

        # Close page and context to finalize video recording
        await page.close()
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        print(f"Demo video saved to: {video_path}")
        
        final_mp4 = "/config/Desktop/BuildWithGemini/fitcoach_demo.mp4"
        # Convert webm to standardized mp4 using ffmpeg
        os.system(f"ffmpeg -y -i '{video_path}' -c:v libx264 -pix_fmt yuv420p '{final_mp4}'")
        print(f"Standardized MP4 video saved to: {final_mp4}")

if __name__ == "__main__":
    asyncio.run(record_demo())
