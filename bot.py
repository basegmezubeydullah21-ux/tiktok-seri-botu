import os
import json
import asyncio
from playwright.async_api import async_playwright

async def process_user(data):
    my_user = data.get("myUser")
    target_user = data.get("targetUser")
    session_id = data.get("sessionId")

    if not all([my_user, target_user, session_id]):
        print(f"⚠️ Eksik bilgi barındıran veri atlandı.")
        return

    print(f"\n[+] İşlem başlatılıyor: @{my_user} -> @{target_user}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # TikTok Session Cookie Ekle
        await context.add_cookies([{
            'name': 'sessionid',
            'value': session_id,
            'domain': '.tiktok.com',
            'path': '/'
        }])

        page = await context.new_page()
        
        # Medya ve kaynakları engelleyerek kaynak tasarrufu sağla
        await context.route("**/*.{png,jpg,jpeg,webp,mp4,webm,gif,svg,css,font}", lambda route: route.abort())

        target_url = f"https://www.tiktok.com/@{target_user}"
        print(f" Profile gidiliyor: {target_url}")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # İlk videoyu bul
            first_video = page.locator('div[data-e2e="user-post-item"]').first
            await first_video.click()
            await page.wait_for_timeout(3000)

            # Beğen butonuna tıkla
            like_button = page.locator('span[data-e2e="like-icon"]').first
            await like_button.click()
            print(f"✅ Başarılı: @{my_user}, @{target_user} kullanıcısının son videosunu beğendi!")

        except Exception as e:
            print(f"❌ @{my_user} için işlem sırasında hata oluştu: {e}")

        await browser.close()

async def main():
    # Verileri GitHub Secret içinden okur
    raw_data = os.environ.get("USERS_JSON", "[]")
    try:
        users = json.loads(raw_data)
    except Exception as e:
        print(f"❌ JSON okuma hatası: {e}")
        return

    if not users:
        print("⚠️ Hiçbir kullanıcı verisi bulunamadı!")
        return

    print(f"Bulunan kullanıcı sayısı: {len(users)}")
    for user_data in users:
        await process_user(user_data)

if __name__ == "__main__":
    asyncio.run(main())
