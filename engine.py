import asyncio
from playwright.async_api import async_playwright
import os
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class ClientInfo:
    first_name: str
    last_name: str
    dob: str          # MM/DD/YYYY
    gender: str       # Male/Female
    address: str
    city: str
    state: str
    zip_code: str
    license_number: str
    date_licensed: str  # MMDDYYYY format e.g. 06202020
    vin: str

@dataclass
class QuoteResult:
    carrier: str
    rate: Optional[str]
    bill_plan: Optional[str]
    error: Optional[str]
    screenshot_path: Optional[str]


async def quote_good2go(client: ClientInfo, credentials: dict) -> QuoteResult:
    """Automate Good2Go quote flow"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Login
            await page.goto("https://isi.good2go.com/is/root/logon/index.cfm")
            await page.fill('input[name="username"], input[type="text"]', credentials["good2go_user"])
            await page.fill('input[name="password"], input[type="password"]', credentials["good2go_pass"])
            await page.click('input[type="submit"], button[type="submit"]')
            await page.wait_for_load_state("networkidle")

            # Start new quote
            await page.click('text=Start a New Quote, a:has-text("Start"), button:has-text("New Quote")')
            await page.wait_for_load_state("networkidle")

            # Enter ZIP code
            await page.fill('input[name*="zip"], input[placeholder*="ZIP"], input[placeholder*="Zip"]', client.zip_code)
            await page.click('button:has-text("Quote"), input[value="Quote"]')
            await page.wait_for_load_state("networkidle")

            # Personal info page
            await page.fill('input[name*="first"], input[placeholder*="First"]', client.first_name)
            await page.fill('input[name*="last"], input[placeholder*="Last"]', client.last_name)
            await page.fill('input[name*="address"], input[placeholder*="Address"]', client.address)
            await page.fill('input[name*="dob"], input[name*="birth"], input[placeholder*="Date of Birth"]', client.dob)
            
            # Gender dropdown
            gender_select = page.locator('select[name*="sex"], select[name*="gender"]')
            await gender_select.select_option(label=client.gender)
            
            # License number
            await page.fill('input[name*="license"], input[placeholder*="License"]', client.license_number)

            # Vehicle section - Look Up VIN
            await page.click('button:has-text("Look Up"), a:has-text("Look Up")')
            await page.wait_for_selector('input[name*="vin"], input[placeholder*="VIN"]')
            await page.fill('input[name*="vin"], input[placeholder*="VIN"]', client.vin)
            await page.keyboard.press("Enter")
            await page.wait_for_load_state("networkidle")

            # Click Rate
            await page.click('button:has-text("Rate"), input[value="Rate"]')
            await page.wait_for_load_state("networkidle")

            # Extended application
            # Paperless -> No
            paperless = page.locator('select[name*="paperless"], input[name*="paperless"][value="N"]')
            if await paperless.count() > 0:
                if await paperless.evaluate("el => el.tagName") == "SELECT":
                    await paperless.select_option(label="No")
                else:
                    await paperless.check()

            # Delivery method -> Paper
            delivery = page.locator('select[name*="delivery"]')
            if await delivery.count() > 0:
                await delivery.select_option(label="Paper")

            # Vehicle purchased in last 90 days -> No
            purchased = page.locator('select[name*="purchased"], select[name*="90day"]')
            if await purchased.count() > 0:
                await purchased.select_option(label="No")

            # Driver 1 tab
            driver_tab = page.locator('a:has-text("Driver 1"), button:has-text("Driver 1")')
            if await driver_tab.count() > 0:
                await driver_tab.click()

            await page.fill('input[name*="license"], input[placeholder*="License"]', client.license_number)
            
            # Date licensed
            date_lic_field = page.locator('input[name*="date_licensed"], input[name*="datelicensed"]')
            if await date_lic_field.count() > 0:
                await date_lic_field.fill(client.date_licensed)

            # Continue
            await page.click('button:has-text("Continue"), input[value="Continue"]')
            await page.wait_for_load_state("networkidle")

            # Final Rate button
            await page.click('button:has-text("Rate"), input[value="Rate"]')
            await page.wait_for_load_state("networkidle")

            # Screenshot and scrape rate
            screenshot_path = f"/tmp/good2go_{client.last_name}_{client.first_name}.png"
            await page.screenshot(path=screenshot_path, full_page=False)

            # Try to scrape the rate from the right side
            rate_text = None
            rate_selectors = [
                '.rate-amount', '.premium', '[class*="rate"]', '[class*="premium"]',
                'td:has-text("$")', 'span:has-text("$")', 'div:has-text("Total Premium")'
            ]
            for sel in rate_selectors:
                elements = page.locator(sel)
                if await elements.count() > 0:
                    rate_text = await elements.first.inner_text()
                    break

            await browser.close()
            return QuoteResult(
                carrier="Good2Go",
                rate=rate_text,
                bill_plan=None,
                error=None,
                screenshot_path=screenshot_path
            )

        except Exception as e:
            screenshot_path = f"/tmp/good2go_error_{client.last_name}.png"
            try:
                await page.screenshot(path=screenshot_path)
            except:
                screenshot_path = None
            await browser.close()
            logger.error(f"Good2Go error: {e}")
            return QuoteResult(carrier="Good2Go", rate=None, bill_plan=None, error=str(e), screenshot_path=screenshot_path)


async def quote_natgen(client: ClientInfo, credentials: dict) -> QuoteResult:
    """Automate NatGen quote flow"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Login
            await page.goto("https://natgenagency.com/Login.aspx?Menu=Login")
            await page.fill('input[name*="user"], input[id*="user"]', credentials["natgen_user"])
            await page.click('button:has-text("SIGN IN"), input[value*="Sign"]')
            await page.wait_for_load_state("networkidle")
            await page.fill('input[name*="pass"], input[type="password"]', credentials["natgen_pass"])
            await page.click('button:has-text("SIGN IN"), input[value*="Sign"]')
            await page.wait_for_load_state("networkidle")

            # New Quote -> Begin
            await page.click('a:has-text("New Quote"), button:has-text("New Quote")')
            await page.wait_for_load_state("networkidle")
            await page.click('button:has-text("Begin"), a:has-text("Begin")')
            await page.wait_for_load_state("networkidle")

            # Input by -> Robert Perez
            input_by = page.locator('select[name*="input"], select[id*="input"]')
            if await input_by.count() > 0:
                await input_by.select_option(label="Robert Perez")

            # Named insured info
            await page.fill('input[name*="last"], input[id*="last"]', client.last_name)
            await page.fill('input[name*="dob"], input[id*="dob"], input[placeholder*="birth"]', client.dob)
            await page.fill('input[name*="address"], input[id*="address"]', client.address)
            await page.click('button:has-text("Continue"), input[value="Continue"]')
            await page.wait_for_load_state("networkidle")

            # Pre-fills - click through
            continue_btn = page.locator('button:has-text("Continue"), input[value="Continue"]')
            if await continue_btn.count() > 0:
                await continue_btn.click()
                await page.wait_for_load_state("networkidle")

            # Driver tab -> View/Edit
            await page.click('a:has-text("Drivers"), button:has-text("Drivers")')
            await page.wait_for_load_state("networkidle")
            await page.click('a:has-text("View/Edit"), button:has-text("View/Edit")')
            await page.wait_for_load_state("networkidle")

            # Years of experience -> 3
            yoe = page.locator('select[name*="experience"], input[name*="experience"]')
            if await yoe.count() > 0:
                if await yoe.evaluate("el => el.tagName") == "SELECT":
                    await yoe.select_option(label="3")
                else:
                    await yoe.fill("3")

            # Driver status -> Rated Driver
            status = page.locator('select[name*="status"], select[id*="status"]')
            if await status.count() > 0:
                await status.select_option(label="Rated Driver")

            # License number
            await page.fill('input[name*="license"], input[id*="license"]', client.license_number)
            await page.click('button:has-text("Save"), input[value="Save"]')
            await page.wait_for_load_state("networkidle")

            # Click through driver history
            await page.click('button:has-text("Continue"), input[value="Continue"]')
            await page.wait_for_load_state("networkidle")

            # Vehicles tab
            await page.click('a:has-text("Vehicles"), button:has-text("Vehicles")')
            await page.wait_for_load_state("networkidle")
            await page.click('button:has-text("Add Vehicle"), a:has-text("Add Vehicle")')
            await page.wait_for_load_state("networkidle")

            # VIN lookup
            await page.fill('input[name*="vin"], input[id*="vin"]', client.vin)
            await page.click('.magnifying-glass, button[aria-label*="search"], button:has-text("🔍"), img[alt*="search"]')
            await page.wait_for_load_state("networkidle")

            # Primary use -> Pleasure Commute
            primary_use = page.locator('select[name*="use"], select[id*="use"]')
            if await primary_use.count() > 0:
                await primary_use.select_option(label="Pleasure Commute")

            # Ownership -> Owned
            ownership = page.locator('select[name*="ownership"], select[id*="ownership"]')
            if await ownership.count() > 0:
                await ownership.select_option(label="Owned")

            await page.click('button:has-text("Save"), input[value="Save"]')
            await page.wait_for_load_state("networkidle")
            await page.click('button:has-text("Continue"), input[value="Continue"]')
            await page.wait_for_load_state("networkidle")

            # Additional information - No to all dropdowns
            dropdowns = page.locator('select')
            count = await dropdowns.count()
            for i in range(count):
                try:
                    dropdown = dropdowns.nth(i)
                    options = await dropdown.locator('option').all_text_contents()
                    no_options = [o for o in options if o.lower() in ['no', 'n', 'none']]
                    if no_options:
                        await dropdown.select_option(label=no_options[0])
                except:
                    pass

            await page.click('button:has-text("Continue"), input[value="Continue"]')
            await page.wait_for_load_state("networkidle")

            # Payment and policy settings
            pay_method = page.locator('select[name*="pay"], select[id*="pay"]')
            if await pay_method.count() > 0:
                await pay_method.select_option(label="Auto Pay Credit Card")

            pay_plan = page.locator('select[name*="plan"], select[id*="plan"]')
            if await pay_plan.count() > 0:
                await pay_plan.select_option(label="5 Payments 20% Down")

            policy_type = page.locator('select[name*="policy"], select[id*="policy_type"]')
            if await policy_type.count() > 0:
                await policy_type.select_option(label="Basic")

            # PIP settings
            pip_limit = page.locator('select[name*="pip_limit"], select[id*="pip"]')
            if await pip_limit.count() > 0:
                await pip_limit.select_option(label="15,000")

            pip_ded = page.locator('select[name*="pip_ded"], select[name*="pip_deductible"]')
            if await pip_ded.count() > 0:
                await pip_ded.select_option(label="2,500")

            # Rate and Continue
            await page.click('button:has-text("Rate"), input[value="Rate"]')
            await page.wait_for_load_state("networkidle")
            await page.click('button:has-text("Continue"), input[value="Continue"]')
            await page.wait_for_load_state("networkidle")

            # Screenshot bill plan
            screenshot_path = f"/tmp/natgen_{client.last_name}_{client.first_name}.png"
            await page.screenshot(path=screenshot_path, full_page=False)

            # Scrape rate
            rate_text = None
            rate_selectors = ['.rate', '.premium', '[class*="rate"]', 'td:has-text("$")', 'span:has-text("$")']
            for sel in rate_selectors:
                elements = page.locator(sel)
                if await elements.count() > 0:
                    rate_text = await elements.first.inner_text()
                    break

            await browser.close()
            return QuoteResult(
                carrier="NatGen",
                rate=rate_text,
                bill_plan=None,
                error=None,
                screenshot_path=screenshot_path
            )

        except Exception as e:
            screenshot_path = f"/tmp/natgen_error_{client.last_name}.png"
            try:
                await page.screenshot(path=screenshot_path)
            except:
                screenshot_path = None
            await browser.close()
            logger.error(f"NatGen error: {e}")
            return QuoteResult(carrier="NatGen", rate=None, bill_plan=None, error=str(e), screenshot_path=screenshot_path)


