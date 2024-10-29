from colorama import Fore, Back, Style, init
import os 
from playwright.sync_api import sync_playwright

init()


terminal_width = os.get_terminal_size().columns
def printer(text, color="WHITE", bg="BLACK"):
    lines = text.splitlines()

    for line in lines:
        padded_line = line.ljust(terminal_width)
        print(f"{getattr(Fore, color)}{getattr(Back, bg)}{padded_line}{Style.RESET_ALL}")

    if text.endswith('\n'):
        print(f"{getattr(Fore, color)}{getattr(Back, bg)}"+'' * terminal_width + Style.RESET_ALL)

def cprint(text, role="system"):
    if role == "user":
        printer(text, color="CYAN", bg="BLACK")
    elif role == "assistant":
        printer(text, color="WHITE", bg="BLUE")
    elif role == "context":
        printer(text, color="BLACK", bg="WHITE")
    elif role == "input":
        printer(text, color="CYAN", bg="BLACK")
    elif role == "error":
        printer(text, color="RED", bg="BLACK")
    elif role == "info":
        printer(text, color="CYAN", bg="BLACK")
    elif role == "success":
        printer(text, color="GREEN", bg="BLACK")
    else:
        printer(text, color="CYAN", bg="BLACK")
    


def take_screenshot(url: str, output_path: str):
    try:
        with sync_playwright() as p:
            # Launch a browser (e.g., Chromium)
            browser = p.chromium.launch()
            # Open a new browser context and page
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to the specified URL
            page.goto(url)
            
            # Take a screenshot and save it to the specified path
            page.screenshot(path=output_path)
            
            # Close the browser
            browser.close()
    except:
        # if the app is not running, return an empty image
        with open(output_path, 'wb') as f:
            f.write(b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjPHtg6AAAAABJRU5ErkJggg==')

# Example usage
# take_screenshot('https://www.youtube.com/', 'example_screenshot.png')

# cprint("========user============\n user are ready .... \n hello", "user")
# cprint("========user============\n assistant are ready .... \n hello", "assistant")
# cprint("========user============\n context are ready .... \n hello", "context")
# cprint("========user============\n input are ready .... \n hello", "input")
# cprint("========user============\n error are ready .... \n hello", "error")
# cprint("========user============\n success are ready .... \n hello", "success")
# cprint("========user============\n default are ready .... \n hello", "s")


# import sounddevice as sd

# # List all available devices
# devices = sd.query_devices()

# # Display the devices
# for idx, device in enumerate(devices):
#     print(f"{idx}: {device['name']} - {device['hostapi']}")

# # Alternatively, you can print all devices at once
# print(devices)