# === client.py ===
# Client program that connects to a server and performs file system operations
# Operations include: uploading files, downloading files, and executing commands remotely

import socket  # Imports the socket library to handle TCP communication
import os      # Imports the OS library to work with the file system (checking if files exist, etc.)

# === Configuration ===
HEADER = 64  # Number of bytes reserved to tell how big the next message will be
PORT = 5050  # The port number that the server is listening on
FORMAT = 'utf-8'  # Encoding format used to convert messages into bytes and back into strings
DISCONNECT_MESSAGE = "!DISCONNECT"  # Special message used to tell the server we want to disconnect
SERVER = '164.92.127.180'  # The IP address of the server we want to connect to (must be changed to your server’s real IP)
ADDR = (SERVER, PORT)  # Combine server IP and port into one address tuple

# === Socket Setup ===
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket (AF_INET = IPv4, SOCK_STREAM = TCP)
client.connect(ADDR)  # Connect the client socket to the server address

# === Helper Function to Send a Command Message with Framed Length ===
def send_msg(msg):
    # This function sends a message to the server properly framed

    message = msg.encode(FORMAT)  # Encode the text message into bytes
    msg_length = len(message)  # Find out how many bytes long the message is
    send_length = str(msg_length).encode(FORMAT)  # Encode the message length itself into bytes
    send_length += b' ' * (HEADER - len(send_length))  # Pad the length to 64 bytes (so server knows exactly where length ends)
    client.send(send_length)  # Send the length of the message first
    client.send(message)  # Then send the actual message itself

# === Upload File to Server ===
def upload_file(filename):
    # This function uploads a file from client to server

    if not os.path.isfile(filename):
        # Check if the file actually exists
        print(f"[!] File not found: {filename}")
        return  # Exit if the file does not exist

    send_msg(f"UPLOAD {filename}")  # Send a message to server that we want to upload and pass filename
    with open(filename, 'rb') as f:
        # Open the file in binary read mode
        client.sendall(f.read())  # Send all the file contents to the server
    client.send(b"__END__")  # After file contents, send special marker to show file is fully sent
    print("[+] File uploaded.")  # Confirm to user that upload is done

# === Download File from Server ===
def download_file(filename):
    # This function downloads a file from server to client

    send_msg(f"DOWNLOAD {filename}")  # Tell server we want to download a particular file
    with open(filename, 'wb') as f:
        # Open a new file in binary write mode to save incoming data
        while True:
            data = client.recv(1024)  # Receive chunks of 1024 bytes from server
            if b"__END__" in data:
                # If we detect the special "__END__" marker, it means file is done
                f.write(data.replace(b"__END__", b""))  # Remove "__END__" and write final data
                break  # Exit the loop after download completes
            f.write(data)  # Otherwise, keep writing data chunks to the file
    print("[+] File downloaded.")  # Confirm to user that download is finished

# === Main Command Loop ===
def main():
    # This function is the main interaction loop where user types commands

    while True:
        cmd = input(">>> ").strip()  # Wait for user to type a command and remove extra spaces
        if cmd == "quit":
            # If user types "quit", disconnect from server
            send_msg(DISCONNECT_MESSAGE)  # Send special disconnect message
            break  # Break the loop and close client
        elif cmd.startswith("upload "):
            # If user types upload followed by filename, upload that file
            filename = cmd.split(" ", 1)[1]  # Split command and get filename
            upload_file(filename)  # Call upload function
        elif cmd.startswith("download "):
            # If user types download followed by filename, download that file
            filename = cmd.split(" ", 1)[1]  # Split command and get filename
            download_file(filename)  # Call download function
        else:
            # Otherwise, assume the command is a shell command (mkdir, dir, mv, etc.)
            send_msg(cmd)  # Send the command to server
            response = client.recv(2048).decode(FORMAT)  # Receive the server’s response and decode it
            print(response)  # Show server’s response to user

    client.close()  # After loop exits, close the socket connection
    print("[*] Disconnected from server.")  # Notify user that client has exited

if __name__ == "__main__":
    main()  # If we are running this script directly, call the main() function
