import socket
import os
import base64
import ssl

# Cấu hình
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

def save_attachment(attachment_data, filename):
    with open(filename, 'wb') as attachment_file:
        attachment_file.write(base64.b64decode(attachment_data))

def process_part(part, uid):
    content_type = part.split(b'\r\nContent-Type: ')[1].split(b'\r\n')[0].decode('utf-8')
    content_disposition = part.split(b'\r\nContent-Disposition: ')[1].split(b'\r\n')[0].decode('utf-8')

    if content_type.startswith("text"):
        # Xử lý phần văn bản
        content = part.split(b'\r\n\r\n')[1].decode('utf-8')
        print(f"Text content:\n{content}")
    elif content_disposition.startswith("attachment"):
        # Xử lý phần đính kèm
        filename = content_disposition.split('filename=')[1].strip('"')
        filename = f'{uid}_{filename}'
        save_attachment(part.split(b'\r\n\r\n')[1], filename)
        print(f"Saved attachment: {filename}")

def process_multipart(multipart_data, uid):
    boundary = multipart_data.split(b'\r\n')[0].decode('utf-8').split('boundary=')[1].strip('"')
    parts = multipart_data.split(b'--' + boundary)[1:-1]

    for part in parts:
        process_part(part, uid)

def process_mime(email_content, uid):
    mime_index = email_content.find(b'Content-Type: multipart')
    if mime_index != -1:
        # Nếu có phần MIME
        mime_data = email_content[mime_index:]
        process_multipart(mime_data, uid)
    else:
        # Nếu không có phần MIME, xử lý nội dung trực tiếp
        process_part(email_content, uid)

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
            process_mime(email_content, uid)

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
