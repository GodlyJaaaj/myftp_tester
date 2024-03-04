import os
import socket
import sys
import threading
import time
import colorama


def prep_line(line):
    if line.endswith("\n"):
        line = line[:-1]
        line += "\r\n"
    elif not line.endswith("\n"):
        line += "\r\n"
    return line


class Client:
    def __init__(self, host, port, file):
        self.host = host
        self.port = port
        self.file = file

        self.socket = None

        self.all_data = b""

        self.data_host = None
        self.data_port = None
        self.data_socket = None

        self.remaining = b""
        self.response = b""

    def connect_to_server(self, timeout=5):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.socket.connect((self.host, self.port)):
            print(f"{colorama.Fore.RED}COULD NOT CONNECT "
                  f"TO SERVER {self.host} {self.port}", file=sys.stderr)
            raise ConnectionError
        print(f"{colorama.Fore.GREEN}CONNECTED TO SERVER "
              f"{self.host} {self.port} {colorama.Style.RESET_ALL}")
        self.socket.settimeout(timeout)

    def end_connection(self):
        self.socket.close()
        if self.data_socket is not None:
            self.data_socket.close()

    def handle_data(self):
        if self.data_socket is None:
            print(f"{colorama.Fore.RED}[DATA SOCKET] NOT OPENED")
            return
        buffer = b""
        while True:
            data = self.data_socket.recv(1024)
            if not data:
                break
            buffer += data
        print(f"{colorama.Fore.MAGENTA}[DATA SOCKET] RECEIVED DATA:\n"
              f"[{colorama.Fore.GREEN}{buffer.decode()}"
              f"{colorama.Fore.MAGENTA}]")
        self.data_socket.close()
        self.data_socket = None

    def handle_pasv(self):
        self.response, self.remaining = self.get_and_show_response()
        pasv_mode = self.response.decode().split("(")[1].split(")")[0].split(
            ",")
        if len(pasv_mode) != 6:
            print(f"{colorama.Fore.RED}WRONG PARAMS: {pasv_mode}"
                  f"{colorama.Style.RESET_ALL}")
            raise ValueError
        self.data_host = ".".join(pasv_mode[:4])
        self.data_port = int(pasv_mode[4]) * 256 + int(pasv_mode[5])

        print(f"{colorama.Fore.LIGHTBLUE_EX}[DATA SOCKET] TRYING TO OPEN")
        time.sleep(0.5)
        if not self.data_host or not self.data_port:
            print(f"{colorama.Fore.RED}[DATA SOCKET] NO DATA HOST OR PORT"
                  f"{colorama.Style.RESET_ALL}")
            raise ValueError
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.data_socket.connect((self.data_host, self.data_port)):
            print(f"{colorama.Fore.RED}[DATA SOCKET] COULD NOT CONNECT TO "
                  f"DATA SOCKET {self.data_host} {self.data_port}"
                  f"{colorama.Style.RESET_ALL}")
            raise ConnectionError

    def get_reponse(self):
        self.response = self.remaining
        self.remaining = b""
        while not b"\r\n" in self.response:
            try:
                data = self.socket.recv(1024)
            except socket.timeout as e:
                print(f"{colorama.Fore.RED}SERVER TIMEOUT"
                      f"{colorama.Style.RESET_ALL}")
                raise e
            self.all_data += data
            self.response += data
            if b"\r\n" in self.response:
                self.response, self.remaining = self.response.split(b"\r\n", 1)
                self.response += b"\r\n"
                break
        return self.response, self.remaining

    def get_and_show_response(self):
        try:
            self.response, self.remaining = self.get_reponse()
        except socket.timeout as e:
            raise e
        try:
            print(f"{colorama.Fore.WHITE}R: [{self.response.decode().strip()}]"
                  f"{colorama.Style.RESET_ALL}")
        except UnicodeDecodeError:
            print(f"{colorama.Fore.RED}[DECODE_ERR] R: [{self.response}]"
                  f"{colorama.Style.RESET_ALL}")
        return self.response, self.remaining

    def check_connection(self):
        try:
            self.response, self.remaining = self.get_reponse()
            print(f"{colorama.Style.DIM}R: [{self.response.decode().strip()}]"
                  f"{colorama.Style.RESET_ALL}")
            if self.remaining:
                print(f"{colorama.Fore.RED}remaining: "
                      f"[{self.remaining.decode().strip()}]"
                      f"{colorama.Style.RESET_ALL}")
        except socket.timeout as e:
            print(f"{colorama.Fore.RED}SERVER TIMEOUT"
                  f"{colorama.Style.RESET_ALL}")
            raise e

    def send_command(self, command):
        print(f"{colorama.Fore.MAGENTA}", end="")
        print(f"S: {command.encode()}")
        self.socket.send(command.encode())
        time.sleep(0.1)
        print(f"{colorama.Style.RESET_ALL}", end="")

    def handle_list(self):
        self.response, self.remaining = self.get_and_show_response()
        if "150" in self.response.decode():
            thread = threading.Thread(target=self.handle_data)
            thread.start()
            thread.join()
            self.response, self.remaining = self.get_and_show_response()

    def handle_RETR(self):
        self.response, self.remaining = self.get_and_show_response()
        if "150" in self.response.decode():
            thread = threading.Thread(target=self.handle_data)
            thread.start()
            thread.join()
            self.response, self.remaining = self.get_and_show_response()

    def handle_STOR(self):
        self.response, self.remaining = self.get_and_show_response()
        if "150" in self.response.decode():
            self.data_socket.send(b"Dummy data")
            self.data_socket.close()
            self.data_socket = None
            self.response, self.remaining = self.get_and_show_response()

    def handle_commands(self, command):
        stripped_command = command.strip().split(" ")[0]
        try:
            match stripped_command:
                case "USER" | "PASS" | "CWD" | "CDUP" \
                     | "DELE" | "PWD" | "NOOP" | "QUIT" \
                     | "HELP":
                    self.send_command(command)
                    self.get_and_show_response()
                    if stripped_command == "QUIT":
                        self.end_connection()
                case "PASV":
                    self.send_command(command)
                    self.handle_pasv()
                case "LIST":
                    self.send_command(command)
                    self.handle_list()
                case "RETR":
                    self.send_command(command)
                    self.handle_RETR()
                case "STOR":
                    self.send_command(command)
                    self.handle_STOR()
                case "PORT":
                    self.handle_PORT()
                case _:
                    print(f"{colorama.Fore.RED}UNKNOWN COMMAND {command}"
                          f"{colorama.Style.RESET_ALL}", end="")
                    self.send_command(command)
                    self.get_and_show_response()
        except BaseException as e:
            raise e

    def client_loop(self):
        try:
            self.check_connection()
            with open(self.file) as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    line = prep_line(line)
                    self.handle_commands(line)

        except socket.timeout:
            print(f"{colorama.Fore.RED}")
            print(f"last response: [{self.response.decode().strip()}]")
            print(f"last remain: [{self.remaining.decode().strip()}]")
            print(f"{colorama.Style.RESET_ALL}")

    def dump_data(self):
        file_name = "dump.txt"
        print(colorama.Fore.LIGHTBLUE_EX, end="")
        print(colorama.Style.RESET_ALL, end="")
        with open(file_name, "wb") as f:
            f.write(self.all_data)
        print(f"{colorama.Fore.LIGHTBLUE_EX}"
              f"Check {file_name} for all data"
              f"{colorama.Style.RESET_ALL}")

    def handle_PORT(self):
        client_socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket_server.bind(('', 0))
        client_socket_server.listen(1)
        client_socket_server.settimeout(5)

        self.data_host, _ = self.socket.getsockname()
        self.data_port = client_socket_server.getsockname()[1]

        print(f"{colorama.Fore.YELLOW}"
              f"[HANDLE_PORT] Host: {self.data_host}", end="")
        print(f" {self.data_port}{colorama.Style.RESET_ALL}")

        host = ','.join(map(str, map(int, self.data_host.split('.'))))
        port = ','.join(map(str, divmod(self.data_port, 256)))

        self.send_command(f"PORT {host},{port}\r\n")
        try:
            self.data_socket = client_socket_server.accept()[0]
            self.response, self.remaining = self.get_and_show_response()
            if "200" not in self.response.decode():
                print(f"{colorama.Fore.RED}PORT COMMAND FAILED"
                      f"{colorama.Style.RESET_ALL}")
                raise ValueError
        except socket.timeout:
            print(f"{colorama.Fore.RED}DATA SOCKET TIMEOUT"
                  f"{colorama.Style.RESET_ALL}")
            raise ConnectionError


def start_client(host, port, file):
    client: Client = Client(host, port, file)
    try:
        client.connect_to_server()
    except ConnectionError:
        print(
            f"{colorama.Fore.RED}COULD NOT "
            f"CONNECT TO SERVER{colorama.Style.RESET_ALL}")
        return
    time.sleep(0.1)
    client.client_loop()
    client.end_connection()
    client.dump_data()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"{colorama.Fore.RED}Usage: {sys.argv[0]} <host> <port> <file>")
        sys.exit(1)

    if not os.access(sys.argv[3], os.R_OK):
        print(
            f"{colorama.Fore.RED}File {sys.argv[3]} not found or not readable")
        sys.exit(1)

    start_client(sys.argv[1], int(sys.argv[2]), sys.argv[3])
