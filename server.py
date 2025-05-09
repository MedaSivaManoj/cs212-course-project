# Importing required libraries
import socket                           # For network communication
import tkinter as tk                    # For creating the graphical user interface (GUI)
from tkinter import simpledialog        # For showing simple input dialog boxes
from threading import Thread            # For handling multiple threads (e.g., receiving data while playing)
import time                             # For handling time-related operations
from datetime import datetime           # For working with date and time

# Define host and port for the server
HOST = '127.0.0.1'                      # Localhost, meaning this will run only on this machine
PORT = 5000                             # Port number to listen for incoming connections

# The TicTacToeServer class handles all the server-side logic
class TicTacToeServer:
    def __init__(self):                 # Initialize the server and set up GUI
        # Initialize tkinter window
        self.window = tk.Tk()
        self.window.title("Server - Tic Tac Toe (X)")                               # Set the window title
        self.player_name = simpledialog.askstring("Name", "Enter your name:")       # Ask the server player for their name
        self.client_name = "Client"                                                 # Set default name for client
        self.create_widgets()                                                       # Create the game board and UI elements

        # Set up the socket for network communication
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)           # Create a TCP socket
        self.sock.bind((HOST, PORT))                                            # Bind the socket to the address (host, port)
        self.sock.listen(1)                                                     # Allow the server to listen for 1 incoming connection
        self.conn, _ = self.sock.accept()                                       # Accept the incoming connection and create a new socket connection
        self.conn.sendall(f"NAME {self.player_name}".encode())                  # Send the player's name to the client

        self.client_name = self.conn.recv(1024).decode().split("NAME ")[-1]     # Receive the client's name

        # Set up the chat log file
        self.chat_log_path = "chatlog.txt"
        self.reset_game()                           # Reset the game to the initial state
        self.start_game_timer()                     # Start the game timer
        # Start the thread to handle incoming data from the client
        Thread(target=self.receive_data).start()

        self.window.mainloop()                      # Start the tkinter event loop to run the GUI

    def create_widgets(self):                       # Create the widgets for the GUI
        self.window.configure(bg="#f0f0f0")         # Set the background color of the window

        self.board_frame = tk.Frame(self.window, bg="#f0f0f0")      # Create a frame to hold the game board
        self.board_frame.pack()                                     # Add the frame to the window

        self.buttons = []                           # List to hold the button references for the game board
        # Create 9 buttons for the Tic Tac Toe grid
        for i in range(9):
            btn = tk.Button(self.board_frame, text="", font=("Arial", 24), width=5, height=2,command=lambda i=i: self.make_move(i), bg="white", fg="black")
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)      # Position the buttons in a 3x3 grid
            self.buttons.append(btn)                                # Add each button to the list

        # Create a label to show the current game status
        self.status = tk.Label(self.window, text="Your turn", font=("Arial", 14), bg="#f0f0f0", fg="blue")
        self.status.pack()                                          # Add the status label to the window

        # Create a label to show the remaining time
        self.timer_label = tk.Label(self.window, text="Time left: 60", font=("Arial", 12), bg="#f0f0f0")
        self.timer_label.pack()                                     # Add the timer label to the window

        # Create a label to show the total game time elapsed
        self.game_time_label = tk.Label(self.window, text="Game time: 0s", font=("Arial", 12), bg="#f0f0f0")
        self.game_time_label.pack()                                 # Add the game time label to the window

        # Create a chat log area to display messages between the server and client
        self.chat_log = tk.Text(self.window, height=10, width=50, state='disabled', bg="#e6f2ff")
        self.chat_log.pack(pady=5)                                  # Add the chat log area to the window

        # Create a text entry box for the player to type messages
        self.chat_entry = tk.Entry(self.window, width=40)
        self.chat_entry.pack(side=tk.LEFT, padx=5)
        # Create a button to send messages
        self.send_button = tk.Button(self.window, text="Send Msg", command=self.send_chat)
        self.send_button.pack(side=tk.LEFT)                         # Add the send button to the window

        # Create a reset button to restart the game
        self.reset_button = tk.Button(self.window, text="Reset Game", command=self.send_reset)
        self.reset_button.pack(pady=5)                              # Add the reset button to the window

    # Reset the game to the initial state
        self.timer_thread = None  # NEW: Thread reference for timer
        self.timer_running = False  # NEW: Control flag for timer

    def reset_game(self):  
        self.board = [""] * 9                   # Initialize the game board with empty spaces
        self.turn = True                        # Set the server (X) to start the game
        self.time_left = 60                     # Set the initial time to 60 seconds
        self.game_start_time = time.time()      # Record the game start time
        self.stop_timers = False                # Flag to stop the timers when the game ends
        # Reset the buttons to be enabled and empty
        for btn in self.buttons:
            btn.config(text="", state="normal")
        self.status.config(text="Your turn", fg="blue")     # Set the status to indicate it's the server's turn
        self.chat_log.config(state='normal')                # Enable chat log for clearing
        self.chat_log.delete("1.0", tk.END)                 # Clear the chat log
        self.chat_log.config(state='disabled')              # Disable chat log to prevent editing

        # Start the turn timer only for your turn
        if self.turn:
            self.timer_running = True
            self.timer_thread = Thread(target=self.start_turn_timer)
            self.timer_thread.start()
        # Start the game timer
        self.start_game_timer()

    # Handle the player's move
    def make_move(self, i):                                     
        if self.turn and self.board[i] == "":                                   # If it's the player's turn and the spot is empty
            self.board[i] = "X"                                                 # Mark the spot with an X
            self.buttons[i].config(text="X", state="disabled")                  # Disable the button to prevent further clicks
            self.conn.sendall(f"MOVE {i}".encode())                             # Send the move to the client
            self.turn = False                                                   # It's now the client's turn
            self.timer_running = False                                      # Stop timer after move
            self.status.config(text="Waiting for opponent move", fg="red")      # Update the status
            self.check_winner("X")                                              # Check if the server (X) has won

     # Continuously receive data from the client
    def receive_data(self): 
        while True:
            try:
                data = self.conn.recv(1024).decode()                    # Receive data from the client
                if data.startswith("MOVE"):                             # If the message is a move
                    i = int(data.split()[1])                            # Extract the move index
                    self.board[i] = "O"                                 # Mark the spot with an O
                    self.buttons[i].config(text="O", state="disabled")  # Disable the button
                    self.turn = True                                    # It's now the server's turn
                    self.timer_running = True                             # Start timer
                    self.timer_thread = Thread(target=self.start_turn_timer)
                    self.timer_thread.start()
                    self.status.config(text="Your turn", fg="blue")     # Update the status
                    self.check_winner("O")                              # Check if the client (O) has won
                    self.time_left = 60                                 # Reset the time for the next turn
                elif data.startswith("CHAT"):                           # If the message is a chat message
                    msg = data[5:]                                      # Extract the chat message
                    self.append_chat(f"{self.client_name}: {msg}")      # Append the client's message to the chat log
                elif data.startswith("RESET"):                          # If the message is a reset command
                    self.reset_game()                                   # Reset the game
                elif data.startswith("NAME"):                           # If the message contains the client's name
                    self.client_name = data[5:]                         # Update the client's name
            except:
                break                                                   # Break out of the loop if there is an error (e.g., connection lost)

    def check_winner(self, symbol):                                     # Check if the current player (X or O) has won
        wins = [(0, 1, 2), (3, 4, 5), (6, 7, 8),(0, 3, 6), (1, 4, 7), (2, 5, 8),(0, 4, 8), (2, 4, 6)]       # List of all possible winning combinations
        for a, b, c in wins:
            if self.board[a] == self.board[b] == self.board[c] == symbol:           # If any combination is a win
                winner = self.player_name if symbol == "X" else self.client_name    # Determine the winner
                self.status.config(text=f"{winner} wins!", fg="green")              # Update the status to show the winner
                self.conn.sendall(f"WINNER {winner}".encode())                      # Notify the client of the winner
                for btn in self.buttons:
                    btn.config(state="disabled")                                    # Disable all buttons since the game is over
                self.stop_timers = True                                             # Stop the timers
                self.save_chat()                                                    # Save the chat log
                return                                                              # End the function
        if "" not in self.board:                                                    # If there are no empty spots, it's a draw
            self.status.config(text="Draw!", fg="purple")                           # Update the status to show it's a draw
            self.conn.sendall("DRAW".encode())                                      # Notify the client of the draw
            self.stop_timers = True                                                 # Stop the timers
            self.save_chat()                                                        # Save the chat log

    def send_chat(self):                                        # Send a chat message to the client
        msg = self.chat_entry.get()                             # Get the message from the chat entry
        if msg:                                                 # If the message is not empty
            self.conn.sendall(f"CHAT {msg}".encode())           # Send the message to the client
            self.append_chat(f"You: {msg}")                     # Append the message to the chat log
            self.chat_entry.delete(0, tk.END)                   # Clear the chat entry

    def append_chat(self, msg):                                 # Add a message to the chat log
        self.chat_log.config(state='normal')                    # Enable chat log for editing
        self.chat_log.insert(tk.END, msg + "\n")                # Insert the message at the end of the log
        self.chat_log.config(state='disabled')                  # Disable chat log to prevent further editing

    def send_reset(self):                               # Send a reset command to the client
        self.conn.sendall("RESET".encode())             # Notify the client to reset the game
        self.save_chat()                                # Save the chat log
        self.reset_game()                               # Reset the game

    def save_chat(self):                                                                    # Save the chat log to a file
        with open(self.chat_log_path, "a") as f:                                            # Open the chat log file in append mode
            f.write(f"\n--- Chat at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")  # Add timestamp
            chat_text = self.chat_log.get("1.0", tk.END).strip()                            # Get the chat log text
            f.write(chat_text + "\n")                                                       # Write the chat text to the file

    def start_turn_timer(self):                                                 # Start the timer for each player's turn
        while self.time_left > 0 and not self.stop_timers and self.timer_running:                      # While there's time left and the game is not over
            self.timer_label.config(text=f"Time left: {self.time_left}")        # Update the timer label
            time.sleep(1)                                                       # Wait for 1 second
            self.time_left -= 1                                                 # Decrease the time left
        if self.time_left == 0 and not self.stop_timers:                        # If time runs out
            self.status.config(text="Time up! You lose.", fg="red")             # Notify the server player that they lose
            self.conn.sendall(f"TIMEOUT {self.player_name}".encode())           # Notify the client about the timeout
            self.stop_timers = True                                             # Stop the timers
            for btn in self.buttons:                                            # Disable all buttons
                btn.config(state="disabled")
            self.save_chat()                                                    # Save the chat log

    def start_game_timer(self):                                                 # Start the overall game timer
        def update_game_timer():
            while not self.stop_timers:                                         # While the game is still ongoing
                elapsed = int(time.time() - self.game_start_time)               # Calculate the elapsed game time
                self.game_time_label.config(text=f"Game time: {elapsed}s")      # Update the game time label
                time.sleep(1)                                                   # Wait for 1 second
        # Start the game timer in a separate thread
        Thread(target=update_game_timer, daemon=True).start()

# Run the server
if __name__ == "__main__":
    TicTacToeServer()
