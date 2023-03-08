import socket
import sys
from threading import Thread
from queue import Queue

client_socket = socket.socket()
LOCALHOST = '127.0.0.1' # '192.168.56.1'
PORT = 8080

try:
    host = input('IP of the server (default 127.0.0.1): ') # sys.argv[1] # server IP given on command line
except IndexError:
    host = LOCALHOST
    print(f"No server given on command line. Trying {host}")
try:
    if not host:
        host = LOCALHOST
    print(f"Waiting for connection to {host}")
    client_socket.connect((host, PORT))
except socket.error as e:
    print(str(e))
    if host == LOCALHOST:
        print("Running locally on Debian based system? "
              "Then you may try 127.0.1.1 for connecting to server")
    sys.exit(1)


def submit_username():
    while True:
        username = input("Choose client ID: ")
        if not username:
            continue
        client_socket.send(str.encode(username))

        client_socket.settimeout(1)
        try: 
            response = client_socket.recv(2048)
            return_msg = response.decode()
            if return_msg:
                print(return_msg)
                
                return username
        except socket.timeout:
            print(f"Username: '{username}' is invalid. Try again.")
            continue


def user_options():
    print("====== Minimal Chat System ======")
    print("1: Send message")
    print("2: Check incoming messages")
    print("ENTER or 3: Quit")
    selection = input("Your selection: ")
    return selection


def check_input(msg):
    client_socket.send(str.encode(msg))
    if "stop" in msg.lower():
        return True
    return False


def get_all_messages():
    all_messages = []
    client_socket.settimeout(0.5)
    print("Loading ...")
    while True:
        try:
            response = client_socket.recv(2048)
            return_msg = response.decode()
            if return_msg:
                all_messages.append(return_msg)
                continue
            else:
                break
        except socket.timeout:
            break

    return all_messages


if __name__ == "__main__":
    # Ask for connection
    username = submit_username()
    # setup Chatroom and do the talk
    while True:
        user_selection = user_options()
        if user_selection == '1':
            user_list = input("Do you want the see the aktive Users in the System? (y/n): ")
            if(user_list == 'y'):
                client_socket.send(str.encode('y'))
                response = client_socket.recv(2048)
                return_user_list = response.decode()
                print(f"{return_user_list}")

            # Send the user the message should be send to
            to_user = input("Send message to: ")
            if not to_user:
                continue
            if check_input(to_user):
                break

            # Send the message
            message_to_send = input("Say something: ")
            if not message_to_send:
                continue
            if check_input(message_to_send):
                break

        elif user_selection == '2':
            messages = get_all_messages()
            if(messages):
                for m in messages:
                    print(f"{m}\n")
            else:
                print("No Messages\n")
            print(f"No more messages for '{username}'.\n")
        elif user_selection == '3' or not user_selection:
            messages = get_all_messages()
            if(messages):
                print("Old messages:")
                for m in messages:
                    print(m)
            else:
                print("No Messages\n")

            client_socket.send(str.encode('stop'))
            break

    client_socket.close()
    print("Closing down Session")
    print("Goodbye")