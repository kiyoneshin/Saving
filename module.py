
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

def process_multipart(multipart_data, uid):
    boundary = multipart_data.get_content_type().split("=")[-1]
    parts = multipart_data.get_payload()

    for part in parts:
        process_part(part, uid)

def process_part(part, uid):
    content_type = part.get_content_type()
    content_disposition = part.get("Content-Disposition")

    if content_type.startswith("text"):
        # Xử lý phần văn bản
        content = part.get_payload(decode=True).decode('utf-8')
        print(f"Text content:\n{content}")
    elif content_disposition and content_disposition.startswith("attachment"):
        # Xử lý phần đính kèm
        filename = part.get_filename()
        if filename:
            filename = f'{uid}_{filename}'
            save_attachment(part.get_payload(), filename)
            print(f"Saved attachment: {filename}")
    elif content_type.startswith("multipart"):
        # Xử lý phần multipart (đệ quy)
        process_multipart(part, uid)

def process_mime(email_content, uid):
    lines = email_content.split('\r\n')

    # Tìm dòng bắt đầu của phần MIME
    start_index = None
    for i, line in enumerate(lines):
        if line.startswith("--"):
            start_index = i
            break

    if start_index is not None:
        # Xử lý từ dòng bắt đầu của phần MIME
        mime_data = '\r\n'.join(lines[start_index:])
        msg_start = email_content.find(mime_data)
        mime_msg = email_content[msg_start:]

        # Phân tích MIME message
        message = email.message_from_string(mime_msg)

        # Xử lý từng phần trong message
        for part in message.walk():
            process_part(part, uid)
    else:
        # Nếu không tìm thấy dòng bắt đầu của phần MIME, xử lý nội dung trực tiếp
        process_part(email.message_from_string(email_content), uid)

def get_uid_list(response):
    lines = response.splitlines()[1:]
    return [uid.split()[0] for uid in lines]

def get_uid_from_response(response):
    lines = response.splitlines()
    if lines[0].startswith(b'+OK'):
        return lines[1].split()[0].decode('utf-8')
    else:
        return None

def main():
    downloaded_uids = read_uid_list()

    # Lấy danh sách UID
    client_socket.sendall(b'UIDL\r\n')
    response = client_socket.recv(1024).decode()
    uid_list_response = response.splitlines()[1:]
    print(uid_list_response)

    for uid_response in uid_list_response:
        uid = get_uid_from_response(uid_response)
        if uid and uid not in downloaded_uids:
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

