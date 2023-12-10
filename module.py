import socket
import json
import os
import email
import ssl
from email.parser import BytesParser
from email.policy import default



# with open('config.json', 'r') as file:
#     config = json.load(file)

# SMTP_SERVER = config.get('SMTP', 'server')
# SMTP_PORT = config.get('SMTP', 'port')
# POP3_SERVER = config.get('POP3', 'server')
# POP3_PORT = config.get('POP3', 'port')
# USERNAME = config.get('Account', 'username')
# PASSWORD = config.get('Account', 'password')

POP3_SERVER = "pop.example.com"
POP3_PORT = 995
USERNAME = "your_email@example.com"
PASSWORD = "your_email_password"

# Hàm để đọc danh sách UID từ tệp
def read_uid_list():
    uid_list = set()
    if os.path.exists('uid_list.txt'):
        with open('uid_list.txt', 'r') as file:
            uid_list = set(file.read().splitlines())
    return uid_list

# Hàm để ghi danh sách UID vào tệp
def write_uid_list(uid_list):
    with open('uid_list.txt', 'w') as file:
        file.write('\n'.join(uid_list))



# Kết nối đến Mail Server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    ip_address = socket.gethostbyname(POP3_SERVER)
    print(f"The IP address of {POP3_SERVER} is {ip_address}")
except socket.gaierror as e:
    print(f"Error resolving {POP3_SERVER}: {e}")

# Xác thực đăng nhập
client_socket.sendall(f'USER {USERNAME}\r\n'.encode())
response = client_socket.recv(1024).decode()
print(response)

client_socket.sendall(f'PASS {PASSWORD}\r\n'.encode())
response = client_socket.recv(1024).decode()
print(response)

# Đọc danh sách UID đã tải trước đó
downloaded_uids = read_uid_list()

# Lấy số lượng email và danh sách UID
client_socket.sendall(b'STAT\r\n')
response = client_socket.recv(1024).decode()
print(response)

client_socket.sendall(b'UIDL\r\n')
response = client_socket.recv(1024).decode()
uid_list_response = response.splitlines()[1:]  # Bỏ qua dòng đầu tiên chứa thông tin số lượng email
print(uid_list_response)

# Lặp qua danh sách UID và tải những email chưa tải
for uid_response in uid_list_response:
    uid = uid_response.split()[0]
    if uid not in downloaded_uids:
        # Tải nội dung của email
        client_socket.sendall(f'RETR {uid}\r\n'.encode())
        email_content = client_socket.recv(4096).decode()  # Đọc nội dung email

        # Phân tích cú pháp email để lấy thông tin về tiêu đề và nội dung
        msg = BytesParser(policy=default).parsebytes(email_content.encode())
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

        # Kiểm tra từ khóa spam trong tiêu đề và nội dung
        spam_keywords = ["viagra", "lottery", "free money"]  # Thêm các từ khóa spam khác vào đây
        is_spam = any(keyword.lower() in subject.lower() or keyword.lower() in body.lower() for keyword in spam_keywords)

        # Di chuyển email vào thư mục Spam nếu là spam
        if is_spam:
            # Thực hiện logic để di chuyển email vào thư mục Spam
            print(f"Email with UID {uid} is marked as spam. Moving to Spam folder.")
            # Đặt logic di chuyển email vào thư mục Spam ở đây

        # Ghi UID vào danh sách đã tải
        downloaded_uids.add(uid)

# Ghi danh sách UID đã tải vào tệp
write_uid_list(downloaded_uids)

# Đóng kết nối
client_socket.sendall(b'QUIT\r\n')
response = client_socket.recv(1024).decode()
print(response)

client_socket.close()
