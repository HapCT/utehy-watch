"""Đăng nhập cổng thông tin sinh viên UTEHY và đọc điểm, lịch thi, lịch học theo tuần."""
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

BASE = "https://qldaotao.utehy.edu.vn"
TIMEOUT = 30


class LoginError(Exception):
    pass


def table_rows(table):
    """Các dòng dữ liệu của bảng dưới dạng list ô chữ, đã trải rowspan/colspan ra cho thẳng cột."""
    grid, carry = [], {}  # carry: cột -> (số dòng còn lại, chữ) do rowspan để lại
    for tr in table.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if not cells:
            continue  # dòng tiêu đề
        row, col, queue = [], 0, list(cells)
        while queue or col in carry:
            if col in carry:
                left, text = carry[col]
                row.append(text)
                if left > 1:
                    carry[col] = (left - 1, text)
                else:
                    del carry[col]
                col += 1
                continue
            td = queue.pop(0)
            text = " ".join(td.get_text(" ", strip=True).split())
            rowspan = int(td.get("rowspan", 1) or 1)
            for i in range(int(td.get("colspan", 1) or 1)):
                cell = text if i == 0 else ""  # ô gộp ngang chỉ giữ chữ ở cột đầu
                if rowspan > 1:
                    carry[col] = (rowspan - 1, cell)
                row.append(cell)
                col += 1
        grid.append(row)
    return grid


def _data_rows(table, min_cells, required):
    # Bỏ các dòng "Không có dữ liệu" hay dòng tổng kết: chúng trống ở các cột bắt buộc.
    return [
        row for row in table_rows(table)
        if len(row) >= min_cells and all(row[i] for i in required)
    ]


def parse_grades(html):
    """{mã học phần: {"name", "cells"}} từ trang Kết quả học tập."""
    table = BeautifulSoup(html, "html.parser").find("table", id="ctl00_ContentCP_ctl00_gvDiem")
    grades = {}
    if table is None:
        return grades
    for row in _data_rows(table, 10, required=(1, 2)):
        key = row[1]
        n = 2
        while key in grades:  # học lại cùng một môn
            key = f"{row[1]}#{n}"
            n += 1
        grades[key] = {"name": row[2], "cells": row[3:]}
    return grades


def parse_exams(html):
    """{mã học phần + lần thi: thông tin buổi thi} từ trang Lịch thi sinh viên."""
    table = BeautifulSoup(html, "html.parser").find("table", id="ctl00_ContentCP_ctl00_gvDiem")
    exams = {}
    if table is None:
        return exams
    for row in _data_rows(table, 10, required=(1, 2)):
        exams[f"{row[1]}|lần {row[6]}"] = {
            "name": row[2], "date": row[4], "time": row[5], "room": row[9], "form": row[10] if len(row) > 10 else "",
        }
    return exams


def day_name(day):
    """Trang trường ghi thứ bằng số: "2" là Thứ 2, "8" (hoặc "1", "CN") là Chủ nhật."""
    day = day.strip()
    if day.upper() in ("1", "8", "CN") or day.lower() == "chủ nhật":
        return "Chủ nhật"
    return f"Thứ {day}" if day.isdigit() else day


def parse_week_sessions(html):
    """Các buổi học trong một tuần: [{"day", "period", "name", "room", "teacher"}, ...]."""
    sessions = []
    for table in BeautifulSoup(html, "html.parser").find_all("table"):
        for row in _data_rows(table, 6, required=(0, 3)):
            sessions.append({
                "day": day_name(row[0]), "period": row[1], "name": row[3], "room": row[5],
                "teacher": row[6] if len(row) > 6 else "",
            })
    return sessions


def parse_week(html):
    """Các buổi học trong một tuần, mỗi buổi là một dòng chữ, đã sắp xếp (dùng để so sánh)."""
    return sorted({
        f"{s['day']}, tiết {s['period']}: {s['name']}, phòng {s['room']}" + (f", GV {s['teacher']}" if s["teacher"] else "")
        for s in parse_week_sessions(html)
    })


def week_ranges(html):
    """{tuần thứ: (ngày đầu, ngày cuối)} đọc từ danh sách tuần, ví dụ "Tuần 9 [Từ 19/10/2026 -- Đến 25/10/2026]"."""
    ranges = {}
    for option in BeautifulSoup(html, "html.parser").select("#cmbTuanThu option"):
        found = re.findall(r"(\d{1,2})/(\d{1,2})/(\d{4})", option.get_text())
        if option.get("value", "").isdigit() and len(found) == 2:
            start, end = (date(int(y), int(m), int(d)) for d, m, y in found)
            ranges[int(option["value"])] = (start, end)
    return ranges


def current_week(html):
    """(năm học, tuần thứ) đang được chọn sẵn trên trang Thông tin lịch học, hoặc None."""
    soup = BeautifulSoup(html, "html.parser")
    year = soup.select_one("#cmbNamHoc2 option[selected]")
    week = soup.select_one("#cmbTuanThu option[selected]")
    if not year or not week or year.get("value") in (None, "-1") or week.get("value") in (None, "-1"):
        return None
    return year["value"], int(week["value"])


def login(user, password):
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (UTEHY grade watcher for personal use)"
    session.get(f"{BASE}/DangNhap/Login", timeout=TIMEOUT)
    session.post(
        f"{BASE}/DangNhap/CheckLogin",
        files={"Role": (None, "0"), "Username": (None, user), "password": (None, password)},
        timeout=TIMEOUT,
    )
    home = session.get(f"{BASE}/SinhVien", timeout=TIMEOUT)
    if "/DangNhap" in home.url:
        raise LoginError("Sai mã sinh viên hoặc mật khẩu, hoặc trang trường đổi cách đăng nhập.")
    return session


def _getter(session):
    def get(path):
        response = session.get(BASE + path, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text
    return get


def fetch_day(user, password, day):
    """(các buổi học, mọi lịch thi) cho tin nhắc ngày `day`, chung một lần đăng nhập.
    Các buổi học là None nếu ngày đó không nằm trong năm học đang hiện trên cổng."""
    get = _getter(login(user, password))
    return _day_sessions(get, day), parse_exams(get("/TraCuuLichThi/Index"))


def _day_sessions(get, day):
    index = get("/TraCuuLichHoc/Index")
    week = current_week(index)
    if not week:
        return None
    year = week[0]
    for number, (start, end) in week_ranges(index).items():
        if start <= day <= end:
            sessions = parse_week_sessions(get(f"/TraCuuLichHoc/DanhSachTuan?Nam_hoc={year}&Tuan_thu={number}"))
            wanted = day_name(str(day.isoweekday() + 1))  # thứ Hai -> "2", ..., Chủ nhật -> "8"
            return [s for s in sessions if s["day"] == wanted]
    return None


def fetch_all(user, password):
    """Đăng nhập rồi đọc mọi thứ cần theo dõi."""
    get = _getter(login(user, password))

    snapshot = {
        "grades": parse_grades(get("/TraCuuDiem/Index")),
        "exams": parse_exams(get("/TraCuuLichThi/Index")),
        "weeks": {},
    }
    week = current_week(get("/TraCuuLichHoc/Index"))
    if week:
        year, number = week
        for n in (number, number + 1):  # tuần này và tuần sau, giống trang trường
            snapshot["weeks"][f"{year} tuần {n}"] = parse_week(
                get(f"/TraCuuLichHoc/DanhSachTuan?Nam_hoc={year}&Tuan_thu={n}")
            )
    return snapshot
