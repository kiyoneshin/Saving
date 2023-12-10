import socket
import os
import base64
import ssl
from email import policy
from email.parser import BytesParser

# Các biến cấu hình
POP3_SERVER = "pop.example.com"
POP3_PORT = 995
USERNAME = "your_email@example.com"
PASSWORD = "your_email_password"
DOWNLOAD_PATH = "downloaded_emails"

def read_uid_list():
    uid_list = set()
    if os.path.exists('uid_list.txt'):
        with open('uid_list.txt', 'r') as file:
            uid_list = set(file.read().splitlines())
    return uid_list

def write_uid_list(uid_list):
    with open('uid_list.txt', 'w') as file:
        file.write('\n'.join(uid_list))

def decode_base64(data):
    return base64.b64decode(data).decode('utf-8')

def download_email(uid, client_socket):
    client_socket.sendall(f'RETR {uid}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    email_content = ''
    while True:
        data = client_socket.recv(4096).decode()
        email_content += data
        if data.endswith('\r\n.\r\n'):
            break

    return email_content

def process_multipart(mime_header, mime_body):
    # TODO: Thực hiện xử lý cho các phần multipart
    msg = BytesParser(policy=policy.default).parsebytes(mime_body.encode())
    for part in msg.iter_parts():
        content_type = part.get_content_type()
        if content_type.startswith("text/"):
            process_text_part(part)
        elif content_type.startswith("image/") or content_type.startswith("application/"):
            process_attachment(part)

def process_text_plain(mime_body):
    # TODO: Thực hiện xử lý cho phần text/plain
    print("Text/Plain Content:")
    print(mime_body)

def process_text_part(part):
    content_type = part.get_content_type()
    content = part.get_payload(decode=True).decode(part.get_content_charset())
    print(f"Text Part ({content_type}):")
    print(content)

def process_attachment(part):
    filename = part.get_filename()
    if filename:
        print(f"Found attachment: {filename}")
        # TODO: Lưu tệp đính kèm xuống máy cục bộ của client
        with open(filename, 'wb') as attachment_file:
            attachment_file.write(part.get_payload(decode=True))

def main():
    # Kết nối đến Mail Server qua SSL
    context = ssl.create_default_context()
    client_socket = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=POP3_SERVER)
    client_socket.connect((POP3_SERVER, POP3_PORT))
    response = client_socket.recv(1024).decode()
    print(response)

    # Xác thực đăng nhập
    client_socket.sendall(f'USER {USERNAME}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.sendall(f'PASS {PASSWORD}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    downloaded_uids = read_uid_list()

    # Lấy danh sách UID
    client_socket.sendall(b'UIDL\r\n')
    response = client_socket.recv(1024).decode()
    uid_list_response = response.splitlines()[1:]
    print(uid_list_response)

    for uid_response in uid_list_response:
        uid = uid_response.split()[0]
        if uid not in downloaded_uids:
            email_content = download_email(uid, client_socket)
            
            # Xử lý MIME để trích xuất nội dung và đính kèm
            mime_header, mime_body = extract_mime_parts(email_content)

            # Thực hiện xử lý MIME cho từng loại MIME
            if mime_header and mime_body:
                if "multipart" in mime_header.lower():
                    process_multipart(mime_header, mime_body)
                elif "text/plain" in mime_header.lower():
                    process_text_plain(mime_body)
            
            # Ghi nội dung email vào tệp
            file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
            with open(file_path, 'w', encoding='utf-8') as email_file:
                email_file.write(email_content)

            downloaded_uids.add(uid)

    write_uid_list(downloaded_uids)

    client_socket.sendall(b'QUIT\r\n')
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.close()

if __name__ == "__main__":
    main()
