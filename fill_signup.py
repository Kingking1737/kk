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
SS_FILLED  = "instagram_signup_filled.png"
SS_MODAL   = "instagram_captcha_modal.png"
SS_AFTER   = "instagram_captcha_clicked.png"
SS_ERROR   = "error_missing_element.png"

WAIT_AFTER_SUBMIT = 10_000   # 10 ثانیه
WAIT_AFTER_CLICK  = 10_000   # 10 ثانیه


async def try_selectors(page, name, selectors, timeout_per=4000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                continue
            await loc.wait_for(state="visible", timeout=timeout_per)
            print(f"  ✅ {name} → {sel}")
            return loc
        except PlaywrightTimeoutError:
            continue
        except Exception as e:
            print(f"     ⚠️  {sel}: {e}")
            continue
    print(f"  ❌ {name} → پیدا نشد")
    return None


async def select_dropdown(page, combobox, value):
    await combobox.scroll_into_view_if_needed()
    await combobox.click()
    await page.wait_for_timeout(800)
    option = page.get_by_role("option", name=value, exact=True)
    n = await option.count()
    print(f"    {n} گزینه با متن دقیق '{value}'")
    for i in range(n):
        cand = option.nth(i)
        try:
            if await cand.is_visible():
                await cand.scroll_into_view_if_needed()
                await cand.click()
                await page.wait_for_timeout(400)
                return
        except Exception:
            continue
    raise RuntimeError(f"گزینه‌ی '{value}' visible پیدا نشد")


async def find_captcha_checkbox(page, timeout_ms=8000):
    """
    دنبال چک‌باکس reCAPTCHA داخل iframe می‌گردد.
    """
    print("  🔎 جستجوی iframe های reCAPTCHA...")
    candidates = [
        "iframe[src*='recaptcha']",
        "iframe[title*='reCAPTCHA' i]",
        "iframe[title*='recaptcha' i]",
    ]

    deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
    while asyncio.get_event_loop().time() < deadline:
        for sel in candidates:
            cnt = await page.locator(sel).count()
            if cnt == 0:
                continue
            print(f"    {cnt} iframe با سلکتور '{sel}'")
            for i in range(cnt):
                try:
                    fl = page.frame_locator(sel).nth(i)
                    checkbox = fl.locator("#recaptcha-anchor, .recaptcha-checkbox").first
                    if await checkbox.count() == 0:
                        continue
                    if await checkbox.is_visible():
                        print(f"    ✅ چک‌باکس در iframe #{i} پیدا شد")
                        return checkbox
                except Exception as e:
                    print(f"    ⚠️  iframe #{i}: {e}")
                    continue
        await page.wait_for_timeout(500)

    print("    ❌ چک‌باکس reCAPTCHA پیدا نشد")
    return None


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

            fields = {
                "email":    ["//label[normalize-space()='Mobile number or email']/preceding-sibling::input"],
                "password": ["input[type='password']"],
                "month":    ["div[aria-label='Select Month']"],
                "day":      ["div[aria-label='Select Day']"],
                "year":     ["div[aria-label='Select Year']"],
                "fullname": [
                    "//label[normalize-space()='Full name']/preceding-sibling::input",
                    "input[aria-label='Full name']",
                ],
                "username": ["input[aria-label='Username']"],
            }

            locators, missing = {}, []
            print("🔍 بررسی المان‌ها:")
            for name, sels in fields.items():
                loc = await try_selectors(page, name, sels)
                if loc is None:
                    missing.append(name)
                locators[name] = loc

            if missing:
                print(f"\n❌ پیدا نشده: {missing}")
                await page.screenshot(path=SS_ERROR, full_page=True)
                await browser.close()
                sys.exit(1)

            print("\n✏️  پر کردن فیلدها...")
            await locators["email"].fill(FAKE_DATA["email"]);                print("  ✅ Email")
            await locators["password"].fill(FAKE_DATA["password"]);          print("  ✅ Password")
            await select_dropdown(page, locators["year"],  FAKE_DATA["year"]);   print(f"  ✅ Year → {FAKE_DATA['year']}")
            await select_dropdown(page, locators["month"], FAKE_DATA["month"]);  print(f"  ✅ Month → {FAKE_DATA['month']}")
            await select_dropdown(page, locators["day"],   FAKE_DATA["day"]);    print(f"  ✅ Day → {FAKE_DATA['day']}")
            await locators["fullname"].fill(FAKE_DATA["fullname"]);          print("  ✅ Full Name")
            await locators["username"].fill(FAKE_DATA["username"]);          print("  ✅ Username")

            await page.wait_for_timeout(800)
            await page.screenshot(path=SS_FILLED, full_page=True)
            print(f"📸 فرم پر شده: {SS_FILLED}")

            # ── Submit ──────────────────────────────────────────
            print("\n🖱️  کلیک روی Submit...")
            submit = page.locator(
                "//div[@role='button'][.//span[normalize-space()='Submit']]"
            ).first
            if await submit.count() == 0:
                submit = page.get_by_role("button", name="Submit", exact=True).first
            await submit.scroll_into_view_if_needed()
            await submit.click()
            print("  ✅ Submit کلیک شد.")

            # ── ۱۰ ثانیه صبر ────────────────────────────────────
            print(f"\n⏳ انتظار {WAIT_AFTER_SUBMIT/1000:.0f} ثانیه...")
            await page.wait_for_timeout(WAIT_AFTER_SUBMIT)

            # ── پیدا کردن چک‌باکس reCAPTCHA ────────────────────
            print("\n🔍 بررسی وجود reCAPTCHA...")
            checkbox = await find_captcha_checkbox(page)

            if checkbox is None:
                # modal نیامده یا چک‌باکس نیست → اسکرین‌شات و خروج
                await page.screenshot(path=SS_MODAL, full_page=True)
                print(f"📸 اسکرین‌شات بعد از Submit: {SS_MODAL}")
                print("ℹ️  reCAPTCHA پیدا نشد.")
            else:
                # ── اسکرین‌شات قبل از کلیک ─────────────────
                await page.screenshot(path=SS_MODAL, full_page=True)
                print(f"📸 اسکرین‌شات modal قبل از کلیک: {SS_MODAL}")

                # ── کلیک روی چک‌باکس ──────────────────────
                print("\n🖱️  کلیک روی چک‌باکس 'I'm not a robot'...")
                clicked = False
                for attempt in range(3):
                    try:
                        await checkbox.scroll_into_view_if_needed()
                        await checkbox.click(timeout=5000)
                        clicked = True
                        print(f"  ✅ کلیک موفق (تلاش #{attempt+1})")
                        break
                    except Exception as e:
                        print(f"  ⚠️  تلاش #{attempt+1} ناموفق: {e}")
                        await page.wait_for_timeout(700)

                if not clicked:
                    # تلاش با force
                    try:
                        await checkbox.click(force=True, timeout=5000)
                        print("  ✅ با force کلیک شد")
                        clicked = True
                    except Exception as e:
                        print(f"  ❌ force هم نشد: {e}")

                # ── ۱۰ ثانیه صبر بعد از کلیک ──────────────
                print(f"\n⏳ انتظار {WAIT_AFTER_CLICK/1000:.0f} ثانیه بعد از کلیک...")
                await page.wait_for_timeout(WAIT_AFTER_CLICK)

                # ── اسکرین‌شات نهایی ─────────────────────
                await page.screenshot(path=SS_AFTER, full_page=True)
                print(f"📸 اسکرین‌شات بعد از کلیک: {SS_AFTER}")

            print("\n🎉 تمام شد!")

        except Exception as e:
            print(f"\n❌ خطا: {e}")
            try:
                await page.screenshot(path=SS_ERROR, full_page=True)
                print(f"📸 اسکرین‌شات خطا: {SS_ERROR}")
            except Exception:
                pass
            await browser.close()
            sys.exit(1)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
