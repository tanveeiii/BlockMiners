import socket
import threading
import sys

# Global Variables
peers = set()                   # Store "IP:PORT" strings for known peers
peers_lock = threading.Lock()   # Lock to synchronize access to peers set
my_port = None
name = None

def start_server(port):
    """Starts the TCP server to listen for incoming connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(("", port))
    except Exception as e:
        print(f"Failed to bind server on port {port}: {e}")
        sys.exit(1)
    server.listen(5)
    print(f"Server listening on port {port}")
    
    while True:
        try:
            client_socket, address = server.accept()
            # Handle each connection in a new thread
            threading.Thread(target=handle_client, args=(client_socket, address), daemon=True).start()
        except Exception as e:
            print("Error accepting connection:", e)
            break

def handle_client(client_socket, address):
    """Handles an incoming connection and processes a single message."""
    try:
        message = client_socket.recv(1024).decode().strip()
        if not message:
            return

        # Process a connection request
        if message.startswith("CONNECT:"):
            parts = message.split(":")
            if len(parts) >= 3:
                _, peer_name, peer_listen_port = parts[0:3]
                print(f"Received connection request from {peer_name} at {address[0]}:{peer_listen_port}")
                with peers_lock:
                    peers.add(f"{address[0]}:{peer_listen_port}")
                ack_message = f"ACK:{name}:{my_port}"
                client_socket.sendall(ack_message.encode())

        # Process a query request (if needed, a peer can query our info)
        elif message.startswith("QUERY"):
            response_message = f"RESPONSE:{name}:{my_port}"
            client_socket.sendall(response_message.encode())

        # Process a regular chat message
        elif message.startswith("MESSAGE:"):
            # Expected format: MESSAGE:<sender_name>:<sender_listen_port>:<message>
            parts = message.split(":", 3)
            if len(parts) < 4:
                print("Malformed MESSAGE received.")
            else:
                _, sender_name, sender_listen_port, actual_message = parts
                if actual_message.strip().lower() == "exit":
                    print(f"Peer {sender_name} at {address[0]}:{sender_listen_port} has disconnected.")
                    with peers_lock:
                        peers.discard(f"{address[0]}:{sender_listen_port}")
                else:
                    print(f"Message from {sender_name} ({address[0]}:{sender_listen_port}): {actual_message}")
                    with peers_lock:
                        peers.add(f"{address[0]}:{sender_listen_port}")
        else:
            print(f"Unknown message from {address}: {message}")

    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        client_socket.close()

def send_message(target_ip, target_port, message):
    """Sends a chat message to a target peer."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((target_ip, target_port))
        # Construct the message including sender's fixed (listening) port
        full_message = f"MESSAGE:{name}:{my_port}:{message}"
        client.sendall(full_message.encode())
        client.close()
    except Exception as e:
        print(f"Failed to send message to {target_ip}:{target_port} - {e}")

def query_peers():
    """Displays the list of active peers discovered so far."""
    print("\nActive peers discovered:")
    with peers_lock:
        if peers:
            for peer in peers:
                print(peer)
        else:
            print("No connected peers.")

def connect_to_peers():
    """Connects to each active peer and sends a connection request."""
    with peers_lock:
        current_peers = list(peers)
    if not current_peers:
        print("No active peers to connect.")
        return

    for peer in current_peers:
        ip, port_str = peer.split(":")
        try:
            port = int(port_str)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, port))
            connect_message = f"CONNECT:{name}:{my_port}"
            client.sendall(connect_message.encode())
            ack_message = client.recv(1024).decode().strip()
            if ack_message.startswith("ACK:"):
                ack_parts = ack_message.split(":")
                if len(ack_parts) >= 2:
                    print(f"\n\nConnection accepted by {ack_parts[1]} at {ip}:{port}")
            else:
                print(f"\n\nNo proper acknowledgment received from {ip}:{port}.")
            client.close()
        except Exception as e:
            print(f"\n\nFailed to connect to {ip}:{port} - {e}")

def main():
    global my_port, name
    print("Block Miners P2P\n")
    name = input("Enter your name: ").strip()
    try:
        my_port = int(input("Enter your port number: ").strip())
    except ValueError:
        print("Invalid port number.")
        sys.exit(1)

    # Start the server thread (daemon thread so it exits when main thread ends)
    threading.Thread(target=start_server, args=(my_port,), daemon=True).start()

    # Main menu loop
    while True:
        print("\n***** Menu *****")
        print("1. Send message")
        print("2. Query active peers")
        print("3. Connect to active peers")
        print("0. Quit")
        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            target_ip = input("Enter the recipient's IP address: ").strip()
            try:
                target_port = int(input("Enter the recipient's port number: ").strip())
            except ValueError:
                print("Invalid port number.")
                continue
            message = input("Enter your message (type 'exit' to disconnect a peer): ").strip()
            send_message(target_ip, target_port, message)
        elif choice == "2":
            query_peers()
        elif choice == "3":
            connect_to_peers()
        elif choice == "0":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