async def quote_bristol_west(client: ClientInfo, credentials: dict) -> QuoteResult:
    """Automate Bristol West quote flow"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Login
            await page.goto("https://www.iaproducers.com/Producers/FMLogIn.aspx")
            await page.fill('input[name*="user"], input[id*="user"]', credentials["bw_user"])
            await page.fill('input[type="password"]', credentials["bw_pass"])
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle")

            # Quoting -> New Business -> New Customer -> New Basic Quote
            await page.click('a:has-text("Quoting"), button:has-text("Quoting")')
            await page.wait_for_load_state("networkidle")
            await page.click('a:has-text("New Business"), button:has-text("New Business")')
            await page.wait_for_load_state("networkidle")
            await page.click('a:has-text("New Customer"), button:has-text("New Customer")')
            await page.wait_for_load_state("networkidle")
            await page.click('a:has-text("New Basic Quote"), button:has-text("New Basic Quote")')
            await page.wait_for_load_state("networkidle")

            # Client info
            await page.fill('input[name*="first"], input[id*="first"]', client.first_name)
            await page.fill('input[name*="last"], input[id*="last"]', client.last_name)
            await page.fill('input[name*="dob"], input[name*="birth"]', client.dob)

            gender_sel = page.locator('select[name*="gender"], select[name*="sex"]')
            if await gender_sel.count() > 0:
                await gender_sel.select_option(label=client.gender)

            await page.fill('input[name*="address"], input[id*="address"]', client.address)
            await page.click('button:has-text("Continue"), input[value="Continue"]')
            await page.wait_for_load_state("networkidle")

            # Click through Drivers -> Violations -> Vehicle Coverages
            for section in ["Drivers", "Violations", "Vehicle Coverages"]:
                btn = page.locator(f'a:has-text("{section}"), button:has-text("{section}")')
                if await btn.count() > 0:
                    await btn.click()
                    await page.wait_for_load_state("networkidle")

            # VIN
            await page.fill('input[name*="vin"], input[id*="vin"]', client.vin)
            await page.wait_for_load_state("networkidle")

            # Coverage selections
            # Bodily injury -> None
            bi = page.locator('select[name*="bodily"], select[id*="bi"]')
            if await bi.count() > 0:
                await bi.select_option(label="None")

            # Property damage -> 5000
            pd = page.locator('select[name*="property"], select[id*="pd"]')
            if await pd.count() > 0:
                await pd.select_option(label="5,000")

            # PIP limit -> 15,000
            pip = page.locator('select[name*="pip_limit"], select[id*="pip"]')
            if await pip.count() > 0:
                await pip.select_option(label="15,000")

            # PIP deductible -> 2,500
            pip_ded = page.locator('select[name*="pip_ded"]')
            if await pip_ded.count() > 0:
                await pip_ded.select_option(label="2,500")

            # No prior insurance
            no_prior = page.locator('input[name*="prior"][value*="N"], input[id*="no_prior"]')
            if await no_prior.count() > 0:
                await no_prior.check()

            # Solak paperless discount -> Yes
            paperless = page.locator('select[name*="paperless"], select[id*="paperless"]')
            if await paperless.count() > 0:
                await paperless.select_option(label="Yes")

            # E-signature -> Yes
            esig = page.locator('select[name*="esign"], select[id*="esig"]')
            if await esig.count() > 0:
                await esig.select_option(label="Yes")

            # EFT -> Yes
            eft = page.locator('select[name*="eft"]')
            if await eft.count() > 0:
                await eft.select_option(label="Yes")

            # Down payment -> Credit Card
            down = page.locator('select[name*="down"], select[name*="payment_method"]')
            if await down.count() > 0:
                await down.select_option(label="Credit Card")

            # Get rate
            await page.click('button:has-text("Rate"), input[value="Rate"]')
            await page.wait_for_load_state("networkidle")

            screenshot_path = f"/tmp/bw_{client.last_name}_{client.first_name}.png"
            await page.screenshot(path=screenshot_path, full_page=False)

            rate_text = None
            rate_selectors = ['.rate', '.premium', '[class*="rate"]', 'td:has-text("$")', 'span:has-text("$")']
            for sel in rate_selectors:
                elements = page.locator(sel)
                if await elements.count() > 0:
                    rate_text = await elements.first.inner_text()
                    break

            await browser.close()
            return QuoteResult(
                carrier="Bristol West",
                rate=rate_text,
                bill_plan=None,
                error=None,
                screenshot_path=screenshot_path
            )

        except Exception as e:
            screenshot_path = f"/tmp/bw_error_{client.last_name}.png"
            try:
                await page.screenshot(path=screenshot_path)
            except:
                screenshot_path = None
            await browser.close()
            logger.error(f"Bristol West error: {e}")
            return QuoteResult(carrier="Bristol West", rate=None, bill_plan=None, error=str(e), screenshot_path=screenshot_path)


async def run_all_quotes(client: ClientInfo, credentials: dict) -> list[QuoteResult]:
    """Run all 3 carriers in parallel"""
    results = await asyncio.gather(
        quote_good2go(client, credentials),
        quote_natgen(client, credentials),
        quote_bristol_west(client, credentials),
        return_exceptions=True
    )
    
    final = []
    for r in results:
        if isinstance(r, Exception):
            final.append(QuoteResult(carrier="Unknown", rate=None, bill_plan=None, error=str(r), screenshot_path=None))
        else:
            final.append(r)
    
    return final
