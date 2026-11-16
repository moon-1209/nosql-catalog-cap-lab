\# NoSQL Catalog \& CAP Lab



Đồ án môn học Cloud Computing - Phân tích CAP và NoSQL.



\## Yêu cầu hệ thống

\- Python 3.11+

\- MongoDB (nếu muốn chạy thật, nếu không có script sẽ tự động dùng Mock Data để sinh log)

\- Git



\## Hướng dẫn cài đặt môi trường (Clean Run)

1\. Clone repository:

&#x20;  `git clone https://github.com/moon-1209/nosql-catalog-cap-lab.git`

2\. Di chuyển vào thư mục dự án:

&#x20;  `cd nosql-catalog-cap-lab`

3\. Cài đặt các thư viện Python cần thiết:

&#x20;  `pip install -r requirements.txt`



\## Danh sách các kịch bản thí nghiệm (Scripts)

Tất cả các script đều tự động lưu kết quả log (JSONL) và báo cáo (CSV) vào thư mục `experiments/`.



1\. \*\*Benchmark đo độ trễ cơ bản:\*\*

&#x20;  `python scripts/benchmark\_harness.py`

&#x20;  \*Kết quả: experiments/...\*



2\. \*\*Thí nghiệm E1a - Phân phối Zipf (Schema A):\*\*

&#x20;  `python scripts/e1a\_zipf\_workload.py`

&#x20;  \*Kết quả: experiments/e1a\_zipf/\*



3\. \*\*Thí nghiệm E1b - Phân phối Bucketing (Schema B):\*\*

&#x20;  `python scripts/e1b\_bucketing\_workload.py`

&#x20;  \*Kết quả: experiments/e1b\_bucketing/\*



4\. \*\*Thí nghiệm E2-E5 - Ma trận CAP (Consistency Level):\*\*

&#x20;  `python scripts/cap\_matrix\_e2\_e5.py`

&#x20;  \*Kết quả: experiments/cap\_matrix/\*



5\. \*\*Thí nghiệm LWT/Counter - Chống Oversell:\*\*

&#x20;  `python scripts/lwt\_counter\_oversell.py`

&#x20;  \*Kết quả: experiments/lwt\_oversell/\*



6\. \*\*Thí nghiệm E6 - Rollback trên Replica Set:\*\*

&#x20;  `python scripts/mongodb\_rollback\_e6.py`

&#x20;  \*Kết quả: experiments/e6\_rollback/\*



\## Cấu trúc thư mục

\- `scripts/`: Chứa toàn bộ code Python thực thi các thí nghiệm.

\- `experiments/`: Chứa dữ liệu log và báo cáo sinh ra sau khi chạy script.

