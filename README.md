
Để chạy dự án /n
**cài đặt thư viện**/n
pip install flask flask-sqlalchemy/n
**tạo dữ liệu mẫu**/n
python seed.py/n
**khởi động server**/n
python app.py/n

**Cấu trúc Thư Mục**
canteenhcmut/
│
├── app.
```py                  # File chạy server (Backend & APIs)
├── models.py               # Định nghĩa các bảng trong Database
├── seed.py                 # File nạp dữ liệu mẫu ban đầu
├── README.md               # Tài liệu mô tả dự án
├── instance/               # Chứa file Database SQLite
└── templates/              # Chứa giao diện Frontend (HTML)
    ├── index.html          # Trang đặt món cho Khách
    ├── staff.html          # Trang quản lý đơn cho Nhân viên
    └── dashboard.html      # Trang thống kê & quản lý kho
