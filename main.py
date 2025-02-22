import socket
import threading
import sys
import builtins
import time

# Global structures
connected_peers = {}            # key: "IP:PORT", value: {"socket": socket_obj, "name": peer_name}
connected_peers_lock = threading.Lock()

pending_messages = []

active_peers = set()        # Set of discovered "IP:PORT" strings (not necessarily persistent)
active_peers_lock = threading.Lock()

my_port = None
name = None

def start_server(port):
    """Starts a TCP server that listens for incoming connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(("", port))
    except Exception as e:
        print(f"Failed to bind server on port {port}: {e}")
        sys.exit(1)
    server.listen(5)
    print(f"Server listening on port {port}")
    
    while True:
        client_socket, address = server.accept()
        # Each incoming connection is handled in a separate thread
        threading.Thread(target=handle_client, args=(client_socket, address), daemon=True).start()

def handle_client(client_socket, address):
    """Continuously handles messages from a connected peer."""
    peer_key = None
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode().strip()

            # Auto-accept connection requests
            if message.startswith("CONNECT:"):
                parts = message.split(":")
                if len(parts) >= 3:
                    _, peer_name, peer_listen_port = parts[:3]
                    peer_key = f"{address[0]}:{peer_listen_port}"
                    print(f"Auto-accepted connection from {peer_name} at {peer_key}")

                    # Store connection
                    with connected_peers_lock:
                        connected_peers[peer_key] = {"socket": client_socket, "name": peer_name}
                    with active_peers_lock:
                        active_peers.add(peer_key)

                    # Send ACK back to confirm connection
                    ack_message = f"ACK:{name}:{my_port}"
                    client_socket.sendall(ack_message.encode())

            # Handle chat messages
            elif message.startswith("MESSAGE:"):
                parts = message.split(":", 3)
                if len(parts) < 4:
                    print("Malformed MESSAGE received.")
                else:
                    _, sender_name, sender_port, actual_message = parts
                    sender_key = f"{address[0]}:{sender_port}"
                    print(f"\n{sender_key} {sender_name}: {actual_message}")

                    with active_peers_lock:
                        active_peers.add(sender_key)

            # Handle peer discovery
            elif message.startswith("QUERY"):
                with connected_peers_lock:
                    peer_list = ",".join(connected_peers.keys())
                response_message = f"PEERLIST:{peer_list}"
                client_socket.sendall(response_message.encode())

            elif message.startswith("PEERLIST:"):
                _, peer_list = message.split(":", 1)
                peers_from_peer = peer_list.split(",") if peer_list else []
                with active_peers_lock:
                    for p in peers_from_peer:
                        if p:
                            active_peers.add(p)
                print("Updated discovered peers from query:")
                with active_peers_lock:
                    for p in active_peers:
                        print(p)
            else:
                print(f"Unknown message from {address}: {message}")

    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        if peer_key:
            with connected_peers_lock:
                if peer_key in connected_peers:
                    del connected_peers[peer_key]
        client_socket.close()

# 1. send message
def send_message(target_ip, target_port, message):
    """Sends a chat message to a target peer."""
    try:
        p = f"{target_ip}:{target_port}"
        active_peers.add(p)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((target_ip, target_port))
        # Construct the message including sender's fixed (listening) port
        full_message = f"MESSAGE:{name}:{my_port}:{message}"
        client.sendall(full_message.encode())
        client.close()
    except Exception as e:
        print(f"Failed to send message to {target_ip}:{target_port} - {e}")

# 2. show active peers
def display_active_peers():
    """Displays the list of active peers discovered so far."""
    print("\nActive peers:")
    with active_peers_lock:
        if active_peers:
            for peer in active_peers:
                print(peer)
        else:
            print("No active peers.")

# 3. connect to peer
def connect_to_peer(ip, port):
    """Initiates a connection to an active peer and stores the persistent connection."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, port))
        
        # Send connection request
        connect_message = f"CONNECT:{name}:{my_port}"
        client.sendall(connect_message.encode())

        # Wait for acknowledgment
        ack_data = client.recv(1024)
        if ack_data:
            ack_message = ack_data.decode().strip()
            if ack_message.startswith("ACK:"):
                parts = ack_message.split(":")
                if len(parts) >= 3:
                    peer_name = parts[1]
                    peer_port = parts[2]
                    peer_key = f"{ip}:{peer_port}"
                    print(f"Connected to {peer_name} at {peer_key}")

                    # Store connection
                    with connected_peers_lock:
                        connected_peers[peer_key] = {"socket": client, "name": peer_name}
                    with active_peers_lock:
                        active_peers.add(peer_key)

                    # Start a listener thread for this connection
                    threading.Thread(target=handle_client, args=(client, (ip, port)), daemon=True).start()
                    return
        client.close()
    except Exception as e:
        print(f"Failed to connect to {ip}:{port} - {e}")

