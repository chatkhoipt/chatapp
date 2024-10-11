import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

# TimeSelectionDialog allows the admin to select hours, minutes, and seconds for the ban duration
class TimeSelectionDialog(simpledialog.Dialog):
    def body(self, master):
        self.title("Select Ban Duration")

        # Create labels for hours, minutes, and seconds
        tk.Label(master, text="Hours:").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(master, text="Minutes:").grid(row=1, column=0, padx=5, pady=5)
        tk.Label(master, text="Seconds:").grid(row=2, column=0, padx=5, pady=5)

        # Spinboxes for selecting hours, minutes, and seconds
        self.hours_spinbox = tk.Spinbox(master, from_=0, to=23, width=5)
        self.hours_spinbox.grid(row=0, column=1, padx=5, pady=5)

        self.minutes_spinbox = tk.Spinbox(master, from_=0, to=59, width=5)
        self.minutes_spinbox.grid(row=1, column=1, padx=5, pady=5)

        self.seconds_spinbox = tk.Spinbox(master, from_=0, to=59, width=5)
        self.seconds_spinbox.grid(row=2, column=1, padx=5, pady=5)

        return self.hours_spinbox  # Initial focus

    def apply(self):
        # Retrieve the values from the spinboxes and return them as a tuple
        self.result = (
            int(self.hours_spinbox.get()),
            int(self.minutes_spinbox.get()),
            int(self.seconds_spinbox.get()),
        )


# Admin GUI App
class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Panel")
        self.root.geometry("600x500")
        self.root.configure(bg="#2c3e50")

        # Chat display area
        self.chat_frame = tk.Frame(self.root, bg="#34495e")
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Chat window for displaying messages
        self.chat_window = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, bg="#ecf0f1", fg="#2c3e50",
                                                     font=("Helvetica", 12))
        self.chat_window.pack(fill=tk.BOTH, expand=True)
        self.chat_window.config(state='disabled')

        # Message entry area
        self.entry_frame = tk.Frame(self.root, bg="#34495e")
        self.entry_frame.pack(fill=tk.X, padx=10, pady=5)

        # Entry box for typing messages
        self.msg_entry = tk.Entry(self.entry_frame, font=("Helvetica", 14))
        self.msg_entry.pack(fill=tk.X, padx=10, pady=5)
        self.msg_entry.bind("<Return>", self.send_message)

        # Admin actions frame
        self.action_frame = tk.Frame(self.root, bg="#34495e")
        self.action_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create buttons for actions
        self.kick_button = tk.Button(self.action_frame, text="Kick Selected", bg="#e74c3c", fg="#ecf0f1",
                                     font=("Helvetica", 12), command=self.kick_user)
        self.kick_button.pack(side=tk.LEFT, padx=10)

        self.ban_button = tk.Button(self.action_frame, text="Ban Selected", bg="#c0392b", fg="#ecf0f1",
                                    font=("Helvetica", 12), command=self.ban_user)
        self.ban_button.pack(side=tk.LEFT, padx=10)

        self.view_users_button = tk.Button(self.action_frame, text="Refresh User List", bg="#16a085", fg="#ecf0f1",
                                           font=("Helvetica", 12), command=self.view_users)
        self.view_users_button.pack(side=tk.LEFT, padx=10)

        # Adding a warning button
        self.warning_button = tk.Button(self.action_frame, text="Send Warning", bg="#f39c12", fg="#ecf0f1",
                                        font=("Helvetica", 12), command=self.send_warning)
        self.warning_button.pack(side=tk.LEFT, padx=10)

        # User list area
        self.user_list_frame = tk.Frame(self.root, bg="#2c3e50")
        self.user_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.user_list_label = tk.Label(self.user_list_frame, text="Online Users", bg="#2c3e50", fg="#ecf0f1",
                                        font=("Helvetica", 14))
        self.user_list_label.pack(anchor="w", padx=10)

        # Scrollable user list
        self.user_listbox = tk.Listbox(self.user_list_frame, font=("Helvetica", 12), height=8)
        self.user_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Connect to the server
        self.admin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.admin_socket.connect(('myfirstweb.ddns.net', 9999))  # Server IP
        except:
            messagebox.showerror("Connection Error", "Unable to connect to the server")
            self.root.quit()

        # Identify as admin
        self.admin_socket.send("/admin".encode('utf-8'))

        # Start a thread to receive messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def send_message(self, event=None):
        """Send a message to the chat like a normal user"""
        message = self.msg_entry.get()
        if message.strip():
            self.admin_socket.send(message.encode('utf-8'))
            self.msg_entry.delete(0, tk.END)

    def view_users(self):
        """Request the list of online users"""
        self.admin_socket.send("/admin_list".encode('utf-8'))

    def kick_user(self):
        """Kick the selected user"""
        selected_user = self.user_listbox.get(tk.ACTIVE)
        if selected_user:
            target_name = selected_user.split(" ")[0]
            command = f"/admin_kick {target_name}"
            self.admin_socket.send(command.encode('utf-8'))

    def ban_user(self):
        """Ban the selected user by hostname"""
        selected_user = self.user_listbox.get(tk.ACTIVE)
        if selected_user:
            target_name = selected_user.split(" ")[0]

            # Open the time selection dialog
            dialog = TimeSelectionDialog(self.root)
            if dialog.result:
                hours, minutes, seconds = dialog.result
                ban_duration = f"{hours:02}:{minutes:02}:{seconds:02}"

                # Send the ban command with the duration to the server
                command = f"/admin_ban_hostname {target_name} {ban_duration}"
                self.admin_socket.send(command.encode('utf-8'))

    def send_warning(self):
        """Send a warning message to all users"""
        warning_message = simpledialog.askstring("Warning", "Enter warning message:", parent=self.root)
        if warning_message:
            command = f"/admin_warning {warning_message}"
            self.admin_socket.send(command.encode('utf-8'))

    def receive_messages(self):
        """Receive messages and handle updates"""
        while True:
            try:
                message = self.admin_socket.recv(1024).decode('utf-8')
                if message.startswith("USER_LIST:"):
                    self.update_user_list(message)
                else:
                    self.chat_window.config(state='normal')
                    self.chat_window.insert(tk.END, message + '\n')
                    self.chat_window.config(state='disabled')
                    self.chat_window.yview(tk.END)
            except:
                break

    def update_user_list(self, message):
        """Update the scrollable list with users"""
        self.user_listbox.delete(0, tk.END)
        user_list = message.replace("USER_LIST: ", "").split(", ")
        for user in user_list:
            self.user_listbox.insert(tk.END, user)


# Main loop for the admin panel window
root = tk.Tk()
app = AdminApp(root)
root.mainloop()
