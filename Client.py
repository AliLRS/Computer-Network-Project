import socket
import threading
import os
import msvcrt
import hashlib
import time

clear = lambda: os.system('cls')

# Buffers for Received messages
private_messages = []
public_messages = []

#Chat mode
private_mode = False
public_mode = False

def get_char():
    return msvcrt.getch().decode()

def stime():
    arr = time.asctime(time.localtime()).split(' ')
    return ' '.join(arr[1:3]) + ' at ' + ' '.join(arr[3:4])

def get_clients():

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto("get clients".encode(),('127.0.0.1',33333))
    message, _ = client.recvfrom(2048)
    client.close()

    if message == b'':
        return 'No clients connected'
    
    return message.decode('ascii')
 
def internal_menu(client,nickname):

    global public_mode
    global private_mode

    choose = input("1. Get connected clients\n2. Enter Public Chatroom\n3. Send Private Message\n4. Get Private Messages\n5. Change status\n6. Change username\n7. Change password\n8. Exit\n")
    clear()

    if choose == "1":

        print(get_clients() + '\n')
        print(f'Press any key to quit') 
        get_char()
        clear()
        internal_menu(client,nickname)

    elif choose == "2":

        public_mode=True
        
        # Starting Thread For Writing
        write_thread = threading.Thread(target=write, args=(client,nickname))
        write_thread.start()

        # Starting Thread For Readin public buffer
        read_public_buffer_thread = threading.Thread(target=read_public_buffer, args=())
        read_public_buffer_thread.start()

    elif choose == "3":

        client_nicknames = get_clients().split(', ')
        print('Who is the recipient of this message?')
        num = 0
        for name in client_nicknames:
            print(str(num)+". "+name)
            num=num+1
        
        recipient = int(input())
        
        print("Enter your message:")
        private_message = input()
        clear()
        strtime = stime()
        message = 'send-private{}#{}\n{}: {}'.format(client_nicknames[recipient], strtime, nickname, private_message)
        client.send(message.encode('ascii'))
        time.sleep(0.1)
        internal_menu(client,nickname)

    elif choose == "4":

        private_mode=True
        print(f'Press any key to quit')
        
        # Starting Thread For Readin private buffer
        read_private_buffer_thread = threading.Thread(target=read_private_buffer, args=())
        read_private_buffer_thread.start()

        get_char()
        clear()
        private_mode=False
        internal_menu(client,nickname)

    elif choose == "5":
        status = input('What is your status?\n1.busy    2.available\n')
        clear()
        if status == "1" or status == "2":
            if status == "1":
                status = "busy"
            else:
                status = "available"
            client.send('modify#status#{}'.format(status).encode('ascii'))
        else:
            clear()
            print('Invalid input\n')
        time.sleep(0.1)
        internal_menu(client,nickname)
        
    elif choose == "6":
        new_username = input('Enter your new username: ')
        clear()
        client.send('modify#username#{}'.format(new_username).encode('ascii'))
        time.sleep(0.1)
        internal_menu(client,nickname)
        
    elif choose == "7":
        new_password = input('Enter your new password: ')
        clear()
        hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
        client.send('modify#password#{}'.format(hashed_new_password).encode('ascii'))
        time.sleep(0.1)
        internal_menu(client,nickname)

    elif choose == "8":
        clear()
        print('Exit program')
        exit()
    
    else:
        clear()
        print('Invalid input')
        internal_menu(client,nickname)

# Listening to Server and Sending Nickname
def receive(client,nickname):
    global private_mode
    global public_mode
    while True:
        try:
            # Receive Message From Server
            message = client.recv(1024).decode('ascii')

            if message.startswith('receive-message'):
                if private_mode:
                    print(message[15:])
                else:
                    private_messages.append(message[15:])
            
            elif message.startswith('send-private'):
                if message[13:] == 'OK':
                    print('Your message is sent\n')
                else:
                    print('User is busy!\n')

            elif message.startswith('modify-status'):
                if message[14:] == 'OK':
                    print('Your Status is updated\n')
                else:
                    print('Your request was not accepted\n')

            elif message.startswith('modify-username'):
                if message[16:] == 'OK':
                    print('Your Username is updated\n')
                else:
                    print('This username is already taken!\n')

            elif message.startswith('modify-password'):
                if message[16:] == 'OK':
                    print('Your Password is updated\n')
                else:
                    print('Your request was not accepted\n')

            else:
                if public_mode:
                    print(message)
                else:
                    public_messages.append(message)
                
        except:
            # Close Connection When Error
            print(f"An error occured!")
            client.close()
            break
        

# Sending Messages To Server
def write(client,nickname):
    global public_mode
    while True:
        text = input('')
        if text == "quit":
            clear()
            public_mode=False
            internal_menu(client,nickname)
            break
        else:
            strtime = stime()
            message = '\n{}\n{}: {}'.format(strtime, nickname, text)
            client.send(message.encode('ascii'))
        
def read_private_buffer():
    global private_mode
    while True:
        if not private_mode:
            break
        if private_messages:
            for message in private_messages:
                print(message)
            private_messages.clear()

def read_public_buffer():
    global public_mode
    while True:
        if not public_mode:
            break
        if public_messages:
            for message in public_messages:
                print(message)
            public_messages.clear()


#main menu comes up
def main_menu():

    global public_mode
    global private_mode
    
    public_mode = False
    private_mode = False
    
    choose = input(f"1. Get connected clients\n2. Enter Chatroom\n3. Exit\n")
    clear()
    
    if choose == "1":
    
        print(get_clients() + '\n')
        main_menu()
    
    elif choose == "2":
    
        # Choosing Nickname
        nickname = input(f"Enter your username: ")
        password = input(f"Enter your password: ")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
        # Connecting To Server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 55555))

        message = client.recv(1024).decode('ascii') 
        if message == 'NICK':
            client.send(nickname.encode('ascii'))

        message = client.recv(1024).decode('ascii')
        if message == 'PASS':
            client.send(hashed_password.encode('ascii'))

        while 'OK' != client.recv(1024).decode('ascii'):
            password = input('Wrong Password\nTry again: ')
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            client.send(hashed_password.encode('ascii'))
        
        # Starting Threads For Listening And Reading
        receive_thread = threading.Thread(target=receive, args=(client,nickname))
        receive_thread.start()
        
        clear()
        internal_menu(client,nickname)
    
    elif choose == "3":
        clear()
        exit()
    
    else:
        print(f"Invalid Input\n")
        main_menu()


main_menu()