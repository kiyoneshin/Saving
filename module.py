import socket
import os
import base64
import ssl
import re

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

def extract_headers_and_body(mime_msg):
    header_end = mime_msg.find('\r\n\r\n')
    if header_end != -1:
        headers = mime_msg[:header_end]
        body = mime_msg[header_end + 4:]
        return headers, body
    else:
        return None, None

def get_content_type(headers):
    content_type_match = re.search(r'Content-Type: (.+?)(;|$)', headers, re.IGNORECASE)
    if content_type_match:
        return content_type_match.group(1).strip()
    else:
        return None

def process_part (part, uid):
    headers, body = extract_headers_and_body(part)

    if headers and body:
        content_type = get_content_type(headers)

        if content_type and content_type.startswith("text"):
            content = body.decode('utf-8')
            print(f"Text content:\n{content}")
        elif content_type and content_type.startswith("multipart"):
            process_multipart (body, uid)
        elif content_type and content_type.startswith("image"):
            filename = f'{uid}_image.jpg'
            with open(filename, 'wb') as image_file:
                image_file.write(body)
            print(f"Saved image: {filename}")
        elif content_type and content_type.startswith("application"):
            filename = f'{uid}_attachment.bin'
            with open(filename, 'wb') as attachment_file:
                attachment_file.write(body)
            print(f"Saved attachment: {filename}")
        else:
            print("Unsupported content type")

def process_multipart (multipart_data, uid):
    boundary_match = re.search(r'boundary=(.+)', multipart_data, re.IGNORECASE)
    if boundary_match:
        boundary = boundary_match.group(1)
        parts = re.split(f'--{boundary}', multipart_data)[1:-1]

        for part in parts:
            process_part (part, uid)

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

def process_mime (email_content, uid):
    mime_headers, mime_body = extract_headers_and_body(email_content)

    if mime_headers and mime_body:
        content_type = get_content_type(mime_headers)

        if content_type and content_type.startswith("multipart"):
            process_multipart(mime_body, uid)
        else:
            process_part(email_content, uid)
    else:
        print("Invalid MIME format")

def main():
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
    response = client_socket.recv(4096).decode()
    uid_list_response = response.splitlines()[1:]
    print(uid_list_response)

    for uid_response in uid_list_response:
        uid = uid_response.split()[0]
        if uid not in downloaded_uids:
            email_content = download_email(uid, client_socket)

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
