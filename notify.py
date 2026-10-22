"""Gửi thông báo lên Windows và lên điện thoại qua ntfy."""
import base64
import logging
import subprocess
import sys
from xml.sax.saxutils import escape

import requests

log = logging.getLogger("utehy-watch")

# Mượn ID ứng dụng của Windows PowerShell để Windows chịu hiện thông báo mà không cần cài gì thêm.
POWERSHELL_APP_ID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"

TOAST_SCRIPT = """
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('{xml}')
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{app_id}').Show($toast)
"""


def windows(title, body, url):
    xml = (
        f'<toast activationType="protocol" launch="{escape(url, {chr(34): "&quot;"})}">'
        f'<visual><binding template="ToastGeneric"><text>{escape(title)}</text><text>{escape(body)}</text>'
        f"</binding></visual></toast>"
    )
    script = TOAST_SCRIPT.replace("{xml}", xml.replace("'", "''")).replace("{app_id}", POWERSHELL_APP_ID)
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True, timeout=30, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0:
        log.warning("Không hiện được thông báo Windows: %s", result.stderr.decode(errors="ignore")[:300])


def phone(topic, title, body, url):
    if not topic:
        return
    try:
        response = requests.post(
            "https://ntfy.sh/",
            json={"topic": topic, "title": title, "message": body, "click": url, "tags": ["mortar_board"]},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        log.warning("Không gửi được lên điện thoại (ntfy): %s", error)


def send(topic, title, public_body, detail_body, url):
    """Máy tính nhận bản chi tiết, điện thoại nhận bản không có số điểm."""
    if sys.platform == "win32":  # trên máy chủ GitHub (Linux) chỉ gửi lên điện thoại
        windows(title, detail_body, url)
    phone(topic, title, public_body, url)
