import asyncio
import sys
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ── اطلاعات ساختگی ──────────────────────────────────────────────
FAKE_DATA = {
    "email":    "kingkngdbjodbno@llf.com",
    "password": "Kingking00Q)@)",
    "day":      "1",
    "month":    "January",
    "year":     "1999",
    "fullname": "fjofjinoervnervnioernvemoe",
    "username": "klfeir",
}

SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/?hl=en"
SCREENSHOT_PATH = "instagram_signup_filled.png"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print(f"🌐 در حال باز کردن صفحه: {SIGNUP_URL}")
        await page.goto(SIGNUP_URL, wait_until="networkidle", timeout=60_000)
        print("✅ صفحه بارگذاری شد.")

        # ── بررسی وجود المان‌ها ──────────────────────────────────
        elements = {
            "email":    "input[type='text']",
            "password": "input[type='password']",
            "month":    "div[aria-label='Select Month']",
            "day":      "div[aria-label='Select Day']",
            "year":     "div[aria-label='Select Year']",
            "fullname": "input[aria-label='Full name']",
            "username": "input[aria-label='Username']",
        }

        print("\n🔍 بررسی وجود المان‌ها:")
        for name, selector in elements.items():
            try:
                await page.wait_for_selector(selector, timeout=10_000)
                print(f"  ✅ {name} → پیدا شد")
            except PlaywrightTimeoutError:
                print(f"  ❌ {name} → پیدا نشد")
                await page.screenshot(path="error_missing_element.png")
                print("📸 اسکرین‌شات خطا ذخیره شد: error_missing_element.png")
                await browser.close()
                sys.exit(1)

        print("\n✏️  در حال پر کردن فیلدها...")

        # ── پر کردن Email ────────────────────────────────────────
        await page.locator("input[type='text']").first.fill(FAKE_DATA["email"])
        print("  ✅ Email پر شد")

        # ── پر کردن Password ─────────────────────────────────────
        await page.locator("input[type='password']").fill(FAKE_DATA["password"])
        print("  ✅ Password پر شد")

        # ── انتخاب Month ─────────────────────────────────────────
        await page.locator("div[aria-label='Select Month']").click()
        await page.wait_for_timeout(500)
        await page.locator("div[role='option']").filter(
            has_text=FAKE_DATA["month"]
        ).click()
        print(f"  ✅ Month → {FAKE_DATA['month']}")

        # ── انتخاب Day ───────────────────────────────────────────
        await page.locator("div[aria-label='Select Day']").click()
        await page.wait_for_timeout(500)
        await page.locator("div[role='option']").filter(
            has_text=FAKE_DATA["day"]
        ).first.click()
        print(f"  ✅ Day → {FAKE_DATA['day']}")

        # ── انتخاب Year ──────────────────────────────────────────
        await page.locator("div[aria-label='Select Year']").click()
        await page.wait_for_timeout(500)
        await page.locator("div[role='option']").filter(
            has_text=FAKE_DATA["year"]
        ).first.click()
        print(f"  ✅ Year → {FAKE_DATA['year']}")

        # ── پر کردن Full Name ────────────────────────────────────
        await page.locator("input[aria-label='Full name']").fill(
            FAKE_DATA["fullname"]
        )
        print("  ✅ Full Name پر شد")

        # ── پر کردن Username ─────────────────────────────────────
        await page.locator("input[aria-label='Username']").fill(
            FAKE_DATA["username"]
        )
        print("  ✅ Username پر شد")

        # ── تیک زدن I accept (اگر وجود داشته باشد) ───────────────
        try:
            accept = page.locator("span:has-text('I agree')").first
            if await accept.is_visible(timeout=3000):
                await accept.click()
                print("  ✅ I accept تیک زده شد")
            else:
                print("  ⚠️  گزینه I accept پیدا نشد (ممکن است نیازی نباشد)")
        except Exception:
            print("  ⚠️  گزینه I accept پیدا نشد (ممکن است نیازی نباشد)")

        # ── Submit را نمی‌زنیم ──────────────────────────────────
        print("\n⏸️  Submit زده نمی‌شود (طبق درخواست).")

        # ── اسکرین‌شات نهایی ─────────────────────────────────────
        await page.wait_for_timeout(1000)
        await page.screenshot(path=SCREENSHOT_PATH, full_page=True)
        print(f"📸 اسکرین‌شات ذخیره شد: {SCREENSHOT_PATH}")

        await browser.close()
        print("\n🎉 تمام شد!")


if __name__ == "__main__":
    asyncio.run(main())
