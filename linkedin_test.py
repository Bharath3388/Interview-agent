import requests
import base64
from playwright.sync_api import sync_playwright
import time
import json
import os
from dotenv import load_dotenv
import random

# Load candidate profile from config
_config_path = os.path.join(os.path.dirname(__file__), "configs", "default_answers.json")
with open(_config_path, "r") as _f:
    _answers_config = json.load(_f)
CANDIDATE_PROFILE = _answers_config["profile"]
COMMON_ANSWERS = _answers_config["common_answers"]

# Pre-built profile context string sent with every AI prompt
PROFILE_CONTEXT = f"""Candidate profile for form filling:
- Name: {CANDIDATE_PROFILE['name']}
- City: {CANDIDATE_PROFILE['city']}
- Total years of experience: {CANDIDATE_PROFILE['years_of_experience']} year
- Current CTC: {CANDIDATE_PROFILE['current_ctc_lpa']} LPA (INR {CANDIDATE_PROFILE['current_ctc_inr']:,})
- Expected CTC: {CANDIDATE_PROFILE['expected_ctc_lpa']} LPA (INR {CANDIDATE_PROFILE['expected_ctc_inr']:,})
- Notice period: {CANDIDATE_PROFILE['notice_period_days']} days
- Immediate joiner: Yes
- Has experience in relevant technologies: Yes
- Open to relocation: Yes
- LinkedIn: {CANDIDATE_PROFILE['linkedin']}
- GitHub: {CANDIDATE_PROFILE['github']}
- Cover letter: {CANDIDATE_PROFILE['cover_letter']}
Common answers: {json.dumps(COMMON_ANSWERS, indent=2)}"""

# Load environment variables
load_dotenv()

