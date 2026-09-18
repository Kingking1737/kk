import asyncio
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
    """هر سلکتور را امتحان می‌کند؛ اولین موردی که visible باشد برمی‌گرداند."""
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


async def dump_debug(page):
    """چاپ همه label ها و input ها برای دیباگ."""
    print("\n───── DEBUG ─────")
    print(f"URL فعلی: {page.url}")
    print(f"Title: {await page.title()}")

    labels = await page.locator("label").all()
    print(f"\nتعداد label: {len(labels)}")
    for i, lbl in enumerate(labels[:30]):
        try:
            txt = (await lbl.inner_text()).strip().replace("\n", " ")
            visible = await lbl.is_visible()
            print(f"  [{i}] visible={visible} text='{txt[:80]}'")
        except Exception:
            pass

    inputs = await page.locator("input").all()
    print(f"\nتعداد input: {len(inputs)}")
    for i, inp in enumerate(inputs[:30]):
        try:
            t = await inp.get_attribute("type")
            al = await inp.get_attribute("aria-label")
            id_ = await inp.get_attribute("id")
            visible = await inp.is_visible()
            print(f"  [{i}] visible={visible} type='{t}' aria-label='{al}' id='{id_}'")
        except Exception:
            pass
    print("───── END DEBUG ─────\n")


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

        # ── لیست سلکتورهای fallback برای هر فیلد ──────────────
        fields = {
            "email": [
                "//label[normalize-space()='Mobile number or email']/preceding-sibling::input",
                "//label[contains(text(), 'Mobile number')]/preceding-sibling::input",
                "input[type='text']",  # fallback نهایی
            ],
            "password": [
                "input[type='password']",
            ],
            "month": [
                "div[aria-label='Select Month']",
                "[role='combobox'][aria-label*='Month']",
            ],
            "day": [
                "div[aria-label='Select Day']",
                "[role='combobox'][aria-label*='Day']",
            ],
            "year": [
                "div[aria-label='Select Year']",
                "[role='combobox'][aria-label*='Year']",
            ],
            "fullname": [
                # ۱: XPath با preceding-sibling
                "//label[normalize-space()='Full name']/preceding-sibling::input",
                # ۲: XPath بدون normalize (case-sensitive)
                "//label[text()='Full name']/preceding-sibling::input",
                # ۳: CSS :has — input که بلافاصله بعدش label با متن Full name است
                "input:has(+ label:text-is('Full name'))",
                # ۴: با contains (اگر "Full Name" یا فاصله اضافه باشد)
                "//label[contains(translate(text(), 'F', 'f'), 'full name')]/preceding-sibling::input",
                # ۵: aria-label (اگر نسخه‌ای استفاده کند)
                "input[aria-label='Full name']",
                "input[aria-label='Full Name']",
                # ۶: input دوم از نوع text (چون اولی email است)
                "input[type='text'] >> nth=1",
            ],
            "username": [
                "input[aria-label='Username']",
                "//label[normalize-space()='Username']/preceding-sibling::input",
                "input[type='search']",
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
            await dump_debug(page)
            await page.screenshot(path=SCREENSHOT_ERROR, full_page=True)
            print(f"📸 اسکرین‌شات خطا: {SCREENSHOT_ERROR}")
            await browser.close()
            sys.exit(1)

        print("\n✏️  پر کردن فیلدها...")

        # ── Email ────────────────────────────────────────────────
        await locators["email"].scroll_into_view_if_needed()
        await locators["email"].fill(FAKE_DATA["email"])
        print("  ✅ Email")

        # ── Password ─────────────────────────────────────────────
        await locators["password"].fill(FAKE_DATA["password"])
        print("  ✅ Password")

        # ── Month ────────────────────────────────────────────────
        await locators["month"].click()
        await page.wait_for_timeout(700)
        await page.locator("div[role='option']").filter(
            has_text=FAKE_DATA["month"]
        ).first.click()
        print(f"  ✅ Month → {FAKE_DATA['month']}")

        # ── Day ──────────────────────────────────────────────────
        await locators["day"].click()
        await page.wait_for_timeout(700)
        await page.locator("div[role='option']").filter(
            has_text=FAKE_DATA["day"]
        ).first.click()
        print(f"  ✅ Day → {FAKE_DATA['day']}")

        # ── Year ─────────────────────────────────────────────────
        await locators["year"].click()
        await page.wait_for_timeout(700)
        await page.locator("div[role='option']").filter(
            has_text=FAKE_DATA["year"]
        ).first.click()
        print(f"  ✅ Year → {FAKE_DATA['year']}")

        # ── Full Name ────────────────────────────────────────────
        await locators["fullname"].scroll_into_view_if_needed()
        await locators["fullname"].fill(FAKE_DATA["fullname"])
        print("  ✅ Full Name")

        # ── Username ─────────────────────────────────────────────
        await locators["username"].scroll_into_view_if_needed()
        await locators["username"].fill(FAKE_DATA["username"])
        print("  ✅ Username")

        # ── تیک I agree ──────────────────────────────────────────
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

        await browser.close()
        print("\n🎉 تمام شد!")


if __name__ == "__main__":
    asyncio.run(main())
