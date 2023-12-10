import socket
import os

# Các biến cấu hình
POP3_SERVER = "pop.example.com"
POP3_PORT = 995
USERNAME = "your_email@example.com"
PASSWORD = "your_email_password"
DOWNLOAD_PATH = "downloaded_emails"
PROJECT_FOLDER = 'Project'
IMPORTANT_FOLDER = 'Important'
WORK_FOLDER = 'Work'
SPAM_FOLDER = 'Spam'

# Quy tắc lọc
FILTER_RULES = {
    'Project': ['ahihi@testing.com', 'ahuu@testing.com'],
    'Important': ['urgent', 'ASAP'],
    'Work': ['report', 'meeting'],
}

# Từ khóa spam
SPAM_KEYWORDS = ['virus', 'hack', 'crack']

def read_uid_list():
    uid_list = set()
    if os.path.exists('uid_list.txt'):
        with open('uid_list.txt', 'r') as file:
            uid_list = set(file.read().splitlines())
    return uid_list

def write_uid_list(uid_list):
    with open('uid_list.txt', 'w') as file:
        file.write('\n'.join(uid_list))

def move_to_folder(uid, client_socket, folder):
    client_socket.sendall(f'DELE {uid}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
    folder_file_path = os.path.join(folder, f'{folder.lower()}_email_{uid}.txt')

    with open(file_path, 'r', encoding='utf-8') as original_email:
        email_content = original_email.read()

    with open(folder_file_path, 'w', encoding='utf-8') as folder_email:
        folder_email.write(email_content)

    os.remove(file_path)

    print(f"Email with UID {uid} is moved to {folder} folder.")

def apply_filters(uid, email_content, client_socket):
    for folder, keywords in FILTER_RULES.items():
        if any(keyword.lower() in email_content.lower() for keyword in keywords):
            move_to_folder(uid, client_socket, folder)

    if any(keyword.lower() in email_content.lower() for keyword in SPAM_KEYWORDS):
        move_to_folder(uid, client_socket, SPAM_FOLDER)

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ip_address = socket.gethostbyname(POP3_SERVER)
        print(f"The IP address of {POP3_SERVER} is {ip_address}")
    except socket.gaierror as e:
        print(f"Error resolving {POP3_SERVER}: {e}")

    client_socket.connect((POP3_SERVER, POP3_PORT))

    client_socket.sendall(f'USER {USERNAME}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.sendall(f'PASS {PASSWORD}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    downloaded_uids = read_uid_list()

    client_socket.sendall(b'STAT\r\n')
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.sendall(b'UIDL\r\n')
    response = client_socket.recv(1024).decode()
    uid_list_response = response.splitlines()[1:]
    print(uid_list_response)

    for uid_response in uid_list_response:
        uid = uid_response.split()[0]
        if uid not in downloaded_uids:
            client_socket.sendall(f'RETR {uid}\r\n'.encode())
            email_content = client_socket.recv(4096).decode()
            print(email_content)

            apply_filters(uid, email_content, client_socket)

            downloaded_uids.add(uid)

    write_uid_list(downloaded_uids)

    client_socket.sendall(b'QUIT\r\n')
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.close()

if __name__ == "__main__":
    main()
