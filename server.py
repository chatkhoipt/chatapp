import socket
import threading
import time
from datetime import datetime, timedelta

# Server Configuration
SERVER_IP = '0.0.0.0'
SERVER_PORT = 9999
clients = {}  # Store client sockets with their names and hostnames
admin_socket = None  # Track the admin socket
banned_hostnames = {}  # Dict to store banned hostnames with expiration times

# Broadcast message to all clients (including admin if connected)
def broadcast_message(message, include_admin=True):
    # Send to regular clients
    for client_socket in list(clients.keys()):
        try:
            client_socket.send(message.encode('utf-8'))
        except:
            client_socket.close()
            del clients[client_socket]

    # Send to admin, if connected
    if include_admin and admin_socket:
        try:
            admin_socket.send(message.encode('utf-8'))
        except:
            pass

# Broadcast user list to admin
def update_admin_with_user_list():
    if admin_socket:
        user_list = "USER_LIST: " + ", ".join(f"{name} (Hostname: {hostname})" for (name, hostname) in clients.values())
        try:
            admin_socket.send(user_list.encode('utf-8'))
        except:
            pass

# Handle individual client connection
def handle_client(client_socket, client_address):
    global admin_socket
    try:
        # Receive client information (either username:hostname or admin)
        client_info = client_socket.recv(1024).decode('utf-8')

        if client_info == "/admin":  # Admin connection
            print("Admin connected.")
            admin_socket = client_socket
            handle_admin_commands(admin_socket)
        else:
            # Regular client connection (username:hostname)
            client_name, client_hostname = client_info.split(":")

            # Check if the hostname is banned and if the ban is still active
            if client_hostname in banned_hostnames:
                ban_end_time = banned_hostnames[client_hostname]
                if datetime.now() < ban_end_time:
                    client_socket.send(f"You are banned from this server until {ban_end_time}.".encode('utf-8'))
                    client_socket.close()
                    return  # Exit function if the user is still banned
                else:
                    del banned_hostnames[client_hostname]  # Lift the ban if time has expired

            # Normal client behavior
            clients[client_socket] = (client_name, client_hostname)
            
            # Notify all clients and admin that a new user has joined
            welcome_message = f"SYSTEM: {client_name} has joined the chat!"
            broadcast_message(f"{welcome_message}")
            update_admin_with_user_list()  # Send updated user list to admin
            print(welcome_message)

            # Handle communication with the client
            while True:
                try:
                    # Receive messages from the client
                    message = client_socket.recv(1024).decode('utf-8')
                    if message:
                        broadcast_message(f"{client_name}: {message}")
                except:
                    # Handle client disconnection
                    if client_socket in clients:
                        print(f"{client_name} has disconnected.")
                        broadcast_message(f"SYSTEM: {client_name} has left the chat.")
                        del clients[client_socket]
                        update_admin_with_user_list()  # Send updated user list to admin
                    client_socket.close()
                    break
    except:
        pass

# Handle admin commands in a loop
def handle_admin_commands(admin_socket):
    while True:
        try:
            message = admin_socket.recv(1024).decode('utf-8')
            if message.startswith("/admin"):
                handle_admin_command(message)
            else:
                # Admin can chat just like regular users
                broadcast_message(f"ADMIN: {message}")
        except:
            break

# Ban a client by hostname for a specified duration
def ban_hostname(client_socket, client_name, client_hostname, duration_seconds):
    ban_end_time = datetime.now() + timedelta(seconds=duration_seconds)
    banned_hostnames[client_hostname] = ban_end_time

    # Send ban message to client before kicking them
    ban_message = f"SYSTEM: You have been banned from the server for {str(timedelta(seconds=duration_seconds))}. The ban will expire at {ban_end_time}."
    try:
        client_socket.send(ban_message.encode('utf-8'))
    except:
        pass

    # Kick the user after sending the ban message
    kick_client(client_socket, reason="ban")

    print(f"Banned Hostname: {client_hostname} until {ban_end_time}")

# Kick a client (disconnect only, with an optional reason)
def kick_client(client_socket, reason="kick"):
    try:
        if reason == "ban":
            client_socket.send("You have been banned by the admin.".encode('utf-8'))
        else:
            client_socket.send("You have been kicked by the admin.".encode('utf-8'))

        client_socket.close()
        if client_socket in clients:
            del clients[client_socket]
        update_admin_with_user_list()  # Update admin with new user list
    except:
        pass

def handle_admin_command(message):
    command = message.split(" ", 2)

    if command[0] == "/admin_list":  # List all online users
        update_admin_with_user_list()

    elif command[0] == "/admin_kick":
        target_name = command[1]
        for client_socket, (client_name, hostname) in clients.items():
            if client_name == target_name:
                kick_client(client_socket)
                broadcast_message(f"SYSTEM: {client_name} has been kicked by the admin.")
                return

    elif command[0] == "/admin_ban_hostname":
        target_name = command[1]
        duration_str = command[2]  # Expected to be in the format "HH:MM:SS"
        duration_parts = list(map(int, duration_str.split(":")))
        duration_seconds = duration_parts[0] * 3600 + duration_parts[1] * 60 + duration_parts[2]

        for client_socket, (client_name, hostname) in clients.items():
            if client_name == target_name:
                ban_hostname(client_socket, client_name, hostname, duration_seconds)  # Ban for the specified duration
                broadcast_message(f"SYSTEM: {client_name}'s device has been banned by the admin for {duration_str}.")
                return

    elif command[0] == "/admin_warning":
        warning_message = command[1]  # The warning message to send to clients
        broadcast_message(f"WARNING: {warning_message}", include_admin=False)  # Send to all clients

# Set up the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(26)  # Listen for up to 26 connections

print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

# Accept incoming connections
while True:
    client_socket, client_address = server_socket.accept()
    print(f"New connection from {client_address}")
    
    # Start a new thread to handle the client's communication (either admin or normal)
    threading.Thread(target=handle_client, args=(client_socket, client_address)).start()
