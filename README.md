# FTP Client

This is a simple FTP client implemented in Python. It supports a variety of FTP commands and can be used to interact with an FTP server.

## Features

- Connect to an FTP server
- Send FTP commands to the server
- Handle server responses
- Support for both active (PORT) and passive (PASV) modes
- File transfer (RETR, STOR)
- Directory navigation (CWD, CDUP)
- File deletion (DELE)
- Current working directory retrieval (PWD)
- Server status check (NOOP)
- Help command (HELP)
- Quit command (QUIT)

## Usage

To use this FTP client, you need to provide the host, port, and a file containing the FTP commands to be executed.

```bash
python tester.py <host> <port> <file>
```

Replace `<host>`, `<port>`, and `<file>` with the actual host, port, and file path.

The file should contain one FTP command per line. The commands will be executed in the order they appear in the file.

## Dependencies

This program uses the following Python libraries:

- `os`
- `socket`
- `multiprocessing`
- `sys`
- `threading`
- `time`
- `colorama`

Make sure to install these dependencies before running the program.
