
import socket
import json
import os
import email
import ssl
from email.parser import BytesParser
from email.policy import default

# ... (Các phần khác của mã)

# Lặp qua danh sách UID và tải những email chưa tải
for uid_response in uid_list_response:
    uid = uid_response.split()[0]
    if uid not in downloaded_uids:
        # Tải nội dung của email
        client_socket.sendall(f'RETR {uid}\r\n'.encode())
        email_content = client_socket.recv(4096).decode()  # Đọc nội dung email

        # Phân tích cú pháp email để lấy thông tin về tiêu đề, địa chỉ người gửi và nội dung
        msg = BytesParser(policy=default).parsebytes(email_content.encode())
        sender = msg.get("From", "")
        subject = msg.get("Subject", "")
        body = ""

        for part in msg.iter_parts():
            if part.is_multipart():
                # Nếu là multipart, lấy phần text/plain
                for subpart in part.iter_parts():
                    if subpart.get_content_type() == "text/plain":
                        body += subpart.get_payload()
            elif part.get_content_type() == "text/plain":
                # Nếu là text/plain
                body += part.get_payload()

        # Kiểm tra và xử lý lọc email dựa trên địa chỉ người gửi
        if "spam_sender@example.com" in sender.lower():
            print(f"Email with UID {uid} is from a spam sender. Moving to Spam folder.")
            # Thực hiện logic di chuyển email vào thư mục Spam ở đây
            continue  # Bỏ qua xử lý tiếp theo vì đã di chuyển vào thư mục Spam

        # Kiểm tra và xử lý lọc email dựa trên subject
        if "spam_keyword" in subject.lower():
            print(f"Email with UID {uid} has a spam subject. Moving to Spam folder.")
            # Thực hiện logic di chuyển email vào thư mục Spam ở đây
            continue  # Bỏ qua xử lý tiếp theo vì đã di chuyển vào thư mục Spam

        # Kiểm tra và xử lý lọc email dựa trên nội dung
        if "spam_keyword" in body.lower():
            print(f"Email with UID {uid} has spam content. Moving to Spam folder.")
            # Thực hiện logic di chuyển email vào thư mục Spam ở đây
            continue  # Bỏ qua xử lý tiếp theo vì đã di chuyển vào thư mục Spam

        # Logic di chuyển email vào các thư mục cụ thể dựa trên điều kiện khác (ví dụ: nếu không phải spam)
        if "important_sender@example.com" in sender.lower():
            print(f"Email with UID {uid} is from an important sender. Moving to Important folder.")
            # Thực hiện logic di chuyển email vào thư mục quan trọng ở đây

        # Ghi UID vào danh sách đã tải
        downloaded_uids.add(uid)

# ... (Các phần khác của mã)
