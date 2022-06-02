import json
import signal
import socket
from pathlib import Path
from subprocess import PIPE, Popen, run
from tempfile import NamedTemporaryFile
from time import sleep
from typing import List
from contextlib import contextmanager


import srsly
from playwright.sync_api import sync_playwright


def get_open_port() -> int:
    sock = socket.socket()
    sock.bind(("", 0))
    return sock.getsockname()[1]


EXAMPLE_DATA = [
    {
        "text": "This is an example document",
    }
]
NEW_COLOR = "#FF5F1F"

temp_jsonl = NamedTemporaryFile(suffix=".jsonl")
srsly.write_jsonl(temp_jsonl.name, EXAMPLE_DATA)

temp_jsonl_patterns = NamedTemporaryFile(suffix=".jsonl")
PATTERN = {"label": "LABEL!", "pattern": [{"lower": "document"}]}
srsly.write_jsonl(temp_jsonl_patterns.name, [PATTERN])
color_attributes = [
    "accept",
    "reject",
    "ignore",
    "undo",
    "colorButton",
    "bgCard",
    "bgCardSecondary",
    "bgCardTertiary",
    "bgCardQuaternary",
    "bgPage",
    "bgSidebar",
    "bgSidebarDark",
    "bgHighlight",
    "bgLowlight",
    "bgCardTitle",
    "bgProgress",
    "bgButton",
    "bgMeta",
    "colorText",
    "colorMeta",
    "colorMessage",
    "colorSidebar",
    "colorSidebarHeadline",
    "colorSidebarLabel",
    "colorHighlightLabel",
    "colorCardTitle",
]

Path("readme.md").write_text(
    "# Prodigy Custom Theme Screencaps\n\nSee: https://prodi.gy/docs/api-web-app#themes for options"
)


@contextmanager
def run_prodigy(args: List[str]):
    prodigy_bin = run(["which", "prodigy"], capture_output=True).stdout.decode().strip()
    prodigy_server = Popen(
        [
            prodigy_bin,
        ]
        + args,
        shell=False,
    )
    sleep(3)
    yield prodigy_server
    # for some reason this just doesn't clean up
    # when just SIGINT or SIGTERM is sent.
    prodigy_server.terminate()
    prodigy_server.wait(10)
    sleep(3)


for i, attribute in enumerate(color_attributes, 1):
    port = get_open_port()
    Path("prodigy.json").write_text(
        json.dumps({"custom_theme": {attribute: NEW_COLOR}, "port": port})
    )
    with run_prodigy(
        [
            "ner.manual",
            "temp1234",
            "blank:en",
            temp_jsonl.name,
            "--label",
            "LABEL1,LABEL2",
            "--patterns",
            temp_jsonl_patterns.name,
        ]
    ):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"http://localhost:{port}")
            page.screenshot(path=f"screenshots/{i:02}_{attribute}.png")
            browser.close()

    with open("readme.md", "a") as f:
        f.write(
            f"## `{attribute}` \n\n![{attribute}](screenshots/{i:02}_{attribute}.png)\n\n"
        )


temp_jsonl.close()
temp_jsonl_patterns.close()
run("rm -f prodigy.json", shell=True)

# This is aggressive, but it doesn't respond to SIGINT / SIGTERM :(
run("pkill -f 'prodigy'", shell=True)
