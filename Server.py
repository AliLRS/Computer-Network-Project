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

# Lists For online_clients and Their Nicknames
online_clients = []
nicknames = []
users = []

class User:
    username = ""
    password = ""   # TODO: encrypt password
    is_online = False
    is_busy = False
    message = []

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
    for client in online_clients:
        if client == curr:
            continue
        client.send(message)

# Sending Messages To Special Client
def unitcast(message,to):
    to.send(message)

# Handling Messages From online_clients
def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if '$$$' in message:
                recipient_nickname = message[3:message.find('#')]
                recipient_socket = online_clients[nicknames.index(recipient_nickname)]
                message = "$$$"+message[message.find('#')+1:]
                unitcast(message.encode('ascii'),recipient_socket)
            else:
                # Broadcasting Messages
                broadcast(message.encode('ascii'),client)
        except Exception as e:
            print("Exception:", e)
            # Removing And Closing online_clients
            index = online_clients.index(client)
            online_clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast('{} left!'.format(nickname).encode('ascii'),client)
            nicknames.remove(nickname)
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
                        nicknames.append(nickname) 
                        online_clients.append(client)
                        user.is_online = True
                        login = True
                        client.send('OK'.encode('ascii'))
                    else:
                        client.send('Wrong'.encode('ascii'))
                        password = client.recv(1024).decode('ascii') 
                       
        if not login:
            new_user = User()
            new_user.username = nickname
            new_user.password = password
            new_user.is_online = True
            users.append(new_user)
            nicknames.append(nickname) 
            online_clients.append(client)
            client.send('OK'.encode('ascii'))
        
        # Print And Broadcast Nickname
        print("Nickname: {}".format(nickname))
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
        modified_message = ', '.join(nicknames)
        UDP_server_socket.sendto(modified_message.encode('ascii'),client_address)


# Start Handling Thread For Client
TCP_thread = threading.Thread(target=receive)
TCP_thread.start()
UDP_thread = threading.Thread(target=get_online_clients)
UDP_thread.start()