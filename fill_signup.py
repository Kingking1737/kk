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
SS_FILLED    = "instagram_signup_filled.png"     # بعد از پر کردن فرم
SS_SUBMIT    = "instagram_after_submit.png"      # بعد از Submit
SS_CAPTCHA   = "instagram_captcha_clicked.png"   # بعد از کلیک روی reCAPTCHA
SS_ERROR     = "error_missing_element.png"       # اگر خطایی رخ داد

SUBMIT_WAIT = 10_000  # 10 ثانیه


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
    await combobox.scroll_into_view_if_needed()
    await combobox.click()
    await page.wait_for_timeout(800)
    option = page.get_by_role("option", name=value, exact=True)
    count = await option.count()
    print(f"    {count} گزینه با متن دقیق '{value}' پیدا شد")
    for i in range(count):
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


async def recaptcha_exists(page):
    """
    بررسی می‌کند آیا reCAPTCHA در صفحه هست یا نه.
    reCAPTCHA اینستاگرام داخل iframe بارگذاری می‌شود.
    """
    # 1) iframe های reCAPTCHA
    frames = page.locator(
        "iframe[src*='recaptcha'], iframe[title*='reCAPTCHA' i], iframe[title*='recaptcha' i]"
    )
    n = await frames.count()
    print(f"    تعداد iframe های reCAPTCHA: {n}")
    if n == 0:
        return None

    # 2) داخل اولین iframe دنبال چک‌باکس بگرد
    for i in range(n):
        try:
            fl = page.frame_locator(
                "iframe[src*='recaptcha'], iframe[title*='reCAPTCHA' i], iframe[title*='recaptcha' i]"
            ).nth(i)
            checkbox = fl.locator(
                "#recaptcha-anchor, .recaptcha-checkbox, .recaptcha-checkbox-border"
            ).first
            if await checkbox.count() > 0 and await checkbox.is_visible():
                print(f"    ✅ چک‌باکس reCAPTCHA در iframe #{i} پیدا شد")
                return checkbox
        except Exception as e:
            print(f"    ⚠️  خطا در iframe #{i}: {e}")
            continue
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
                    "input[aria-label='Full Name']",
                ],
                "username": ["input[aria-label='Username']"],
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
                await page.screenshot(path=SS_ERROR, full_page=True)
                print(f"📸 اسکرین‌شات خطا: {SS_ERROR}")
                await browser.close()
                sys.exit(1)

            print("\n✏️  پر کردن فیلدها...")
            await locators["email"].fill(FAKE_DATA["email"]);        print("  ✅ Email")
            await locators["password"].fill(FAKE_DATA["password"]);  print("  ✅ Password")
            await select_dropdown(page, locators["year"],  FAKE_DATA["year"]);  print(f"  ✅ Year → {FAKE_DATA['year']}")
            await select_dropdown(page, locators["month"], FAKE_DATA["month"]); print(f"  ✅ Month → {FAKE_DATA['month']}")
            await select_dropdown(page, locators["day"],   FAKE_DATA["day"]);   print(f"  ✅ Day → {FAKE_DATA['day']}")
            await locators["fullname"].fill(FAKE_DATA["fullname"]);  print("  ✅ Full Name")
            await locators["username"].fill(FAKE_DATA["username"]);  print("  ✅ Username")

            # اسکرین‌شات قبل از Submit
            await page.wait_for_timeout(800)
            await page.screenshot(path=SS_FILLED, full_page=True)
            print(f"📸 اسکرین‌شات فرم پر شده: {SS_FILLED}")

            # ── کلیک روی Submit ─────────────────────────────────
            print("\n🖱️  کلیک روی Submit...")
            submit = page.locator(
                "//div[@role='button'][.//span[normalize-space()='Submit']]"
            ).first
            if await submit.count() == 0:
                # fallback
                submit = page.get_by_role("button", name="Submit", exact=True).first
            await submit.scroll_into_view_if_needed()
            await submit.click()
            print("  ✅ Submit کلیک شد.")

            # ── ۱۰ ثانیه صبر ───────────────────────────────────
            print(f"\n⏳ انتظار {SUBMIT_WAIT/1000:.0f} ثانیه...")
            await page.wait_for_timeout(SUBMIT_WAIT)

            # ── بررسی وجود reCAPTCHA ────────────────────────────
            print("\n🔍 بررسی وجود reCAPTCHA...")
            captcha = await recaptcha_exists(page)

            if captcha is None:
                # ── reCAPTCHA نبود → همان‌جا اسکرین‌شات ─────
                print("  ℹ️  reCAPTCHA ظاهر نشد.")
                await page.screenshot(path=SS_SUBMIT, full_page=True)
                print(f"📸 اسکرین‌شات بعد از Submit: {SS_SUBMIT}")

            else:
                # ── reCAPTCHA بود → کلیک کن، ۱۰ ثانیه صبر، اسکرین‌شات ─
                print("  🖱️  کلیک روی چک‌باکس reCAPTCHA...")
                try:
                    await captcha.click()
                    print("  ✅ روی reCAPTCHA کلیک شد.")
                except Exception as e:
                    print(f"  ⚠️  کلیک روی reCAPTCHA ناموفق: {e}")
                    # تلاش دوم: با force
                    try:
                        await captcha.click(force=True)
                        print("  ✅ با force کلیک شد.")
                    except Exception as e2:
                        print(f"  ❌ کلیک دوم هم نشد: {e2}")

                print(f"\n⏳ انتظار {SUBMIT_WAIT/1000:.0f} ثانیه بعد از کلیک reCAPTCHA...")
                await page.wait_for_timeout(SUBMIT_WAIT)
                await page.screenshot(path=SS_CAPTCHA, full_page=True)
                print(f"📸 اسکرین‌شات بعد از کلیک reCAPTCHA: {SS_CAPTCHA}")

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
