import asyncio
import re
import sys
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

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
SCREENSHOT_FINAL = "instagram_signup_filled.png"
SCREENSHOT_ERROR = "error_missing_element.png"


async def try_selectors(page, name, selectors, timeout_per=4000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            await loc.wait_for(state="visible", timeout=timeout_per)
            print(f"  ✅ {name} → match با: {sel}")
            return loc
        except PlaywrightTimeoutError:
            continue
        except Exception as e:
            print(f"     ⚠️  خطا در '{sel}': {e}")
            continue
    print(f"  ❌ {name} → هیچ سلکتوری جواب نداد")
    return None


async def select_dropdown(page, combobox, value):
    """باز کردن dropdown و انتخاب گزینه با تطابق دقیق داخل همان listbox."""
    listbox_id = await combobox.get_attribute("aria-controls")
    print(f"    listbox id: {listbox_id}")

    # باز کردن dropdown
    await combobox.click()
    await page.wait_for_timeout(700)

    # اسکوپ به listbox مربوطه + تطابق دقیق
    if listbox_id:
        listbox = page.locator(f"#{listbox_id}")
        await listbox.wait_for(state="visible", timeout=5000)
        option = listbox.locator("div[role='option']").filter(
            has_text=re.compile(rf"^{re.escape(value)}$")
        ).first
    else:
        # fallback
        option = page.locator("div[role='option']").filter(
            has_text=re.compile(rf"^{re.escape(value)}$")
        ).first

    await option.wait_for(state="visible", timeout=5000)
    await option.click()
    await page.wait_for_timeout(500)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            print(f"🌐 باز کردن صفحه: {SIGNUP_URL}")
            await page.goto(SIGNUP_URL, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(4000)

            # بستن بنر کوکی‌ها اگر بود
            for txt in ["Allow all cookies", "Accept all", "Only allow essential cookies", "Accept"]:
                try:
                    btn = page.get_by_role("button", name=txt, exact=False).first
                    if await btn.is_visible(timeout=1500):
                        await btn.click()
                        print(f"  🍪 بستن بنر: {txt}")
                        await page.wait_for_timeout(800)
                        break
                except Exception:
                    pass

            print("✅ صفحه بارگذاری شد.\n")

            # ── سلکتورهای مقاوم ────────────────────────────────
            fields = {
                "email": [
                    "//label[normalize-space()='Mobile number or email']/preceding-sibling::input",
                    "//label[contains(text(), 'Mobile number')]/preceding-sibling::input",
                ],
                "password": [
                    "input[type='password']",
                ],
                "month": [
                    "div[aria-label='Select Month']",
                ],
                "day": [
                    "div[aria-label='Select Day']",
                ],
                "year": [
                    "div[aria-label='Select Year']",
                ],
                "fullname": [
                    "//label[normalize-space()='Full name']/preceding-sibling::input",
                    "input[aria-label='Full name']",
                    "input[aria-label='Full Name']",
                ],
                "username": [
                    "input[aria-label='Username']",
                    "//label[normalize-space()='Username']/preceding-sibling::input",
                ],
            }

            print("🔍 بررسی و پیدا کردن المان‌ها:")
            locators = {}
            missing = []
            for name, sels in fields.items():
                loc = await try_selectors(page, name, sels)
                if loc is None:
                    missing.append(name)
                locators[name] = loc

            if missing:
                print(f"\n❌ المان‌های پیدا نشده: {missing}")
                await page.screenshot(path=SCREENSHOT_ERROR, full_page=True)
                print(f"📸 اسکرین‌شات خطا: {SCREENSHOT_ERROR}")
                await browser.close()
                sys.exit(1)

            print("\n✏️  پر کردن فیلدها...")

            # ── Email ────────────────────────────────────────────
            await locators["email"].fill(FAKE_DATA["email"])
            print("  ✅ Email")

            # ── Password ─────────────────────────────────────────
            await locators["password"].fill(FAKE_DATA["password"])
            print("  ✅ Password")

            # ── Month ────────────────────────────────────────────
            await select_dropdown(page, locators["month"], FAKE_DATA["month"])
            print(f"  ✅ Month → {FAKE_DATA['month']}")

            # ── Day ──────────────────────────────────────────────
            await select_dropdown(page, locators["day"], FAKE_DATA["day"])
            print(f"  ✅ Day → {FAKE_DATA['day']}")

            # ── Year ─────────────────────────────────────────────
            await select_dropdown(page, locators["year"], FAKE_DATA["year"])
            print(f"  ✅ Year → {FAKE_DATA['year']}")

            # ── Full Name ────────────────────────────────────────
            await locators["fullname"].fill(FAKE_DATA["fullname"])
            print("  ✅ Full Name")

            # ── Username ─────────────────────────────────────────
            await locators["username"].fill(FAKE_DATA["username"])
            print("  ✅ Username")

            # ── I agree ──────────────────────────────────────────
            try:
                accept = page.get_by_text("I agree", exact=False).first
                if await accept.is_visible(timeout=2000):
                    await accept.click()
                    print("  ✅ I agree تیک زده شد")
                else:
                    print("  ℹ️  گزینه I agree وجود ندارد (نرمال)")
            except Exception:
                print("  ℹ️  گزینه I agree وجود ندارد (نرمال)")

            print("\n⏸️  Submit زده نمی‌شود.")

            await page.wait_for_timeout(1500)
            await page.screenshot(path=SCREENSHOT_FINAL, full_page=True)
            print(f"📸 اسکرین‌شات نهایی: {SCREENSHOT_FINAL}")

        except Exception as e:
            print(f"\n❌ خطا: {e}")
            try:
                await page.screenshot(path=SCREENSHOT_ERROR, full_page=True)
                print(f"📸 اسکرین‌شات خطا: {SCREENSHOT_ERROR}")
            except Exception:
                pass
            await browser.close()
            sys.exit(1)

        await browser.close()
        print("\n🎉 تمام شد!")


if __name__ == "__main__":
    asyncio.run(main())