# 4. show connected peers
def display_connected_peers():
    """Prints the list of peers you are connected to."""
    print("\nConnected peers:")
    with connected_peers_lock:
        if connected_peers:
            for key, info in connected_peers.items():
                print(f"{info['name']} at {key}")
        else:
            print("No connected peers.")



def query_peer_for_peers(peer_key):
    """Sends a QUERY to a connected peer and displays the received peer list."""
    with connected_peers_lock:
        if peer_key in connected_peers:
            try:
                sock = connected_peers[peer_key]["socket"]
                sock.sendall("QUERY".encode())
                data = sock.recv(1024)
                if data:
                    message = data.decode().strip()
                    if message.startswith("PEERLIST:"):
                        _, peer_list = message.split(":", 1)
                        print(f"Peers from {peer_key}: {peer_list}")
                        with active_peers_lock:
                            for p in peer_list.split(","):
                                if p:
                                    active_peers.add(p)
                    else:
                        print("Unexpected response to query.")
            except Exception as e:
                print(f"Error querying peer {peer_key}: {e}")
        else:
            print("Peer not connected.")





def chat_with_peer():
    w = False
    print("\nChoose with Whom you want to chat:")
    display_connected_peers()
    print("If you want to go back typr 'back'")
    idx=""
    selected_peer = None
    while not selected_peer:
        connection_name = input("Enter the name with whom you want to chat: ").strip()
        if connection_name.lower() == "back":
            print("Taking you back to menu")
            return
        count = 0
        for peer_key, info in connected_peers.items():
            if info["name"] == connection_name:
                selected_peer = peer_key 
                count = count + 1
            if count > 1:
                ip_port = input("Multiple peers found. Please specify the IP and port (format: ip port): ").strip()
                parts = ip_port.split()
            if len(parts) == 2:
                selected_peer = f"{parts[0]}:{parts[1]}"
                w = True
        if not selected_peer:
            print("Peer not found, please try again.")
    original_print = builtins.print
    def custom_print(*args, **kwags):
        message.join(str(arg) for arg in args)
        if(message.startswith("\n")):
            tokens = message.strip().split(maxsplit = 1)
            if tokens and tokens[0] != selected_peer:
                pending_messages.append(message)
                return
            else:
                original_print(*args, **kwags)
                original_print("Send message (type 'exit' to leave chat): ", end="", flush=True)
        
        original_print(*args, **kwags)
    builtins.print = custom_print

    try:
        while True:
            message = input("Send message (type 'exit' to leave chat): ").strip()
            if message.lower() == "exit":
                break
            
            ip, port = selected_peer.split(":")
            send_message(ip, int(port), message)
    finally:
        builtins.print = original_print
        print("Exiting chat mode. Messages from other peers have been stored in 'pending messages'.")




def main():
    global my_port, name
    print("Block Miners P2P\n")
    name = input("Enter your name (without any space): ").strip()
    space = name.find(" ")
    while(space != -1):
        name = input("!Please enter the name without any spaces: ").strip()
        space = name.find(" ")
    
    try:
        my_port = int(input("Enter your port number: ").strip())
    except ValueError:
        print("Invalid port number.")
        sys.exit(1)

    # Start the server thread for incoming connections
    threading.Thread(target=start_server, args=(my_port,), daemon=True).start()
    time.sleep(1)

    while True:
        print("\n***** Menu *****")
        print("1. Send message")
        print("2. Show active peers")
        print("3. Connect to an active peer")
        print("4. Show connected peers")
        print("5. Query a peer for its peers")
        print("6. Chat with a connected peer")
        print("7. Show pending messages")
        print("0. Quit")
        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            target_ip = input("Enter the recipient's IP address: ").strip()
            try:
                target_port = int(input("Enter the recipient's port number: ").strip())
            except ValueError:
                print("Invalid port number.")
                continue
            message = input("Enter your message: ").strip()
            send_message(target_ip, target_port, message)
        elif choice == "2":
            display_active_peers()
        elif choice == "3":
            display_active_peers()
            p = input("\nEnter IP:PORT: ").strip()
            target = p.split(':')
            if len(target) != 2:
                print("Invalid format. Please enter in IP:PORT format.")
                continue
            target_ip = target[0]
            try:
                target_port = int(target[1])
            except ValueError:
                print("Invalid port number.")
                continue
            connect_to_peer(target_ip, target_port)
        elif choice == "4":
            display_connected_peers()
        elif choice == "0":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
