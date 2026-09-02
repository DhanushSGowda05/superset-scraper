from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir="./browser_data",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://app.joinsuperset.com/students/jobprofiles")

    page.wait_for_timeout(30000)

    context.close()