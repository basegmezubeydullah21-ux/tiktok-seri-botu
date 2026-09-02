import os
import glob
import json
import asyncio
from playwright.async_api import async_playwright

async def process_user(user_file):
    try:
        with open(user_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Dosya okuma hatası ({user_file}): {e}")
        return

    my_user = data.get("myUser")
    target_user = data.get("targetUser")
    session_id = data.get("sessionId")

    if not all([my_user, target_user, session_id]):
        print(f"⚠️ Eksik bilgi barındıran dosya atlandı: {user_file}")
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

            # Beğen butonunu kontrol et
            like_button = page.locator('span[data-e2e="like-icon"]').first
            await like_button.click()
            print(f"✅ Başarılı: @{my_user}, @{target_user} kullanıcısının son videosunu beğendi!")

        except Exception as e:
            print(f"❌ @{my_user} için işlem sırasında hata oluştu: {e}")

        await browser.close()

async def main():
    user_files = glob.glob("users/*.json")
    if not user_files:
        print("⚠️ 'users/' klasöründe işlenecek JSON dosyası bulunamadı!")
        return

    print(f"Bulunan kullanıcı sayısı: {len(user_files)}")
    for user_file in user_files:
        await process_user(user_file)

if __name__ == "__main__":
    asyncio.run(main())
