""" In this module, the user can connect to a server with the specified IP and Port.
    It is Possible to send messages to other users and receive messages from other users.
    Also, the user can request a list of all users that are connected.
    The IP address can be specified by the user in the command line at runtime.
    
    Authors:
        Samuel Greger <samuel.greger@student.dhbw-vs.de>
"""

import socket
import sys

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
    """Ask for username and send it to the server for validation.
    
        Returns:
            str: The username.
    """
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
    """ Show the user the options he can choose from.
    
        Returns:
            str: The user's selection.
    """
    print("====== Minimal Chat System ======")
    print("1: Send message")
    print("2: Check incoming messages")
    print("3: Get active users")
    print("ENTER or 4: Quit")
    selection = input("Your selection: ")
    return selection


def check_input(msg):
    """ Check if the message is valid.
    
        Args:
            msg (str): The message the user wants to send.

        Returns:
            bool: True if the message is valid, False otherwise.
    """
    client_socket.send(str.encode(msg))
    if "stop" in msg.lower():
        return True
    return False


def get_all_messages(all_messages, users=False):
    """ Get all messages from the server.

        Args:  
            all_messages (list): A list of all messages.
            users (bool): True if the user wants to get a list of all users, False otherwise.

        Returns:
            list: A list of all messages or a list of all users.
    """
    client_socket.settimeout(0.5)
    print("Loading ...")
    while True:
        try:
            response = client_socket.recv(2048)
            return_msg = response.decode()
            if return_msg:
                return_msg_splited = return_msg.split('\n')
                for m in return_msg_splited:
                    if m:
                        all_messages.append(m)
                continue
            else:
                break
        except socket.timeout:
            break

    if users:
        all_users = []
        for m in all_messages[:]: # all_messages[:] because otherwise all_messages.remove(m) did not work.
            if not m.startswith("From"):
                all_users.append(m)
                all_messages.remove(m)
                return all_users
            
    else:
        msg = []
        for m in all_messages[:]: # all_messages[:] because otherwise all_messages.remove(m) did not work.
            if m.startswith("From"):
                msg.append(m)
                all_messages.remove(m)
        
        return msg


if __name__ == "__main__":
    # Ask for connection
    username = submit_username()
    all_messages = []

    # setup Chatroom and handle user input accordingly
    while True:
        user_selection = user_options()
        if user_selection == '1':
            client_socket.send(str.encode('n'))

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
            messages = get_all_messages(all_messages)
            if(messages):
                for m in messages:
                    print(f"{m}\n")
            else:
                print("No Messages\n")
            print(f"No more messages for '{username}'.\n")
        
        elif user_selection == '3':
            client_socket.send(str.encode('y'))

            messages = get_all_messages(all_messages, True)
            if(messages):
                for m in messages:
                    print(f"{m}\n")

            else:
                print("No Users\n")

        elif user_selection == '4' or not user_selection:
            messages = get_all_messages(all_messages)
            if(messages):
                print("Old messages:")
                for m in messages:
                    print(f"{m}\n")
            else:
                print("No Messages.\n")

            client_socket.send(str.encode('stop'))
            break
    
    # close the connection
    client_socket.close() 
    print("Closing down Session")
    print("Goodbye")