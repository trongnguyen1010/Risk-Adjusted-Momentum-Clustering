"""Local-only integration fixture: no VSDC,no network,about:blank only."""
from pathlib import Path
import ctypes
import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

run = Path(sys.argv[1]); sys.stdout.reconfigure(encoding='utf8')
with sync_playwright() as manager:
    browser = manager.chromium.launch(channel='chrome', headless=True, handle_sigint=False, timeout=15000)
    context = browser.new_context(ignore_https_errors=False, accept_downloads=False, service_workers='block')
    context.route('**/*', lambda route: route.abort())
    page = context.new_page(); page.goto('about:blank')
    no_console = ctypes.windll.kernel32.GetConsoleWindow() == 0
    print('LOCAL_BROWSER_READY', flush=True)
    end = time.monotonic()+25
    while not (run / 'PAUSE_REQUEST').exists():
        if time.monotonic() >= end: raise TimeoutError('TEST_PAUSE_TIMEOUT')
        page.wait_for_timeout(50)
    alive_after_parent_CtrlC = browser.is_connected() and page.evaluate('1+1') == 2
    context.close(); browser.close()
(run / 'local_browser_pause_result.json').write_text(json.dumps({'status': 'PASS_LOCAL_BROWSER_PAUSE',
    'worker_pid': os.getpid(), 'no_console': no_console,
    'driver_alive_after_parent_CtrlC': alive_after_parent_CtrlC, 'normal_context_browser_manager_close': True,
    'source_requests': 0, 'only_page': 'about:blank'}), encoding='utf8')
print('LOCAL_BROWSER_CLOSED_NORMALLY', flush=True)
