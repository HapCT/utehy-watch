"""So sánh lần đọc mới với lần trước và tạo ra các thông báo."""


def _grade_text(cells):
    # Đếm từ cuối: Ghi chú, Môn tự chọn, Điểm chữ, Điểm số (hệ 4), TBCHP (hệ 10).
    if len(cells) < 5:
        return ""
    number, letter = cells[-5], cells[-3]
    if number and letter:
        return f"{number} ({letter})"
    return number or letter


def _has_scores(cells):
    # Bỏ "Số tín chỉ", "Hệ số" ở đầu và hai cột cuối; còn lại là các cột điểm.
    return any(cells[2:-2])


def find_changes(old, new):
    """Trả về list thông báo {"public": ..., "detail": ...}.

    "public" được gửi lên điện thoại nên không chứa số điểm; "detail" chỉ hiện trên máy tính.
    """
    events = []

    old_grades = old.get("grades", {})
    for key, grade in new["grades"].items():
        before = old_grades.get(key)
        if before and before["cells"] == grade["cells"]:
            continue
        if not _has_scores(grade["cells"]):
            continue  # môn mới đăng ký, chưa có điểm
        # Một ô điểm đã có giá trị mà bị đổi là "cập nhật"; chỉ thêm điểm vào ô trống là "điểm mới".
        old_cells = before["cells"] if before else []
        revised = any(a and a != b for a, b in zip(old_cells[2:-2], grade["cells"][2:-2]))
        verb = "Điểm được cập nhật" if revised else "Có điểm mới"
        score = _grade_text(grade["cells"])
        events.append({
            "public": f"{verb}: {grade['name']}",
            "detail": f"{verb}: {grade['name']}" + (f" → {score}" if score else ""),
        })

    old_exams = old.get("exams", {})
    for key, exam in new["exams"].items():
        before = old_exams.get(key)
        if before == exam:
            continue
        when = f"{exam['date']} {exam['time']}, phòng {exam['room']}".strip()
        verb = "Lịch thi mới" if before is None else "Lịch thi thay đổi"
        text = f"{verb}: {exam['name']} ({when})"
        events.append({"public": text, "detail": text})

    old_weeks = old.get("weeks", {})
    for week, sessions in new["weeks"].items():
        before = old_weeks.get(week)
        if before is None or before == sessions:
            continue  # tuần mới xuất hiện thì chỉ ghi nhớ, không báo
        added = [f"+ {s}" for s in sessions if s not in before]
        removed = [f"− {s}" for s in before if s not in sessions]
        lines = "\n".join(removed + added)
        events.append({"public": f"Lịch học {week} thay đổi:\n{lines}", "detail": f"Lịch học {week} thay đổi:\n{lines}"})

    return events


def merge_state(old, new):
    """Trạng thái lưu lại: điểm và lịch thi lấy bản mới; giữ lịch các tuần gần đây để so sánh."""
    weeks = dict(old.get("weeks", {}))
    weeks.update(new["weeks"])
    recent = dict(list(weeks.items())[-6:])
    return {**old, "grades": new["grades"], "exams": new["exams"], "weeks": recent}
