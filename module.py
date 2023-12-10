import socket
import os

# Thông tin cấu hình
POP3_SERVER = 'pop.example.com'
POP3_PORT = 995
USERNAME = 'your_email@example.com'
PASSWORD = 'your_email_password'
DOWNLOAD_PATH = 'downloaded_emails'
SPAM_FOLDER = 'spam_emails'

def create_spam_folder():
    if not os.path.exists(SPAM_FOLDER):
        os.makedirs(SPAM_FOLDER)
        print("Thu muc Spam da duoc tao")
        


# Tạo thư mục để lưu trữ email tải về và thư mục Spam
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)
if not os.path.exists(SPAM_FOLDER):
    os.makedirs(SPAM_FOLDER)

def download_email(uid, client_socket):
    # Gửi lệnh để tải nội dung email theo UID
    client_socket.sendall(f'RETR {uid}\r\n'.encode())

    # Nhận phản hồi từ server
    response = client_socket.recv(1024).decode()
    print(response)

    # Đọc dữ liệu từ server và lưu vào tệp
    email_content = b''
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        email_content += data

    # Lưu nội dung email vào tệp
    file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
    with open(file_path, 'wb') as email_file:
        email_file.write(email_content)

    return file_path

def move_to_spam(uid, client_socket):
    client_socket.sendall(f'DELE {uid}\r\n'.encode())
    response =client_socket.recv(1024).decode()
    print(response)
    
    file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
    spam_file_path = os.path.join(SPAM_FOLDER, f'spam_email.{uid}.txt')
    
    with open(file_path, 'r', encoding = 'utf-8') as original_email:
        email_content = original_email.read()
    with open(spam_file_path, 'w', encoding = 'utf-8') as spam_email:
        spam_email.write(email_content)
        
    os.remove(file_path)
    print(f"Email voi UID {uid} da duoc chuyen toi thu muc Spam.")

def main():
    # Kết nối đến Mail Server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((POP3_SERVER, POP3_PORT))

    # Nhận phản hồi từ server khi kết nối
    response = client_socket.recv(1024).decode()
    print(response)

    # Xác thực đăng nhập
    client_socket.sendall(f'USER {USERNAME}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.sendall(f'PASS {PASSWORD}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    # Lấy danh sách UID
    client_socket.sendall(b'UIDL\r\n')
    response = client_socket.recv(1024).decode()
    uid_list_response = response.splitlines()[1:]  # Bỏ qua dòng đầu tiên chứa thông tin số lượng email
    print(uid_list_response)

    # Lặp qua danh sách UID và xử lý email
    for uid_response in uid_list_response:
        uid = uid_response.split()[0]

        # Kiểm tra xem email đã được tải trước đó hay chưa
        if not os.path.exists(os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')):
            file_path = download_email(uid, client_socket)
            with open(file_path, 'r', encoding='utf-8') as email_file:
                email_content = email_file.read()
                if 'sender@gmail.com' in email_content:
                    move_to_spam(uid, client_socket)
                    print(f"Email voi UID {uid} da duoc di chuyen toi Spam dua tren nguoi gui")
                if 'spam' in email_content.lower():
                    move_to_spam(uid, client_socket)
                    print(f"Email voi UID {uid} da duoc di chuyen toi Spam dua tren chu de(Subject)")
                if'spam_content' in email_content.lower():
                    move_to_spam(uid, client_socket)
                    print(f"Email voi UID {uid} da duoc di chuyen toi Spam dua tren noi dung")
    

    # Đóng kết nối
    client_socket.sendall(b'QUIT\r\n')
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.close()

if __name__ == "__main__":
    create_spam_folder()
    main()
