import os
import json
import asyncio
from playwright.async_api import async_playwright

def parse_cookies_txt(cookies_str):
    """cookies.txt (Netscape) formatındaki metni Playwright cookie formatına dönüştürür."""
    cookies = []
    lines = cookies_str.strip().split('\n')
    for line in lines:
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            domain = parts[0]
            path = parts[2]
            secure = parts[3].lower() == 'true'
            name = parts[5]
            value = parts[6].strip()
            cookies.append({
                'name': name,
                'value': value,
                'domain': domain if domain.startswith('.') else f".{domain}",
                'path': path,
                'secure': secure
            })
    return cookies

async def process_user(user_data):
    my_user = user_data.get("myUser")
    target_user = user_data.get("targetUser")
    cookies_raw = user_data.get("cookiesTxt")

    if not all([my_user, target_user, cookies_raw]):
        print(f"⚠️ Eksik bilgi barındıran kullanıcı atlandı.")
        return

    print(f"\n[+] İşlem Başlatılıyor: @{my_user} -> @{target_user}")
    cookies = parse_cookies_txt(cookies_raw)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # cookies.txt'den yüklenen çerezleri ekle
        await context.add_cookies(cookies)

        page = await context.new_page()
        await context.route("**/*.{png,jpg,jpeg,webp,mp4,webm,gif,svg,css,font}", lambda route: route.abort())

        target_url = f"https://www.tiktok.com/@{target_user}"
        print(f" Profile gidiliyor: {target_url}")

        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # İlk videoya tıkla
            first_video = page.locator('div[data-e2e="user-post-item"]').first
            await first_video.click()
            await page.wait_for_timeout(3000)

            # Beğen butonuna tıkla
            like_button = page.locator('span[data-e2e="like-icon"]').first
            await like_button.click()
            print(f"✅ @{my_user}, @{target_user} kullanıcısının videosunu başarıyla beğendi!")

        except Exception as e:
            print(f"❌ Hata oluştu (@{my_user}): {e}")

        await browser.close()

async def main():
    raw_data = os.environ.get("USERS_JSON", "[]")
    try:
        users = json.loads(raw_data)
    except Exception as e:
        print(f"❌ JSON okuma hatası: {e}")
        return

    for user in users:
        await process_user(user)

if __name__ == "__main__":
    asyncio.run(main())
