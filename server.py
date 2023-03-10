""" Server for multithreaded (asynchronous) chat application.

    Authors:
        Samuel Greger <samuel.greger@student.dhbw-vs.de>
        Extended the Moodle file from Wolfgang Funk.
"""

import socket
import sys
import platform
from threading import Thread, Lock
from queue import Queue

PORT = 8080
LOCALHOST = '127.0.0.1'

def get_my_ip():
    """Return the ipaddress of the local host

    On Debian-based systems we may get a rather strange address: 127.0.1.1
    See: https://www.debian.org/doc/manuals/debian-reference/ch05.en.html#_the_hostname_resolution

    """
    return socket.gethostbyname(LOCALHOST) #socket.gethostbyname(socket.gethostname())


def check_received_message(msg):
    """ Check if the received message is a stop message.

        Args:
            msg (str): The message a client send.

        Returns:
            bool: True if the message is a stop message, False otherwise.
    """
    if not msg or "stop" in msg.lower():
        return True
    return False


def send_client_list(conn, username):
    """ Send a list of all connected clients to the client.
        
        Args:
            conn (socket): The socket of the client.
    """
    names = []
    for cli in client_list:
        if (cli[0] != username):
            names.append(cli[0])
    if(len(names) > 0):
        conn.send(str.encode(f"Other users: {','.join(names)}\n"))
    else:
        conn.send(str.encode(f"No Other users at the time\n"))

def accept_client(conn, addr, client_list):
    """ Accept a new client and add it to the client list.

        Args:
            conn (socket): The socket of the client.
            addr (tuple): The address of the client.
            client_list (list): The list of all connected clients.

        Returns:
            tuple: The socket, address and username of the new client.
    """
    valid_user = False
    while True:
        data = conn.recv(2048)
        username = data.decode()
        names = []
        for cli in client_list:
            names.append(cli[0])
        with lock:
            if not names:
                valid_user = True
                break
        
            if not (username in names):
                valid_user = True
                break

    if not valid_user:      
        unvalid_user_msg = f"'{username}' is invalid"
        print(unvalid_user_msg)

    if valid_user:
        with lock:
            client_list.append((username, conn))
            all_clients.put((conn, addr, username))
        msg = f"New connection: {addr[0]}:{addr[1]}"
        print(msg)
        conn.send(str.encode(f'Client "{username}" registered.\n'))


def receive_message(connection, address, username, message_queue):
    """ Receive a message from a client and put it in the queue.

        Args:
            connection (socket): The socket of the client.
            address (tuple): The address of the client.
            username (str): The username of the client.
            message_queue (queue): The queue where the received messages are stored.
    """
    global conn_cnt
    print(f"{username} at {address[0]}:{address[1]}")
    
    while True:
        print(f"Listening for {username} ({address[0]}:{address[1]}) ...")
        data_action = connection.recv(2048)
        action_decoded = data_action.decode()
        if check_received_message(action_decoded):
            break
        if action_decoded == "y":
            send_client_list(connection, username)
        
        elif action_decoded == "n":
            data_to_user = connection.recv(2048)
            to_user_decoded = data_to_user.decode()
            if check_received_message(to_user_decoded):
                break
            data_message = connection.recv(2048)
            message_decoded = data_message.decode()
            if check_received_message(message_decoded):
                break

            message_queue.put((username, message_decoded, to_user_decoded))
        
    for i in client_list:
        if i[0] == username:
            client_list.remove(i)
            conn_cnt -= 1
            connection.close()
            print(f"Closing connection to {address[0]}:{address[1]}. '{username}'")
            return
    print("Can't close connection.")


def send_message(message_queue):
    """ Rread a message from the queue and send it to a client.

        Args:
            message_queue (queue): The queue where the received messages are stored.
    """
    while True:
        username, msg, to_user = message_queue.get()
        found = False
        for sock in client_list:
            if to_user == sock[0]:
                connection = sock[1]
                found = True

                reply = f'From {username}: "{msg}"\n'
                print(reply)
                connection.send(str.encode(reply))
        if not found:
            print(f"'{to_user}' not found")


if __name__ == "__main__":
    # Socket setup
    server_socket = socket.socket()
    try:
        server_socket.bind((get_my_ip(), PORT))
    except socket.error as e:
        print(e)
        server_socket.close()
        sys.exit(1)
    if platform.system() == "Windows":
        # Windows: No reaction to signals during socket.accept()
        #          => Wake up periodically from accept.
        server_socket.settimeout(1)
    # Start socket
    server_socket.listen()
    print(f"Listening on {get_my_ip()}:{PORT}")

    lock = Lock()
    conn_cnt = 0

    client_list = []
    message_queue = Queue()
    all_clients = Queue()

    try:
        while True:
            try:                
                conn_f, addr_f = server_socket.accept()
                Thread(target=accept_client, args=(conn_f, addr_f, client_list), daemon=True).start()
                conn_cnt += 1

                conn, addr, username = all_clients.get()

                Thread(target=receive_message, args=(conn, addr, username, message_queue), daemon=True).start()
                Thread(target=send_message, args=(message_queue, ), daemon=True).start()
                
                print(f"{conn_cnt} connections")
            except socket.timeout:  # Windows (Python >= 3.10: TimeoutError)
                continue
    except KeyboardInterrupt:
        print("\nStopping server due to user request")
    finally:
        print("Closing server socket")
        print(f"{conn_cnt} connections")
        server_socket.close()
