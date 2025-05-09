# Import necessary libraries similar to server code
import socket
import tkinter as tk
from tkinter import simpledialog
from threading import Thread
import time
from datetime import datetime

# Define constants for host and port for the server connection
HOST = '127.0.0.1'
PORT = 5000

# Class for the client-side logic of Tic Tac Toe
class TicTacToeClient:
    def __init__(self):
        self.window = tk.Tk()                                                        # Initialize the Tkinter window and set the title
        self.window.title("Client - Tic Tac Toe (O)")
        self.player_name = simpledialog.askstring("Player Name", "Enter your name:") # Prompt the user to input their name
        self.server_name = "Server"                                                  # The server will be referred to as "Server"
        self.create_widgets()                                                        # Call the method to create the user interface widgets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # Create a socket to connect to the server using IPv4 and TCP
        self.sock.connect((HOST, PORT))                                  # Connect to the server using the defined host and port
        self.send_name()                                                 # Send the player's name to the server
        self.chat_log_path = "chatlog.txt"                              # Define the file path to save the chat log
        self.reset_game()                                               # Reset the game to initial settings
        self.start_game_timer()                                         # Start the game timer
        Thread(target=self.receive_data).start()                        # Start a new thread to receive data from the server (like moves or messages)
        self.window.mainloop()                                          # Start the Tkinter event loop to display the GUI

    # Create and place widgets (buttons, labels, etc.) for the game interface
    def create_widgets(self):
        self.window.configure(bg="#f0f0f0")                             # Set background color of the window
        self.board_frame = tk.Frame(self.window, bg="#f0f0f0")          # Create a frame to hold the Tic Tac Toe board
        self.board_frame.pack()
        self.buttons = []                                               # List to hold references to the button widgets for the board
        
        # Create 9 buttons (for a 3x3 grid) and place them on the grid
        for i in range(9):
            btn = tk.Button(self.board_frame, text="", font=("Arial", 24), width=5, height=2,command=lambda i=i: self.make_move(i), bg="white", fg="black")
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)
            self.buttons.append(btn)

        # Create a label to show the current status of the game (waiting for the opponent)
        self.status = tk.Label(self.window, text="Waiting for opponent move", font=("Arial", 14), bg="#f0f0f0", fg="red")
        self.status.pack()

        # Create a label to show the remaining time for the current move
        self.timer_label = tk.Label(self.window, text="Time left: 60", font=("Arial", 12), bg="#f0f0f0")
        self.timer_label.pack()

        # Create a label to show the total game time elapsed
        self.game_time_label = tk.Label(self.window, text="Game time: 0s", font=("Arial", 12), bg="#f0f0f0")
        self.game_time_label.pack()

        # Create a text area to display the chat log (disabled by default to prevent editing)
        self.chat_log = tk.Text(self.window, height=10, width=50, state='disabled', bg="#e6f2ff")
        self.chat_log.pack(pady=5)

        # Create an entry field for typing chat messages
        self.chat_entry = tk.Entry(self.window, width=40)
        self.chat_entry.pack(side=tk.LEFT, padx=5)

        # Create a button to send chat messages
        self.send_button = tk.Button(self.window, text="Send Msg", command=self.send_chat)
        self.send_button.pack(side=tk.LEFT)

        # Create a button to reset the game
        self.reset_button = tk.Button(self.window, text="Reset Game", command=self.send_reset)
        self.reset_button.pack(pady=5)

    # Send the player's name to the server
    def send_name(self):
        self.sock.sendall(f"NAME {self.player_name}".encode())

    # Reset the game to the initial state
        self.timer_thread = None  # NEW: Thread reference for timer
        self.timer_running = False  # NEW: Control flag for timer

    def reset_game(self):
        self.board = [""] * 9               # Initialize the board (empty spaces)
        self.turn = False                   # Set the initial turn to False (opponent's turn first)
        self.time_left = 60                 # Set the time left for the current move (60 seconds)
        self.stop_timers = False            # Stop the timers when resetting
        for btn in self.buttons:            # Reset the board buttons to empty and re-enable them
            btn.config(text="", state="normal")

        self.status.config(text="Waiting for opponent move", fg="red")  # Set the status text to "waiting for opponent move"
        self.chat_log.config(state='normal')                            # Clear the chat log
        self.chat_log.delete("1.0", tk.END)
        self.chat_log.config(state='disabled')
        self.start_game_timer()                                         # Start the game timer

    # Handle a player's move (place 'O' on the board)
    def make_move(self, i):
        # Only allow a move if it's the player's turn and the spot is empty
        if self.turn and self.board[i] == "":
            # Update the board and the button with the player's symbol ('O')
            self.board[i] = "O"
            self.buttons[i].config(text="O", state="disabled")
            self.sock.sendall(f"MOVE {i}".encode())             # Send the move to the server
            
            # Change the turn to the opponent's and update the status
            self.turn = False
            self.timer_running = False                          # Stop timer
            self.status.config(text="Waiting for opponent move", fg="red")
            self.check_winner("O")                              # Check if the player won after this move

    # Method to continuously receive data from the server (e.g., moves, chat, game reset)
    def receive_data(self):
        while True:
            try:
                data = self.sock.recv(1024).decode()            # Receive data from the server (up to 1024 bytes)
                
                # If the data starts with "MOVE", it indicates the opponent's move
                if data.startswith("MOVE"):
                    i = int(data.split()[1])                            # Get the index of the opponent's move
                    self.board[i] = "X"                                 # Update the board with the opponent's symbol ('X')
                    self.buttons[i].config(text="X", state="disabled")  # Update the button
                    self.turn = True                                    # It's now the player's turn
                    self.timer_running = True                              # Start timer
                    self.timer_thread = Thread(target=self.start_turn_timer)
                    self.timer_thread.start()
                    self.time_left = 60                                 # Reset the move timer
                    self.status.config(text="Your turn", fg="blue")     # Update the status
                    self.check_winner("X")                              # Check if the opponent won
                    Thread(target=self.start_turn_timer).start()        # Start the move timer in a separate thread

                # If the data starts with "CHAT", it indicates a chat message
                elif data.startswith("CHAT"):
                    msg = data[5:]                                      # Extract the chat message
                    self.append_chat(f"{self.server_name}: {msg}")      # Display the message in the chat log

                # If the data starts with "RESET", it indicates that the game is being reset
                elif data.startswith("RESET"):
                    self.save_chat()                                    # Save the chat log to file
                    self.reset_game()                                   # Reset the game board

                # If the data starts with "NAME", it indicates the server's name
                elif data.startswith("NAME"):
                    self.server_name = data[5:]                         # Set the server's name

                # If the data starts with "WINNER", it indicates who won the game
                elif data.startswith("WINNER"):
                    winner = data.split()[1]                                    # Extract the winner's name
                    self.status.config(text=f"{winner} wins!", fg="green")      # Update the status
                    for btn in self.buttons:                                    # Disable all buttons
                        btn.config(state="disabled")
                    self.stop_timers = True                                     # Stop the timers
                    self.save_chat()                                            # Save the chat log

                # If the data starts with "DRAW", it indicates a draw game
                elif data.startswith("DRAW"):
                    self.status.config(text="Draw!", fg="purple")               # Update the status to show draw
                    self.stop_timers = True                                     # Stop the timers
                    self.save_chat()                                            # Save the chat log

                # If the data starts with "TIMEOUT", it indicates that the game timed out
                elif data.startswith("TIMEOUT"):
                    loser = data.split()[1]                                     # Get the name of the player who timed out
                    winner = self.player_name if loser != self.player_name else self.server_name
                    self.status.config(text=f"{winner} wins! ({loser} timed out)", fg="orange")
                    for btn in self.buttons:                                    # Disable all buttons
                        btn.config(state="disabled")
                    self.stop_timers = True             # Stop the timers
                    self.save_chat()                    # Save the chat log
            except:
                break

    # Check if there's a winner after each move
    def check_winner(self, symbol):
        # List of possible winning combinations (3 in a row)
        wins = [(0, 1, 2), (3, 4, 5), (6, 7, 8),(0, 3, 6), (1, 4, 7), (2, 5, 8),(0, 4, 8), (2, 4, 6)]
        for a, b, c in wins:
            # If all three positions in a winning combination are the same as the player's symbol
            if self.board[a] == self.board[b] == self.board[c] == symbol:
                # Determine the winner's name based on the symbol
                winner = self.player_name if symbol == "O" else self.server_name
                self.status.config(text=f"{winner} wins!", fg="green")      # Display winner message
                self.sock.sendall(f"WINNER {winner}".encode())              # Send winner info to the server
                for btn in self.buttons:                                    # Disable all buttons
                    btn.config(state="disabled")
                self.stop_timers = True                                     # Stop the timers
                self.save_chat()                                            # Save the chat log
                return
        
        # If no winner and the board is full, it's a draw
        if "" not in self.board:
            self.status.config(text="Draw!", fg="purple")               # Display draw message
            self.sock.sendall("DRAW".encode())                          # Notify the server of the draw
            self.stop_timers = True                                     # Stop the timers
            self.save_chat()                                            # Save the chat log

    # Method to send a chat message to the server
    def send_chat(self):
        msg = self.chat_entry.get()                     # Get the message from the entry field
        if msg:                                         # If the message is not empty
            self.sock.sendall(f"CHAT {msg}".encode())   # Send the message to the server
            self.append_chat(f"You: {msg}")             # Display the message in the chat log
            self.chat_entry.delete(0, tk.END)           # Clear the entry field

    # Method to append a message to the chat log
    def append_chat(self, msg):
        self.chat_log.config(state='normal')
        self.chat_log.insert(tk.END, msg + "\n")
        self.chat_log.config(state='disabled')

    # Method to send a reset command to the server
    def send_reset(self):
        self.sock.sendall("RESET".encode())     # Notify the server to reset the game
        self.save_chat()                        # Save the chat log
        self.reset_game()                        # Reset the game locally

    # Method to save the chat log to a file
    def save_chat(self):
        with open(self.chat_log_path, "a") as f:
            f.write(f"\n--- Chat at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            chat_text = self.chat_log.get("1.0", tk.END).strip()
            f.write(chat_text + "\n")

    # Method to handle the turn timer (60 seconds for each player)
    def start_turn_timer(self):
        while self.time_left > 0 and not self.stop_timers and self.timer_running:
            self.timer_label.config(text=f"Time left: {self.time_left}")                # Update the timer display
            time.sleep(1)                                                               # Wait for 1 second
            self.time_left -= 1                                                         # Decrease the time left
        # If the time runs out, declare the player as losing
        if self.time_left == 0 and not self.stop_timers:
            self.status.config(text="Time up! You lose.", fg="red")
            self.sock.sendall(f"TIMEOUT {self.player_name}".encode())                   # Notify the server of the timeout
            for btn in self.buttons:                                                    # Disable all buttons
                btn.config(state="disabled")
            self.stop_timers = True                                                     # Stop the timers
            self.save_chat()                                                            # Save the chat log

    # Method to start the game timer (tracks total game time)
    def start_game_timer(self):
        def update_game_timer():
            self.game_start_time = time.time()                              # Get the start time of the game
            while not self.stop_timers:
                elapsed = int(time.time() - self.game_start_time)           # Calculate the elapsed time
                self.game_time_label.config(text=f"Game time: {elapsed}s")  # Update the game time label
                time.sleep(1)                                               # Wait for 1 second
        
        # Start the game timer in a separate thread
        Thread(target=update_game_timer, daemon=True).start()


# Start the TicTacToeClient when the script is run
if __name__ == "__main__":
    TicTacToeClient()
