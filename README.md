# cs212-course-project
# Tic Tac Toe (Two-Player over Network)

This project contains two Python scripts for a turn-based Tic Tac Toe game played over a local network using sockets and Tkinter GUIs.

## Files Included:
- `server.py` – Acts as the host (starts the game and listens for connections)  
- `client.py` – Acts as the connector (joins the game hosted by server)

## How It Works:
- The **server** program waits for a client to connect.
- The **client** program connects to the server using the local IP address and port.
- Once connected, players take turns. The server always plays first (**X**), the client second (**O**).
- A timer (60 seconds) is enforced for each player's turn.
- The game also includes **chat** and **reset** functionality.

## How to Run:
1. Open two terminal windows (or two machines if needed).

2. In the first terminal, run the server script:
   ```bash
   python3 server.py

This will open a GUI for Player 1 (X). Wait here for the client to connect.

3.In the second terminal, run the client script:
  ```bash
  python3 client.py

This opens a GUI for Player 2 (O) and connects to the server.

4.Play the game turn by turn. Only the active player’s timer will count down.
If a player runs out of time, they lose automatically.

5.Use the **"Send Msg"** button to chat, and **"Reset Game"** to restart the board.

**Important Notes:**
The **server must be started before the client.**

Both files use hardcoded localhost IP: 127.0.0.1 and port 5000.
You can modify them in the scripts if testing across different machines.
