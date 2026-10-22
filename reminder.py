"""Soạn tin nhắc lịch học ngày mai."""
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


def build(sessions, day, table):
    """(tiêu đề, nội dung) cho các buổi học của `day`, hoặc None nếu hôm đó không có buổi nào."""
    if not sessions:
        return None
    weekday = "Chủ nhật" if day.isoweekday() == 7 else f"Thứ {day.isoweekday() + 1}"
    lines = []
    for s in sorted(sessions, key=lambda s: (_periods(s["period"]) or (99, 99))):
        when = time_range(s["period"], table)
        head = f"{when} (tiết {s['period']})" if when else f"Tiết {s['period']}"
        lines.append(f"{head}: {s['name']}, phòng {s['room']}")
    title = f"Mai đi học: {weekday}, {day:%d/%m}"
    return title, "\n".join(lines)
