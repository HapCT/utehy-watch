"""Kiểm tra cổng thông tin UTEHY và báo khi có điểm mới, lịch thi mới hoặc lịch học thay đổi.

Chạy:  python watch.py               kiểm tra một lần
       python watch.py --test-notify  gửi thử một thông báo lên máy tính và điện thoại
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

import notify
import portal
from changes import find_changes, merge_state

HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "state.json"
PORTAL_URL = f"{portal.BASE}/SinhVien"
MAX_LINES = 8

log = logging.getLogger("utehy-watch")


def say(text):
    """In ra màn hình nếu có (khi chạy ngầm bằng pythonw thì không có)."""
    if sys.stdout:
        print(text)
    log.info(text)


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATE_FILE)


def announce(topic, events):
    """Gộp mọi thay đổi của lần kiểm tra này vào một thông báo."""
    title = "Cổng trường có cập nhật" if len(events) > 1 else "Cổng trường: " + events[0]["public"].split(":")[0]

    def body(field):
        lines = [e[field] for e in events[:MAX_LINES]]
        if len(events) > MAX_LINES:
            lines.append(f"… và {len(events) - MAX_LINES} thay đổi khác")
        return "\n".join(lines)

    notify.send(topic, title, body("public"), body("detail"), PORTAL_URL)


def check(user, password, topic):
    state = load_state()
    try:
        snapshot = portal.fetch_all(user, password)
    except portal.LoginError as error:
        say(f"Không đăng nhập được: {error}")
        if not state.get("login_failed"):  # chỉ báo một lần, không báo mỗi 2 tiếng
            notify.send(topic, "UTEHY Watch không đăng nhập được",
                        "Kiểm tra lại mã sinh viên và mật khẩu trong file .env.",
                        "Kiểm tra lại mã sinh viên và mật khẩu trong file .env.", PORTAL_URL)
            save_state({**state, "login_failed": True})
        return 1
    except requests.RequestException as error:
        say(f"Không vào được trang trường (có thể mất mạng hoặc trang đang lỗi): {error}")
        return 1

    week_text = ", ".join(f"{week}: {len(s)} buổi" for week, s in snapshot["weeks"].items()) or "chưa thấy lịch tuần"
    say(f"Đọc được {len(snapshot['grades'])} học phần trong bảng điểm, "
        f"{len(snapshot['exams'])} lịch thi, {week_text}.")

    if "grades" not in state:
        say("Lần chạy đầu tiên: đã ghi nhớ hiện trạng. Từ giờ chỉ báo khi có gì thay đổi.")
        notify.send(topic, "UTEHY Watch đã bắt đầu theo dõi",
                    "Bạn sẽ được báo khi có điểm mới, lịch thi mới hoặc lịch học thay đổi.",
                    f"Đang theo dõi {len(snapshot['grades'])} học phần và {len(snapshot['exams'])} lịch thi.",
                    PORTAL_URL)
    else:
        events = find_changes(state, snapshot)
        if events:
            for event in events:
                say(event["detail"])
            announce(topic, events)
        else:
            say("Không có gì thay đổi.")

    save_state({**merge_state(state, snapshot), "login_failed": False})
    return 0


def main():
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        filename=HERE / "watch.log", encoding="utf-8", level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    load_dotenv(HERE / ".env")
    parser = argparse.ArgumentParser(description="Theo dõi cổng thông tin sinh viên UTEHY")
    parser.add_argument("--test-notify", action="store_true", help="gửi thử một thông báo rồi thoát")
    args = parser.parse_args()

    topic = os.getenv("NTFY_TOPIC", "").strip()
    if args.test_notify:
        notify.send(topic, "UTEHY Watch: thử thông báo",
                    "Nếu bạn thấy tin này trên điện thoại là ntfy đã chạy.",
                    "Nếu bạn thấy tin này trên máy tính là thông báo Windows đã chạy.", PORTAL_URL)
        say("Đã gửi thông báo thử" + (f" (kênh ntfy: {topic})." if topic else ". Chưa có NTFY_TOPIC nên không gửi lên điện thoại."))
        return 0

    user, password = os.getenv("UTEHY_USER", "").strip(), os.getenv("UTEHY_PASS", "")
    if not user or not password:
        say("Thiếu UTEHY_USER hoặc UTEHY_PASS. Mở file .env và điền mã sinh viên, mật khẩu (xem README.md).")
        return 1
    return check(user, password, topic)


if __name__ == "__main__":
    sys.exit(main())
