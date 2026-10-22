"""Soạn tin nhắc lịch học và lịch thi ngày mai."""
import re
from datetime import datetime, timedelta, timezone

VIETNAM = timezone(timedelta(hours=7))  # Việt Nam không đổi giờ theo mùa


def tomorrow():
    return (datetime.now(VIETNAM) + timedelta(days=1)).date()


def _periods(period):
    """"1-3" -> (1, 3); "4" -> (4, 4); không đọc được -> None."""
    numbers = [int(n) for n in re.findall(r"\d+", period)]
    return (numbers[0], numbers[-1]) if numbers else None


def time_range(period, table):
    span = _periods(period)
    if not span or span[0] not in table or span[1] not in table:
        return ""
    return f"{table[span[0]][0]}–{table[span[1]][1]}"


def _day_label(day):
    weekday = "Chủ nhật" if day.isoweekday() == 7 else f"Thứ {day.isoweekday() + 1}"
    return f"{weekday}, {day:%d/%m}"


def build(sessions, day, table):
    """(tiêu đề, nội dung) cho các buổi học của `day`, hoặc None nếu hôm đó không có buổi nào."""
    if not sessions:
        return None
    lines = []
    for s in sorted(sessions, key=lambda s: (_periods(s["period"]) or (99, 99))):
        when = time_range(s["period"], table)
        head = f"{when} (tiết {s['period']})" if when else f"Tiết {s['period']}"
        lines.append(f"{head}: {s['name']}, phòng {s['room']}")
    title = f"Mai đi học: {_day_label(day)}"
    return title, "\n".join(lines)


def _same_day(text, day):
    """"26/10/2026" (hoặc "26/10/2026 (Thứ 2)") có phải ngày `day` không."""
    found = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    return bool(found) and tuple(map(int, found.groups())) == (day.day, day.month, day.year)


def build_exams(exams, day):
    """(tiêu đề, nội dung) cho các môn thi vào `day`, hoặc None nếu hôm đó không thi."""
    today = [e for e in exams.values() if _same_day(e["date"], day)]
    if not today:
        return None
    lines = []
    for e in sorted(today, key=lambda e: [int(n) for n in re.findall(r"\d+", e["time"])]):
        line = f"{e['time']}: {e['name']}, phòng {e['room']}"
        lines.append(line + (f" ({e['form']})" if e["form"] else ""))
    return f"Mai thi: {_day_label(day)}", "\n".join(lines)