# Configuration from env
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "https://8001-01kmjz7mphha5exraw9dp10fpg.cloudspaces.litng.ai")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Validation
if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
    print("❌ Error: Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
    print("Example .env file:")
    print("LINKEDIN_EMAIL=your@email.com")
    print("LINKEDIN_PASSWORD=yourpassword")
    exit(1)

def get_ai_action(screenshot_b64, prompt):
    """Send screenshot to Lightning AI model server"""
    print("\n" + "─" * 60)
    print("🤖 [AI REQUEST]")
    print(f"   Endpoint : {MODEL_ENDPOINT}/predict")
    # Print prompt but truncate the profile block so terminal stays readable
    short_prompt = prompt.replace(PROFILE_CONTEXT, "<PROFILE_CONTEXT>") if 'PROFILE_CONTEXT' in dir() else prompt
    print(f"   Prompt   : {short_prompt[:300]}{'...' if len(short_prompt) > 300 else ''}")
    print("─" * 60)
    try:
        response = requests.post(
            f"{MODEL_ENDPOINT}/predict",
            json={
                "prompt": prompt,
                "image_base64": screenshot_b64
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()["generated_text"]
            print(f"✅ [AI RESPONSE] {result}")
            print("─" * 60)
            return result
        else:
            print(f"❌ [AI ERROR] Status {response.status_code}: {response.text}")
            print("─" * 60)
            return None
    except Exception as e:
        print(f"❌ [AI REQUEST FAILED] {e}")
        print("─" * 60)
        return None

def human_like_typing(page, selector, text):
    """Type like a human with random delays"""
    for char in text:
        page.type(selector, char, delay=random.randint(50, 150))
        time.sleep(random.uniform(0.05, 0.2))

def login_linkedin(page):
    """Automate LinkedIn login with anti-detection measures"""
    print("🔐 Navigating to LinkedIn login...")
    page.goto("https://www.linkedin.com/login")
    
    # Random delay before starting (simulating reading page)
    time.sleep(random.uniform(2, 4))
    
    # Check if already logged in (redirected to feed)
    if "feed" in page.url:
        print("✅ Already logged in!")
        return True
    
    print(f"📝 Entering credentials for: {LINKEDIN_EMAIL}")
    
    # Human-like typing for email
    human_like_typing(page, "#username", LINKEDIN_EMAIL)
    time.sleep(random.uniform(0.5, 1.5))
    
    # Human-like typing for password
    human_like_typing(page, "#password", LINKEDIN_PASSWORD)
    time.sleep(random.uniform(0.5, 1.5))
    
    # Random delay before clicking submit
    time.sleep(random.uniform(1, 3))
    print("🖱️ Clicking submit...")
    page.click("button[type='submit']")
    
    # Wait for navigation (max 30 seconds)
    try:
        page.wait_for_url("**/feed**", timeout=30000)
        print("✅ Login successful!")
        return True
    except:
        # Check for CAPTCHA or 2FA
        if page.is_visible("text=Verification") or page.is_visible("text=Security check"):
            print("⚠️ CAPTCHA or 2FA detected! Please solve manually...")
            input("Press Enter after completing verification...")
            return True
        
        if "login" in page.url:
            print("❌ Login failed! Check credentials or if LinkedIn blocked the attempt")
            return False
        
        return True

def run_linkedin_automation():
    with sync_playwright() as p:
        # Anti-detection: use realistic user agent and viewport
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # Launch with persistent context to save session
        user_data_dir = "./linkedin_profile"
        
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=500,  # 500ms delay between actions
            viewport={"width": 1280, "height": 800},
            user_agent=user_agent,
            locale="en-US",
            record_video_dir="./videos"
        )
        
        page = context.new_page()
        
        # Handle cookie consent popup if appears
        try:
            page.click("button:has-text('Accept')", timeout=5000)
        except:
            pass
        
        # Login
        if not login_linkedin(page):
            print("Exiting due to login failure")
            context.close()
            return
        
        # Navigate to Jobs with search query directly via URL (more reliable)
        search_query = "AI Engineer"
        location = "Remote"
        print(f"🎯 Searching for: {search_query} in {location}")

        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={requests.utils.quote(search_query)}"
            f"&location={requests.utils.quote(location)}"
            f"&f_AL=true"  # Easy Apply filter
        )
        print(f"🔍 Navigating to job search results...")
        page.goto(search_url)
        time.sleep(random.uniform(4, 6))

        # Fallback: if URL navigation didn't apply filters, try clicking Easy Apply filter in UI
        print("⚡ Ensuring Easy Apply filter is active...")
        try:
            easy_apply_filter = page.locator(
                "button:has-text('Easy Apply'), "
                "label:has-text('Easy Apply'), "
                "input[value='Easy Apply']"
            ).first
            if easy_apply_filter.is_visible(timeout=4000):
                easy_apply_filter.click()
                time.sleep(random.uniform(2, 4))
        except:
            print("⚠️ Easy Apply filter already applied via URL or not found in UI, continuing...")
        
        # Main loop - scroll through all job listings and apply to Easy Apply ones
        max_jobs = 50        # upper safety cap
        applied_count = 0
        processed_urls = set()
        current_page_num = 1

        # Selector for individual job cards in the left-hand list
        job_card_selector = "li.scaffold-layout__list-item, li.jobs-search-results__list-item"

        card_index = 0  # global index across scrolls

        while applied_count < max_jobs:
            # Wait for cards to load
            try:
                page.wait_for_selector(job_card_selector, timeout=10000)
            except Exception:
                print("⚠️ Could not find job listing cards")
                break

            job_cards = page.locator(job_card_selector)
            count = job_cards.count()
            if count == 0:
                print("⚠️ No job cards found on page")
                break

            if card_index >= count:
                # Tried all cards on this page — go to next LinkedIn results page
                next_page_num = current_page_num + 1
                next_page_url = search_url + f"&start={25 * (next_page_num - 1)}"
                print(f"\n⏩ Moving to results page {next_page_num}...")
                page.goto(next_page_url)
                time.sleep(random.uniform(4, 6))
                card_index = 0
                current_page_num = next_page_num
                continue

            card = job_cards.nth(card_index)

            # Scroll card into view so it loads its detail
            try:
                card.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass
            card.click()
            time.sleep(random.uniform(1.5, 2.5))

            # Get current job URL to avoid duplicates
            job_url = page.url
            if job_url in processed_urls:
                card_index += 1
                continue
            processed_urls.add(job_url)

            print(f"\n📄 Job {card_index + 1}/{count} (page {current_page_num})")

            # Check DOM directly — no need to ask AI whether Easy Apply exists
            easy_apply_btn = page.locator(
                ".jobs-apply-button, "
                "button.jobs-apply-button--top-card, "
                "button[aria-label*='Easy Apply to'], "
                "button:has-text('Easy Apply'):not(#searchFilter_applyWithLinkedin)"
            ).first

            has_easy_apply = False
            try:
                easy_apply_btn.wait_for(state="visible", timeout=3000)
                has_easy_apply = True
            except Exception:
                pass

            if has_easy_apply:
                print("   ⚡ Easy Apply found — applying...")
                try:
                    easy_apply_btn.click()
                    time.sleep(random.uniform(2, 3))

                    success = handle_application_modal(page)
                    if success:
                        applied_count += 1
                        print(f"   ✅ Applied! Total so far: {applied_count}")

                    # Return to search results page
                    page.goto(search_url + f"&start={25 * (current_page_num - 1)}")
                    time.sleep(random.uniform(3, 5))
                    card_index += 1

                except Exception as e:
                    print(f"   ⚠️ Apply failed: {e} — skipping")
                    card_index += 1
            else:
                print("   ⏭ No Easy Apply — skipping")
                card_index += 1
        
        print(f"\n🎉 Done! Applied to {applied_count} jobs")
        print("💾 Session saved to ./linkedin_profile for next time")
        context.close()

def execute_ai_action(page, ai_response):
    """
    Parse the AI's JSON response and execute the recommended action.
    Returns a string hint: 'scrolled', 'clicked', 'SUBMIT', 'NEXT', etc.
    """
    ai_text = ai_response or ""
    try:
        parsed = json.loads(ai_text)
        action = parsed.get("action", {})
        name = action.get("name", "")

        if name == "scroll":
            delta_y = float(action.get("delta_y", 100))
            # Scroll inside the modal dialog
            dialog = page.locator("[role='dialog']").first
            dialog.evaluate(f"el => el.scrollBy(0, {int(delta_y * 5)})")
            print(f"  ↕ Scrolled modal by {int(delta_y * 5)}px")
            return "scrolled"

        elif name == "click":
            x, y = action.get("x"), action.get("y")
            if x is not None and y is not None:
                page.mouse.click(float(x), float(y))
                print(f"  🖱️ Clicked at ({x}, {y})")
                return "clicked"

        elif name == "send_msg_to_user":
            msg = action.get("msg", "")
            return msg.upper()

    except (json.JSONDecodeError, AttributeError, TypeError):
        pass

    return ai_text.upper()





def _label_for_field(page, field_locator):
    """Return the visible label text for a form field."""
    try:
        field_id = field_locator.get_attribute("id", timeout=1000)
        if field_id:
            label = page.locator(f"label[for='{field_id}']").first.inner_text(timeout=1000)
            return label.strip()
    except Exception:
        pass
    try:
        return field_locator.evaluate(
            """el => {
                let p = el.closest('div,fieldset');
                if (!p) return '';
                let lbl = p.querySelector('label,legend,span.t-bold');
                return lbl ? lbl.innerText.trim() : '';
            }""",
            timeout=1000,
        )
    except Exception:
        return ""


def _fallback_answer_for_label(label: str, field_type: str, options=None) -> str:
    """
    Keyword-based fallback answer using CANDIDATE_PROFILE data.
    Used when the AI server is unreachable or returns nothing.
    """
    l = label.lower()
    p = CANDIDATE_PROFILE

    # Years / experience
    if any(k in l for k in ("year", "experience", "exp")):
        return str(p["years_of_experience"])

    # Current CTC
    if any(k in l for k in ("current ctc", "current salary", "current compensation", "ctc")):
        # If label says "in lpa" or "lpa", return LPA figure
        if "lpa" in l or "lac" in l or "lakh" in l:
            return str(p["current_ctc_lpa"])
        return str(p["current_ctc_inr"])

    # Expected CTC
    if any(k in l for k in ("expected ctc", "expected salary", "ectc", "expected compensation")):
        if "lpa" in l or "lac" in l or "lakh" in l:
            return str(p["expected_ctc_lpa"])
        return str(p["expected_ctc_inr"])

    # Notice period
    if any(k in l for k in ("notice", "notice period")):
        return str(p["notice_period_days"])

    # Name
    if "name" in l:
        return p["name"]

    # City / location
    if any(k in l for k in ("city", "location", "current location")):
        return p["city"]

    # LinkedIn / GitHub
    if "linkedin" in l:
        return p["linkedin"]
    if "github" in l:
        return p["github"]

    # Cover letter / cover / summary / why
    if any(k in l for k in ("cover", "summary", "why", "describe", "about yourself")):
        return p["cover_letter"]

    # Night shift / shift / comfortable
    if any(k in l for k in ("shift", "night", "comfortable", "okay", "ok")):
        if options:
            for opt_str in options:
                if "yes" in opt_str.lower():
                    # return just the value= part
                    try:
                        return opt_str.split("value=")[-1].rstrip(")")
                    except Exception:
                        return opt_str
        return COMMON_ANSWERS.get("do_you_have_experience", "Yes")

    # Generic yes/no booleans
    if any(k in l for k in ("immediate", "join", "available", "sponsor", "authorized", "relocat", "willing")):
        answer = COMMON_ANSWERS.get("do_you_have_experience", "Yes")
        if options:
            for opt_str in options:
                if answer.lower() in opt_str.lower():
                    try:
                        return opt_str.split("value=")[-1].rstrip(")")
                    except Exception:
                        return opt_str
        return answer

    # Dropdown fallback: first real option
    if options:
        try:
            return options[0].split("value=")[-1].rstrip(")")
        except Exception:
            return options[0]

    # Number field fallback
    if field_type == "number":
        return str(p["years_of_experience"])

    return COMMON_ANSWERS.get("do_you_have_experience", "Yes")


def _ask_ai_for_field_value(page, label: str, field_type: str, options=None) -> str:
    """
    Ask the AI what value to put in a field given the candidate profile.
    Falls back to keyword matching if the AI server is unreachable.
    """
    screenshot = page.screenshot(type="png")
    screenshot_b64 = base64.b64encode(screenshot).decode()

    options_hint = ""
    if options:
        options_hint = f"\nAvailable options: {options}"

    prompt = (
        f"{PROFILE_CONTEXT}\n\n"
        f"You are filling a LinkedIn Easy Apply form.\n"
        f"Field label: \"{label}\"\n"
        f"Field type: {field_type}{options_hint}\n\n"
        f"Using ONLY the candidate profile above, return the exact value to enter for this field.\n"
        f"If it is a dropdown, return the exact option value from the available options list.\n"
        f"Reply with ONLY the raw value — no explanation, no JSON, no quotes."
    )

    response = get_ai_action(screenshot_b64, prompt)
    if response:
        # AI may return a JSON action object — extract the actual value from it
        value = _extract_value_from_ai_response(response)
        if value:
            return value

    # AI unavailable or returned nothing useful — use keyword-based fallback
    print(f"    ⚠️  AI fallback for '{label[:40]}'")
    return _fallback_answer_for_label(label, field_type, options)


def _extract_value_from_ai_response(response: str) -> str:
    """
    The AI sometimes returns a JSON action object like:
      {"thought": "...", "action": {"name": "send_msg_to_user", "msg": "1"}}
    Extract the actual answer value from it, or return the raw text if it's
    already a plain value.
    """
    text = response.strip()
    try:
        parsed = json.loads(text)
        # {"action": {"name": "send_msg_to_user", "msg": "<value>"}}
        action = parsed.get("action", {})
        if action.get("name") == "send_msg_to_user":
            return str(action.get("msg", "")).strip()
        # {"value": "..."} or {"answer": "..."}
        for key in ("value", "answer", "msg", "text", "result"):
            if key in parsed:
                return str(parsed[key]).strip()
        # {"action": {"value": "..."}}
        if "value" in action:
            return str(action["value"]).strip()
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    # Plain text response — use as-is
    return text.strip('"').strip("'")


def _type_into_field(field_locator, value):
    """Clear a field and type the value character by character (human-like)."""
    try:
        field_locator.click(timeout=1000)
        field_locator.select_all()
        field_locator.press("Backspace")
    except Exception:
        pass
    for char in str(value):
        field_locator.press_sequentially(char, delay=random.randint(60, 140))
        time.sleep(random.uniform(0.04, 0.15))


def fill_form_fields(page):
    """
    Scan the open modal for empty fields, ask the AI for the right value
    (passing full candidate profile as context), then type the answer.
    """
    dialog = page.locator("[role='dialog']").first
    filled = 0

    # ── Text / number inputs ────────────────────────────────────────
    inputs = dialog.locator("input[type='text'], input[type='number'], input:not([type])")
    for idx in range(inputs.count()):
        inp = inputs.nth(idx)
        try:
            if not inp.is_visible(timeout=500):
                continue
            current = inp.input_value(timeout=500).strip()
            if current:
                continue
            label = _label_for_field(page, inp)
            field_type = inp.get_attribute("type") or "text"
            value = _ask_ai_for_field_value(page, label, field_type)
            _type_into_field(inp, value)
            print(f"    ✏️  Typed into '{label[:50]}' → {value}")
            filled += 1
            time.sleep(0.3)
        except Exception:
            continue

    # ── Textareas ───────────────────────────────────────────────────
    textareas = dialog.locator("textarea")
    for idx in range(textareas.count()):
        ta = textareas.nth(idx)
        try:
            if not ta.is_visible(timeout=500):
                continue
            current = ta.input_value(timeout=500).strip()
            if current:
                continue
            label = _label_for_field(page, ta)
            value = _ask_ai_for_field_value(page, label, "textarea")
            _type_into_field(ta, value)
            print(f"    ✏️  Typed into textarea '{label[:50]}'")
            filled += 1
            time.sleep(0.3)
        except Exception:
            continue

    # ── <select> dropdowns ──────────────────────────────────────────
    selects = dialog.locator("select, select.fb-text-selectable__select, div.fb-dash-form-element select")
    for idx in range(selects.count()):
        sel = selects.nth(idx)
        try:
            if not sel.is_visible(timeout=500):
                continue
            current = sel.input_value(timeout=500)
            if current and current not in ("", "Select an option"):
                continue
            label = _label_for_field(page, sel)
            # Collect available option values for AI context
            option_values = []
            for opt in sel.locator("option").all():
                val = opt.get_attribute("value") or ""
                txt = opt.inner_text().strip()
                if val and txt.lower() not in ("select an option", "please select", ""):
                    option_values.append(f"{txt} (value={val})")
            chosen_text = _ask_ai_for_field_value(page, label, "dropdown", options=option_values)
            # Match AI text back to an option value
            chosen_val = None
            for opt in sel.locator("option").all():
                val = opt.get_attribute("value") or ""
                txt = opt.inner_text().strip()
                if chosen_text and (chosen_text.lower() in txt.lower() or chosen_text == val):
                    chosen_val = val
                    break
            # If still no match, pick the first real option
            if not chosen_val:
                for opt in sel.locator("option").all():
                    val = opt.get_attribute("value") or ""
                    txt = opt.inner_text().strip()
                    if val and txt.lower() not in ("select an option", "please select", ""):
                        chosen_val = val
                        break
            if chosen_val:
                sel.select_option(value=chosen_val)
                print(f"    ✏️  Selected '{label[:50]}' → {chosen_val}")
                filled += 1
                time.sleep(0.3)
        except Exception:
            continue

    if filled:
        print(f"    → Filled {filled} field(s) via AI")
        time.sleep(0.5)
    return filled


def handle_application_modal(page):
    """Handle the Easy Apply form steps"""
    max_steps = 10

    for step in range(max_steps):
        print(f"  Step {step+1}/{max_steps}...")
        time.sleep(random.uniform(1.0, 1.5))

        # Check if modal is still open
        try:
            page.wait_for_selector("[role='dialog']", timeout=4000)
        except Exception:
            print("  Modal closed — application may be submitted")
            return True

        # ── FILL any empty required fields first ────────────────────
        fill_form_fields(page)

        # ── Scroll modal to bottom so navigation buttons are visible ─
        try:
            page.locator("[role='dialog']").first.evaluate(
                "el => el.scrollTo(0, el.scrollHeight)"
            )
            time.sleep(0.4)
        except Exception:
            pass

        # ── Determine which button to click via DOM (fast, reliable) ─
        dialog = page.locator("[role='dialog']")

        if dialog.locator("button:has-text('Submit application')").count() > 0:
            if try_submit(page):
                return True
        elif dialog.locator("button:has-text('Review')").count() > 0:
            try:
                dialog.locator("button:has-text('Review')").first.click(timeout=5000)
                print("  Clicked Review")
                time.sleep(1.5)
            except Exception:
                pass
        elif dialog.locator(
            "button:has-text('Next'), button:has-text('Continue')"
        ).count() > 0:
            try_click_next(page)
        else:
            # Fallback: ask AI
            screenshot = page.screenshot(type="png")
            screenshot_b64 = base64.b64encode(screenshot).decode()
            prompt = (
                f"{PROFILE_CONTEXT}\n\n"
                "LinkedIn Easy Apply modal. What button is at the bottom? "
                "Reply with exactly one word: SUBMIT, REVIEW, NEXT, or DONE."
            )
            ai_response = get_ai_action(screenshot_b64, prompt)
            print(f"  🤖 AI (fallback): {ai_response}")
            hint = execute_ai_action(page, ai_response)
            if "SUBMIT" in hint:
                if try_submit(page):
                    return True
            elif "DONE" in hint:
                return True
            else:
                try_click_next(page)

    return False


def try_submit(page):
    """Try to click the submit application button"""
    submit_selectors = [
        "[role='dialog'] button:has-text('Submit application')",
        "button[aria-label*='Submit']",
        "button:has-text('Submit application')",
    ]
    for sel in submit_selectors:
        try:
            page.locator(sel).first.click(timeout=4000)
            print("  ✅ Application submitted!")
            time.sleep(2)
            return True
        except Exception:
            continue
    print("  ⚠️ Could not find Submit button")
    return False

def try_click_next(page):
    """Try to click the Next / Continue / Review navigation button inside the modal"""
    # All known selectors for the forward button in LinkedIn Easy Apply
    selectors = [
        "[role='dialog'] button:has-text('Next')",
        "[role='dialog'] button:has-text('Continue to next step')",
        "[role='dialog'] button:has-text('Continue')",
        "[role='dialog'] button:has-text('Review')",
        "[role='dialog'] button[aria-label*='next step']",
        "[role='dialog'] button[aria-label*='Continue']",
        "button:has-text('Next')",
        "button:has-text('Continue')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            btn.scroll_into_view_if_needed(timeout=2000)
            btn.click(timeout=3000)
            label = sel.split(":has-text(")[-1].strip(")'\"")
            print(f"  Clicked: {label}")
            return
        except Exception:
            continue
    print("  ⚠️ No navigation button found — form may need manual input")

if __name__ == "__main__":
    # Check endpoint health
    try:
        r = requests.get(f"{MODEL_ENDPOINT}/health", timeout=5)
        print(f"✅ Model server connected: {r.json()}")
    except Exception as e:
        print(f"⚠️ Warning: Cannot reach model server: {e}")
        print("Continuing anyway...")
    
    run_linkedin_automation()