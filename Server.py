import socket
import threading

# Connection Data
host = '127.0.0.1'
port = 55555
UDP_port = 33333

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
print("Server is running!")

# List for users
users = []

class User:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    username = ""
    password = ""
    is_online = False
    is_busy = False
    message = []

    def __init__(self, client, username, password):
        self.client = client
        self.username = username
        self.password = password
        self.is_online = True

    def change_username(self, new_name):
        self.username = new_name
    def change_password(self, new_password):
        self.password = new_password
    def busy(self, status):
        self.is_busy = status
    def online(self, status):
        self.is_online = status
    def new_message(self, new):
        self.message.append(new)


# Sending Messages To All Connected online_clients
def broadcast(message,curr):
    for user in users:
        if user.client == curr:
            continue
        user.client.send(message)

# Sending Messages To Special Client
def unitcast(message,to):
    to.send(message)

# Handling Messages From online_clients
def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('ascii')

            if message.startswith('send-private'):
                recipient_nickname = message[12:message.find('#')]
                for user in users:
                    if user.username == recipient_nickname:
                        if not user.is_busy:
                            recipient_socket = user.client
                            message = "receive-message"+message[message.find('#')+1:]
                            unitcast(message.encode('ascii'),recipient_socket)
                            user.client.send('send-private#OK'.encode('ascii'))
                        else:
                            client.send("send-private#NOTOK".encode('ascii'))
                        

            elif message.startswith('modify'):
                message = message.split('#')
                for user in users:
                    if user.client == client:
                        if message[1] == "status":
                            if message[2] == 'busy':
                                user.busy(True)
                            else:
                                user.busy(False)
                            user.client.send('modify-status#OK'.encode('ascii'))
                            print(f"{user.username}'s status is updated to {message[2]}")
                            break

                        if message[1] == "username":
                            break_flag = False
                            for user in users:
                                if user.username == message[2]:
                                    user.client.send('modify-username#NOTOK'.encode('ascii'))
                                    break_flag = True
                                    break
                            if break_flag:
                                break
                            prv_username = user.username
                            user.change_username(message[2])
                            user.client.send('modify-username#OK'.encode('ascii'))
                            print(f"{prv_username}'s username is updated to {message[2]}")

                        if message[1] == "password":
                            user.change_password(message[2])
                            user.client.send('modify-password#OK'.encode('ascii'))
                            print(f"{user.username}'s password is updated.")
                            break
            else:
                # Broadcasting Messages
                broadcast(message.encode('ascii'),client)
        except Exception as e:
            print("Exception:", e)
            for user in users:
                if client == user.client:
                    broadcast('{} left!'.format(user.username).encode('ascii'),user.client)
                    user.online(False)
                    client.close()
            break

# Receiving / Listening Function
def receive():
    while True:
        # Accept Connection
        client, address = server.accept()
        print("A User Connected with address: {}".format(str(address)))

        # Request And Store Nickname
        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        client.send('PASS'.encode('ascii'))
        password = client.recv(1024).decode('ascii')
        login = False
        for user in users:
            if user.username == nickname:
                while not login:
                    if user.password == password:
                        user.online(True)
                        login = True
                        client.send('OK'.encode('ascii'))
                    else:
                        client.send('Wrong'.encode('ascii'))
                        password = client.recv(1024).decode('ascii') 
                       
        if not login:
            new_user = User(client, nickname, password)
            users.append(new_user)
            client.send('OK'.encode('ascii'))
        
        # Print And Broadcast Nickname
        print("Username: {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode('ascii'),client)
        client.send('Connected to Chatroom!'.encode('ascii'))

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


def get_online_clients():
    #Starting UDP server socket
    UDP_server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    UDP_server_socket.bind(("",UDP_port))
    while True:
        _ , client_address = UDP_server_socket.recvfrom(2048)
        usernames = []
        for user in users:
            if user.is_online == True:
                usernames.append(user.username)
        modified_message = ', '.join(usernames)
        UDP_server_socket.sendto(modified_message.encode('ascii'),client_address)


# Start Handling Thread For Client
TCP_thread = threading.Thread(target=receive)
TCP_thread.start()
UDP_thread = threading.Thread(target=get_online_clients)
UDP_thread.start()