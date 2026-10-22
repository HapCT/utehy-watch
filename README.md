# UTEHY Watch

Tự kiểm tra cổng thông tin sinh viên UTEHY mỗi 2 tiếng và báo cho bạn khi có:

- **điểm mới** hoặc điểm được sửa,
- **lịch thi mới** hoặc lịch thi bị đổi (ngày, giờ, phòng),
- **lịch học tuần này hoặc tuần sau thay đổi** (đổi phòng, đổi tiết, nghỉ, học bù).

Thông báo hiện ở **góc màn hình Windows** (có số điểm) và trên **điện thoại qua app ntfy** (không ghi số điểm, chỉ ghi tên môn). Bấm vào thông báo sẽ mở cổng trường.

## Cài đặt (làm một lần)

### 1. Điền mã sinh viên và mật khẩu
Mở file `.env` trong thư mục này bằng Notepad, điền vào sau dấu `=`:

```
UTEHY_USER=mã sinh viên của bạn
UTEHY_PASS=mật khẩu cổng trường
```

Dòng `NTFY_TOPIC` đã được điền sẵn một tên kênh ngẫu nhiên, giữ nguyên.

> File `.env` chỉ nằm trên máy bạn. Đừng gửi nó cho ai.

### 2. Cài app ntfy trên điện thoại
1. Cài **ntfy** từ Google Play hoặc App Store (miễn phí, không cần tài khoản).
2. Bấm **+** (Subscribe to topic), nhập đúng tên kênh trong dòng `NTFY_TOPIC` của file `.env`, rồi bấm Subscribe.

### 3. Thử
Mở terminal trong thư mục này:

```bash
.venv\Scripts\python watch.py --test-notify
```

Máy tính và điện thoại sẽ cùng nhận một thông báo thử. Sau đó chạy kiểm tra thật lần đầu:

```bash
.venv\Scripts\python watch.py
```

Lần đầu, script chỉ ghi nhớ hiện trạng (bao nhiêu môn, bao nhiêu lịch thi) và báo "đã bắt đầu theo dõi". Từ lần sau nó mới báo khi có gì thay đổi.

### 4. Cho nó tự chạy
```bash
powershell -ExecutionPolicy Bypass -File dat-lich.ps1
```

Từ giờ Windows sẽ tự chạy script **mỗi 2 tiếng** và **mỗi khi bạn đăng nhập máy**. Máy tắt thì không kiểm tra được; mở máy lên là nó kiểm tra bù.

Muốn tắt: `powershell -ExecutionPolicy Bypass -File huy-lich.ps1`

## Chạy trên GitHub (nhận thông báo cả khi máy tắt)

GitHub sẽ chạy script mỗi 2 tiếng trên máy chủ của họ, miễn phí, rồi báo về điện thoại qua ntfy. File `.github/workflows/watch.yml` đã có sẵn.

1. Tạo một repo **Private** (riêng tư) trên GitHub, rồi đẩy thư mục này lên. File `.env`, `state.json` và `watch.log` không bị đẩy lên (đã có trong `.gitignore`).
2. Trong repo, vào **Settings → Secrets and variables → Actions → New repository secret**, tạo ba secret:
   - `UTEHY_USER`: mã sinh viên
   - `UTEHY_PASS`: mật khẩu cổng trường
   - `NTFY_TOPIC`: tên kênh ntfy (giống trong `.env`)
3. Vào tab **Actions → UTEHY Watch → Run workflow** để chạy thử ngay. Điện thoại sẽ nhận "UTEHY Watch đã bắt đầu theo dõi".

**Tránh nhận hai lần:** nếu máy tính cũng đang chạy theo lịch (`dat-lich.ps1`), điện thoại sẽ nhận mỗi tin hai lần. Hãy xoá giá trị `NTFY_TOPIC` trong `.env` trên máy (để trống sau dấu `=`). Khi đó máy tính chỉ hiện thông báo Windows có số điểm, còn điện thoại nhận từ GitHub. Hoặc chạy `huy-lich.ps1` để chỉ dùng GitHub.

Lưu ý:
- GitHub đôi khi chạy trễ vài phút đến vài chục phút so với lịch.
- Máy chủ GitHub ở nước ngoài. Nếu trang trường chặn truy cập từ nước ngoài, lần chạy thử sẽ báo lỗi kết nối trong log của tab Actions.
- Repo riêng tư có 2.000 phút chạy miễn phí mỗi tháng; script dùng khoảng 400 phút.

## Khi có trục trặc

- **Nhận thông báo "không đăng nhập được":** bạn vừa đổi mật khẩu cổng trường. Sửa lại trong `.env`. Thông báo này chỉ hiện một lần cho tới khi đăng nhập lại được.
- **Không thấy thông báo gì:** mở `watch.log` để xem các lần kiểm tra gần nhất.
- **Trường đổi giao diện trang:** script có thể đọc sai hoặc không đọc được. Xem `watch.log`, rồi nhờ sửa lại cách đọc trong `portal.py`.
- **Muốn bắt đầu lại từ đầu:** xoá file `state.json`.

## Các file

| File | Việc |
| --- | --- |
| `watch.py` | Chương trình chính: đăng nhập, so sánh với lần trước, gửi thông báo |
| `portal.py` | Đăng nhập cổng trường và đọc bảng điểm, lịch thi, lịch học theo tuần |
| `changes.py` | Tìm ra cái gì đã thay đổi |
| `notify.py` | Gửi thông báo lên Windows và ntfy |
| `state.json` | Lần đọc gần nhất (có điểm của bạn; chỉ nằm trên máy) |
| `tests/` | Kiểm thử: `.venv\Scripts\python -m pytest` |
