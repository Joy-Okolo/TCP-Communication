# === server.py ===
# This is the server program that accepts multiple client connections
# It handles file uploads, file downloads, and executes commands like mkdir, mv, dir remotely

import socket  # Import socket library for network communication
import threading  # Import threading to allow multiple clients to connect at the same time
import os  # Import OS library for file handling (check files, write files)
import subprocess  # Import subprocess to run system shell commands (mkdir, mv, dir, etc.)

# === Configuration ===
HEADER = 64  # Define how many bytes to use to specify the length of a message
PORT = 5050  # Port where the server will listen for client connections
SERVER = socket.gethostbyname(socket.gethostname())
# Automatically find the server's IP address on the local network
ADDR = (SERVER, PORT)  # Create a tuple combining server IP and port
FORMAT = 'utf-8'  # Encoding format for messages (text communication)
DISCONNECT_MESSAGE = "!DISCONNECT"  # Special message used to indicate client wants to disconnect

# === Create TCP Socket ===
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of address
server.bind(ADDR)

# === Handle a Single Client Connection ===
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True

    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if not msg_length:
            continue
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)

        print(f"[{addr}] Sent: {msg}")  # 👈 LOG EACH MESSAGE HERE

        if msg == DISCONNECT_MESSAGE:
            connected = False
            print(f"[DISCONNECT] {addr} disconnected.")

        elif msg.startswith("UPLOAD "):
            filename = msg.split(" ", 1)[1]
            with open(filename, 'wb') as f:
                while True:
                    data = conn.recv(1024)
                    if b"__END__" in data:
                        f.write(data.replace(b"__END__", b""))
                        break
                    f.write(data)
            print(f"[UPLOAD] {addr} sent file: {filename}")

        elif msg.startswith("DOWNLOAD "):
            filename = msg.split(" ", 1)[1]
            if os.path.isfile(filename):
                with open(filename, 'rb') as f:
                    conn.sendall(f.read())
                conn.send(b"__END__")
                print(f"[DOWNLOAD] Sent {filename} to {addr}")
            else:
                conn.send("File not found.__END__".encode())
                print(f"[ERROR] {addr} requested missing file: {filename}")

        else:
            try:
                output = subprocess.check_output(msg, shell=True, stderr=subprocess.STDOUT)
                conn.send(output if output else b"[+] Command executed.\n")
                print(f"[CMD] {addr} ran: {msg}")
            except subprocess.CalledProcessError as e:
                conn.send(e.output)
                print(f"[CMD ERROR] {addr} - {msg} failed")

    conn.close()

# === Start Listening for Clients ===
def start():
    server.listen()
    # Start listening for incoming connections
    print(f"[LISTENING] Server is listening on {SERVER}")
    # Print that the server is now actively listening

    while True:
        conn, addr = server.accept()
        # Accept a new client connection (returns connection socket and client address)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        # Start a new thread to handle this client separately
        thread.start()
        # Begin the thread
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        # Print how many clients are currently connected


print("[STARTING] Server is starting...")
# Initial message when the server script is launched

start()
# Call the start function to begin listening for clients
