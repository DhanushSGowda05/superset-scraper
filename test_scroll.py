from playwright.sync_api import sync_playwright


with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir="./browser_data",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto(
        "https://app.joinsuperset.com/students/jobprofiles"
    )

    page.wait_for_timeout(5000)

    cards = page.locator(
        'div.cursor-pointer:has(div.p-4)'
    )

    total = cards.count()

    print("Total jobs:", total)

    print("\n==============================")
    print("FIRST 5 JOBS")
    print("==============================")

    for i in range(min(5, total)):
        print(f"\nJOB {i + 1}")
        print(cards.nth(i).inner_text())

    print("\n==============================")
    print("LAST 5 JOBS")
    print("==============================")

    start = max(0, total - 5)

    for i in range(start, total):
        print(f"\nJOB {i + 1}")
        print(cards.nth(i).inner_text())

    input("\nPress ENTER to close...")

    context.close()