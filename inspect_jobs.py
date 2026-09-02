from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir="./browser_data",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://app.joinsuperset.com/students/jobprofiles")

    page.wait_for_timeout(5000)

    cards = page.locator('div.cursor-pointer:has(div.p-4)')

    print("Number of job cards:", cards.count())

    # First job
    card = cards.nth(1)

    print("\nBefore clicking:")
    print(page.url)

    print("\nClicking:")
    print(card.inner_text())

    card.click()

    page.wait_for_timeout(3000)

    print("\nAfter clicking:")
    print(page.url)

    input("\nPress ENTER to close...")

    context.close()