import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from changes import find_changes, merge_state  # noqa: E402
from portal import current_week, parse_exams, parse_grades, parse_week  # noqa: E402

GRADES_HTML = """
<table id="ctl00_ContentCP_ctl00_gvDiem">
<tr><th>STT</th><th>Mã học phần</th><th>Tên học phần</th><th>Số tín chỉ</th><th>Hệ số</th>
<th>Điểm thành phần</th><th>Điểm thi</th><th>TBCHP</th><th>Điểm số</th><th>Điểm chữ</th><th>Môn tự chọn</th><th>Ghi chú</th></tr>
<tr><td>1</td><td>IT101</td><td>Lập trình Web</td><td>3</td><td>1</td><td>8</td><td>{web_exam}</td><td>{web_avg}</td><td>{web_num}</td><td>{web_letter}</td><td></td><td></td></tr>
<tr><td>2</td><td>IT102</td><td>Cơ sở dữ liệu</td><td>3</td><td>1</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td colspan="12">Tổng số tín chỉ: 6</td></tr>
</table>
"""

EXAMS_HTML = """
<table id="ctl00_ContentCP_ctl00_gvDiem">
<tr><th>STT</th><th>Mã học phần</th><th>Tên học phần</th><th>Số tín chỉ</th><th>Ngày thi</th><th>Giờ thi</th>
<th>Lần thi</th><th>Đợt thi</th><th>Số báo danh</th><th>Phòng thi</th><th>Hình thức</th></tr>
<tr><td>1</td><td>IT101</td><td>Lập trình Web</td><td>3</td><td>{date}</td><td>07:30</td><td>1</td><td>1</td><td>12</td><td>{room}</td><td>Viết</td></tr>
</table>
"""

# Cột "Thứ" gộp nhiều dòng bằng rowspan, như hay gặp ở thời khoá biểu.
WEEK_HTML = """
<table>
<tr><th>Thứ</th><th>Tiết</th><th>Ký hiệu</th><th>Tên môn</th><th>Tên lớp học phần</th><th>Phòng học</th><th>Giảng viên</th></tr>
<tr><td rowspan="2">2</td><td>1-3</td><td>IT101</td><td>Lập trình Web</td><td>IT101.1</td><td>{room}</td><td>Cô A</td></tr>
<tr><td>4-6</td><td>IT102</td><td>Cơ sở dữ liệu</td><td>IT102.2</td><td>B1-201</td><td>Thầy B</td></tr>
<tr><td colspan="7">Không có dữ liệu</td></tr>
</table>
"""

INDEX_HTML = """
<select id="cmbNamHoc2"><option value="-1">--</option><option value="2026-2027" selected>2026-2027</option></select>
<select id="cmbTuanThu"><option value="8">Tuần 8</option><option value="9" selected>Tuần 9</option></select>
"""


def grades(exam="", avg="", num="", letter=""):  # num là điểm hệ 4
    return parse_grades(GRADES_HTML.format(web_exam=exam, web_avg=avg, web_num=num, web_letter=letter))


def snapshot(g=None, date="10/12/2026", room="A2-301", week_room="A1-101"):
    return {
        "grades": g if g is not None else grades(),
        "exams": parse_exams(EXAMS_HTML.format(date=date, room=room)),
        "weeks": {"2026-2027 tuần 9": parse_week(WEEK_HTML.format(room=week_room))},
    }


def test_parse_grades_skips_summary_row():
    g = grades("9", "8.6", "3.7", "A")
    assert list(g) == ["IT101", "IT102"]
    assert g["IT101"]["name"] == "Lập trình Web"


def test_parse_week_expands_rowspan():
    sessions = parse_week(WEEK_HTML.format(room="A1-101"))
    assert sessions == [
        "Thứ 2, tiết 1-3: Lập trình Web, phòng A1-101, GV Cô A",
        "Thứ 2, tiết 4-6: Cơ sở dữ liệu, phòng B1-201, GV Thầy B",
    ]


def test_current_week():
    assert current_week(INDEX_HTML) == ("2026-2027", 9)
    assert current_week("<html></html>") is None


def test_no_changes_no_events():
    assert find_changes(snapshot(), snapshot()) == []


def test_new_grade_is_reported_without_score_on_phone():
    before = snapshot()
    after = snapshot(grades("9", "8.6", "3.7", "A"))
    events = find_changes(before, after)
    assert len(events) == 1
    assert events[0]["public"] == "Có điểm mới: Lập trình Web"
    assert "8.6 (A)" in events[0]["detail"]
    assert "8.6" not in events[0]["public"]


def test_updated_grade():
    before = snapshot(grades("5", "6.2", "6.2", "C"))
    after = snapshot(grades("7", "7.4", "7.4", "B"))
    assert find_changes(before, after)[0]["public"] == "Điểm được cập nhật: Lập trình Web"


def test_course_without_scores_is_not_reported():
    before = {**snapshot(), "grades": {}}
    events = find_changes(before, snapshot())
    # IT101 có điểm thành phần 8 nên được báo; IT102 chưa có điểm nên không.
    assert [e["public"] for e in events] == ["Có điểm mới: Lập trình Web"]


def test_exam_changes():
    events = find_changes(snapshot(), snapshot(room="C3-105"))
    assert events[0]["public"] == "Lịch thi thay đổi: Lập trình Web (10/12/2026 07:30, phòng C3-105)"
    events = find_changes({**snapshot(), "exams": {}}, snapshot())
    assert events[0]["public"].startswith("Lịch thi mới: Lập trình Web")


def test_week_change_lists_old_and_new_session():
    events = find_changes(snapshot(), snapshot(week_room="A9-999"))
    text = events[0]["public"]
    assert text.startswith("Lịch học 2026-2027 tuần 9 thay đổi")
    assert "− Thứ 2, tiết 1-3: Lập trình Web, phòng A1-101" in text
    assert "+ Thứ 2, tiết 1-3: Lập trình Web, phòng A9-999" in text


def test_new_week_is_remembered_not_reported():
    before = {**snapshot(), "weeks": {}}
    assert find_changes(before, snapshot()) == []
    assert "2026-2027 tuần 9" in merge_state(before, snapshot())["weeks"]
