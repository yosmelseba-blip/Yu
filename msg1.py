import argparse
import os
import time
from playwright.sync_api import sync_playwright

def main():
    parser = argparse.ArgumentParser(description="Instagram DM Auto Sender using Playwright")
    parser.add_argument('--username', required=False, help='Instagram username')
    parser.add_argument('--password', required=False, help='Instagram password')
    parser.add_argument('--thread-url', required=True, help='Full Instagram direct thread URL')
    parser.add_argument('--names', required=True, help='Comma-separated messages list (e.g., "Example 1, Example 2")')
    parser.add_argument('--headless', default='true', help='true/false (optional, default true)')
    parser.add_argument('--storage-state', required=True, help='Path to JSON file to save/load login state')

    args = parser.parse_args()

    # Parse headless as boolean
    headless = args.headless.lower() == 'true'

    # Parse messages
    messages = [msg.strip() for msg in args.names.split(',') if msg.strip()]

    if not messages:
        print("No messages provided.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        storage_path = args.storage_state

        # Load storage state if exists
        if os.path.exists(storage_path):
            context = browser.new_context(storage_state=storage_path)
            print("Loaded storage state, skipping login.")
        else:
            context = browser.new_context()
            if not args.username or not args.password:
                print("Username and password required for login.")
                browser.close()
                return

        page = context.new_page()

        try:
            if not os.path.exists(storage_path):
                # Login
                print("Logging in...")
                page.goto("https://www.instagram.com/", timeout=60000)
                page.wait_for_selector('input[name="username"]', timeout=30000)
                page.fill('input[name="username"]', args.username)
                page.fill('input[name="password"]', args.password)
                page.click('button[type="submit"]')
                # Wait for navigation after login (may need adjustment based on 2FA or saves)
                page.wait_for_url("https://www.instagram.com/", timeout=60000)
                print("Login successful, saving storage state.")
                context.storage_state(path=storage_path)

            # Open thread URL
            print("Opening thread URL...")
            page.goto(args.thread_url, timeout=60000)
            # Wait for DM input to appear (using stable selector)
            page.wait_for_selector('div[role="textbox"][aria-label="Message"]', timeout=30000)
            dm_selector = 'div[role="textbox"][aria-label="Message"]'

            print("Starting infinite message loop. Press Ctrl+C to stop.")
            while True:
                for msg in messages:
                    try:
                        # Directly set message and send
                        page.click(dm_selector)
                        page.fill(dm_selector, msg)  # Directly set the message instead of typing
                        page.press(dm_selector, 'Enter')
                        print(f"Sending: {msg}")
                        time.sleep(0.8)  # Delay to avoid rate limiting/spam detection
                    except Exception as e:
                        print(f"Error sending message '{msg}': {e}")
                        time.sleep(5)  # Wait longer on error

        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()