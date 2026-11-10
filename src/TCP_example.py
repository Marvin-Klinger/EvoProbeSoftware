import socket
from multiprocessing import Process


def server_programm():
    host = "127.0.0.1"
    port = 5000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    conn, address = server_socket.accept()
    while True:
        raw = conn.recv(1024)
        if not raw:
            break
        try:
            data = raw.decode('utf-8')
            response = process_request(data)
        except UnicodeDecodeError:
            print(f"Received non-UTF-8 data from {address}")
            response = "ERROR"
        conn.sendall(response.encode())

    conn.close()
    server_socket.close()


def process_request(request):
    lines = request.split('\n')
    match lines[0]:
        case "get_temp":
            return "OK\n456"
        case "set_temp":
            print(f"setting temp to {lines[1]}")
            return "OK"
        case _:
            return "ERROR"


def client_program():
    host = '127.0.0.1'
    port = 5000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    message = get_input()

    while message != 'exit':
        client_socket.sendall(message.encode())  # send message
        raw = client_socket.recv(1024)  # read up to 1024 bytes; larger messages require multiple recv() calls
        if not raw:
            break
        try:
            data = raw.decode('utf-8')
        except UnicodeDecodeError:
            print("Received non-UTF-8 data from server")
            continue

        print("Received from server:\n" + data)

        message = get_input()

    client_socket.close()


def get_input():
    message = ""
    new_line = input(" -> ")
    while new_line != "":
        message += new_line + "\n"
        new_line = input(" -> ")
    return message.strip()


'''
[Client]
Request:
{function name}
{parameter1},{parameter2},... [optional] (types implied by function)

[Server]
Answer:
{Statuscode} (OK, ERROR)
{return1},{return2},... [optional] (types implied by Request)
'''


if __name__ == "__main__":
    p = Process(target=server_programm)
    p.start()

    client_program()
