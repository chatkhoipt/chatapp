import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog
import tkinter.messagebox

# Client GUI App
class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat App")
        
        # Chat window
        self.chat_window = scrolledtext.ScrolledText(self.root)
        self.chat_window.pack(padx=10, pady=10)
        self.chat_window.config(state='disabled')  # Read-only

        # Message entry field
        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack(fill=tk.X, padx=10, pady=5)
        self.msg_entry.bind("<Return>", self.send_message)

        # Connect to server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('myfirstweb.ddns.net', 9999))  # Server IP and port

        # Ask for the client's name
        self.name = simpledialog.askstring("Name", "Enter your name:", parent=self.root)
        
        # Get computer name (hostname)
        self.computer_name = socket.gethostname()

        if self.name and self.computer_name:
            # Send both the username and the computer name (hostname) to the server
            self.client_socket.send(f"{self.name}:{self.computer_name}".encode('utf-8'))

        # Start a thread to listen for incoming messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def send_message(self, event):
        message = self.msg_entry.get()
        self.client_socket.send(message.encode('utf-8'))
        self.msg_entry.delete(0, tk.END)

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                
                if "You have been banned" in message:
                    self.show_ban_popup(message)  # Show the ban message as a pop-up
                
                elif message.startswith("WARNING:"):
                    warning_text = message.replace("WARNING: ", "")
                    self.show_warning_popup(warning_text)  # Show warning pop-up

                else:
                    self.chat_window.config(state='normal')
                    self.chat_window.insert(tk.END, message + '\n')
                    self.chat_window.config(state='disabled')
                    self.chat_window.yview(tk.END)  # Auto scroll to the bottom
            except:
                break

    # Method to display the ban message as a pop-up
    def show_ban_popup(self, ban_message):
        tkinter.messagebox.showerror("Banned", ban_message)  # On-top ban window

    # Method to display the warning as a pop-up
    def show_warning_popup(self, warning_text):
        tkinter.messagebox.showwarning("Warning", warning_text)  # On-top warning window

# Main loop for the chat window
root = tk.Tk()
app = ChatApp(root)
root.mainloop()
