# BlockMiners

## Overview
This project implements a **Peer-to-Peer (P2P) Chat Application** in Python. It enables the user to send and recieve messages simultaneously, supports multiple peers, and allows querying active peers. Our code also handles the bonus question.

## Team Members
1. Suryansh Nagar - 230003077
2. Manan Jiwnani - 230001049
3. Manan Nigam - 230051009
4. Tanvi Agarval - 230001075

## Features
- Simultaneous sending and recieving of messages.
- Supports multiple peers in the P2P network.
- Peer discivery and querying active peers.
- Handles fixed and ephermal ports.
- Bonus: Implements `connect()` function to establish direct connections.

## Requirements
- Programming Language: Python
- Libraries: `socket`, `threading`

## Setup Instructions
1. **Clone the Repository:**
    ```bash
    git clone https://github.com/tanveeiii/BlockMiners.git
    cd BlockMiners
    ```
2. **Run the Program:**
    ```bash
    python3 main.py
    ```
3. **Running multiple Peers:**
    ```bash
    python3 main.py --port 80
    python3 main.py --port 90
    ```

## Usage

1. **Start the Application**
    ```
    Enter your name (without any space): <Your name>
    Enter your port number: <Your chosen port number>
    Server listening on port <port number>
    ```

2. **Menu Options:**
    ```
    ***** Menu *****
    1. Send message
    2. Show active peers
    3. Connect to an active peer
    4. Show connected peers
    5. Query a peer for its peers
    6. Chat with a connected peer
    7. Show pending messages
    8. Connect to all active peers
    0. Quit
    ```

3. **Sending Messages:**
    - Select option 1.
    - Enter the recipient's IP and port.
    - Type your message.
    - Message format sent to the recipient:
        ```
        <IP:PORT> <team name> <message>
        ```

4. **Querying Peers:**
    - Select option 5 to view the list of active peers.

5. **Connecting to Peers:**
    - Select option 3 to establish connections to known peers.

6. **Exiting:**
    - Select option 0 to quit.

## Functionality Overview

### Core Functions
- **start_server(port):**
    - Starts a TCP server to listen for incoming peer connections.
    - Spawns a new thread for each incoming connection.
- **handle_client(client_socket, address):**
    - Handles messages from connected peers.
    - Supports message parsing for chat, connection requests, peer discovery and exit handling.
- **send_message(target_ip, target_port, message):**
    - Sends a message to a specific peer.
    - Formats message as `MESSAGE:<name>:<my_port>:<message>`.
- **connect_to_peer(ip, port):**
    - Establishes a persistent connection with another peer.
    - Sends a `CONNECT` request and waits for acknowledgement.
- **display_active_peers():**
    - Displays a list of discovered peers.
- **display_connect_peers():**
    - Shows peers with established persistent connections.
- **query_peer_for_peers(peer_key):**
    - Sends a `QUERY` to a peer to discover additional peers.
- **chat_with_peer():**
    - Enables intercative chat with a selected peer.
    - Supports managing pending messages from other peers during the chat.
- **print_pending_msgs():**
    - Displays stored messages received while the user was engaged in other tasks.
- **connect_all():**
    - Connects to all discovered active peers.
- **send_exit_to_all():**
    - Sends an exit notification to all connected peers before shutting down.

### How it Works
- **Networking:** Uses TCP sockets for reliable communication.
- **Concurrency:** Employs threading to handle simultaneous sending and receiving.
- **Peer Management:** Maintains active and connected peers in thread-safe structures.
- **Message Protocol:** Messages follow a structured format (e.g., `MESSAGE`, `CONNECT`, `QUERY`, `EXIT`).
