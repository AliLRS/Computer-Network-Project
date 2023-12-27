import socket
import threading
import os
import msvcrt
import hashlib
import time
from getpass import getpass

clear = lambda: os.system('cls')

# Buffers for Received messages
private_messages = []
public_messages = []

#Chat mode
private_mode = False
chatTo = ""
public_mode = False
quit = False

def get_char():
    return msvcrt.getch().decode()

def stime():
    arr = time.asctime(time.localtime()).split(' ')
    return ' '.join(arr[1:3]) + ' at ' + ' '.join(arr[3:4])

def read_file(filename):
    data = ''
    with open(filename, 'r') as f:
        data = f.read()
    data = data.split('\n***\n')
    private_messages = data[0].split('\n###\n')[:-1]
    public_messages = data[1].split('\n###\n')[:-1]
    return private_messages, public_messages
    
def write_file(filename):
    open(filename, 'w').close() 

    with open(filename, 'a') as f:
        for pm in private_messages:
            f.write(pm + '\n###\n')

        f.write('\n***\n')

        for pm in public_messages:
            f.write(pm + '\n###\n')

def get_clients():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto("get clients".encode(),('127.0.0.1',33333))
    message, _ = client.recvfrom(2048)
    client.close()

    if message == b'':
        return 'No clients connected'
    
    return message.decode('ascii')

def busy_user_menu(client,nickname):
    global quit
    choose = input("1. Get connected clients\n2. Change status\n3. Change username\n4. Change password\n5. Exit\n")
    clear()

    if choose == "1":

        print(get_clients() + '\n')
        print(f'Press any key to quit') 
        get_char()
        clear()
        busy_user_menu(client,nickname)
    
    elif choose == "2":
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
        if status == "busy":
            busy_user_menu(client,nickname)
        else:
            internal_menu(client,nickname)

    elif choose == "3":
        new_username = input('Enter your new username: ')
        clear()
        client.send('modify#username#{}'.format(new_username).encode('ascii'))
        nickname = new_username
        time.sleep(0.1)
        busy_user_menu(client,nickname)
        
    elif choose == "4":
        new_password = getpass('Enter your new password: ')
        clear()
        hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
        client.send('modify#password#{}'.format(hashed_new_password).encode('ascii'))
        time.sleep(0.1)
        busy_user_menu(client,nickname)

    elif choose == "5":
        write_file(nickname+'.txt')
        clear()
        print('Exit program')
        quit = True
        client.close()
        exit()
    
    else:
        clear()
        print('Invalid input')
        busy_user_menu(client,nickname)
        
 
def internal_menu(client,nickname):

    global public_mode
    global private_mode
    global chatTo
    global quit

    choose = input("1. Get connected clients\n2. Enter Public Chatroom\n3. Enter Private Chatroom\n4. Send message in group\n5. Change status\n6. Change username\n7. Change password\n8. Exit\n")
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

        read_public_buffer()

    elif choose == "3":

        private_mode = True

        client_nicknames = get_clients().split(', ')
        print('Directs:')
        num = 1
        for name in client_nicknames:
            if name == nickname:
                print(str(num)+'. saved messages')
            else:
                print(str(num)+". "+name)
            num=num+1
        print(str(num)+'. back')

        recipient = input()
        try:
            recipient = int(recipient)
            if recipient == num:
                clear()
                internal_menu(client,nickname)
            elif recipient<num and recipient>0:
                chatTo = client_nicknames[recipient-1]

                clear()
                write_privatr_thread = threading.Thread(target=write_private, args=(client,nickname,client_nicknames[recipient-1]))
                write_privatr_thread.start()

                read_private_buffer(client_nicknames[recipient-1],nickname)
            else:
                clear()
                print("invalid input!")
                internal_menu(client,nickname)

        except ValueError:
            clear()
            print("invalid input!")
            internal_menu(client,nickname)            

    elif choose == "4":
        print("Who are the recipients of this message?")
        client_nicknames = get_clients().split(', ')
        num = 1
        for name in client_nicknames:
            print(str(num)+". "+name)
            num=num+1
        try:
            recipients = input()
            recipients = recipients.split(', ')
            text = input("What is your message?\n")

            strtime = stime()
            for recipient in recipients:
                message = 'send-private{}#\n{}\n{}: {}\n'.format(client_nicknames[int(recipient)-1], strtime, nickname, text)
                client.send(message.encode('ascii'))
                private_messages.append(message[12:])
            clear()
            internal_menu(client,nickname)

        except ValueError:
            clear()
            print("invalid input!")
            internal_menu(client,nickname)
        except IndexError:
            clear()
            print("invalid input!")
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
        if status == "busy":
            busy_user_menu(client,nickname)
        else:
            internal_menu(client,nickname)
        
    elif choose == "6":
        new_username = input('Enter your new username: ')
        nickname = new_username
        clear()
        client.send('modify#username#{}'.format(new_username).encode('ascii'))
        time.sleep(0.1)
        internal_menu(client,nickname)
        
    elif choose == "7":
        new_password = getpass('Enter your new password: ')
        clear()
        hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
        client.send('modify#password#{}'.format(hashed_new_password).encode('ascii'))
        time.sleep(0.1)
        internal_menu(client,nickname)

    elif choose == "8":
        write_file(nickname+'.txt')
        clear()
        print('Exit program')
        client.close()
        quit = True
        exit()
    
    else:
        clear()
        print('Invalid input')
        internal_menu(client,nickname)

# Listening to Server and Sending Nickname
def receive(client,nickname):
    global quit
    global private_mode
    global public_mode
    global chatTo
    while True:
        try:
            if quit:
                break
            else:
                # Receive Message From Server
                message = client.recv(1024).decode('ascii')

                if message.startswith('receive-message'):
                    if private_mode:
                        text = message.split('\n')[2]
                        sender = text[:text.find(':')]
                        if (chatTo == sender):
                            print(message[message.find('#')+1:])
                        private_messages.append(message[15:])
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
                        public_messages.append(message)
                    else:
                        public_messages.append(message)
                    
        except Exception as e:
            print(e)
            # Close Connection When Error
            # print(f"An error occured!")
            client.close()
            break
        

# Sending Messages To Server
def write(client,nickname):
    global quit
    global public_mode
    while True:
        if quit:
            break
        else:
            text = input('')
            if text == "quit":
                clear()
                public_mode=False
                internal_menu(client,nickname)
                break
            else:
                strtime = stime()
                message = '\n{}\n{}: {}\n'.format(strtime, nickname, text)
                client.send(message.encode('ascii'))
                public_messages.append(message)
                clear()
                read_public_buffer()

def write_private(client,nickname,recipient):
    global quit
    global private_mode
    global chatTo
    while True:
        if quit:
            break
        else:
            text = input('')
            if text == "quit":
                clear()
                private_mode=False
                chatTo = ""
                internal_menu(client,nickname)
                break
            else:
                strtime = stime()
                message = 'send-private{}#\n{}\n{}: {}\n'.format(recipient, strtime, nickname, text)
                client.send(message.encode('ascii'))
                private_messages.append(message[12:])
                clear()
                read_private_buffer(recipient,nickname)

def read_private_buffer(recipient,nickname):
    for message in private_messages:
        text = message.split('\n')[2]
        sender = text[:text.find(':')]
        if (message[:message.find('#')] == recipient and sender == nickname) or (message[:message.find('#')] == nickname and sender == recipient):
            print(message[message.find('#')+1:])

def read_public_buffer():
    for message in public_messages:
        print(message)


#main menu comes up
def main_menu():

    global public_mode
    global private_mode
    global quit
    global public_messages
    global private_messages
    
    public_mode = False
    private_mode = False
    
    choose = input(f"1. Get connected clients\n2. Enter Chatroom\n3. Exit\n")
    clear()
    
    if choose == "1":
    
        print(get_clients() + '\n')
        main_menu()
    
    elif choose == "2":
    
        # Choosing Nickname
        nickname = input("Enter your username: ")
        password = getpass("Enter your password: ")
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

        while 'NOTOK' == client.recv(1024).decode('ascii'):
            password = getpass('Wrong Password\nTry again: ')
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            client.send(hashed_password.encode('ascii'))

        if os.path.isfile(nickname+'.txt'):
            private_messages, public_messages = read_file(nickname+'.txt')

        status = client.recv(1024).decode('ascii')
        # Starting Threads For Listening And Reading
        receive_thread = threading.Thread(target=receive, args=(client,nickname))
        receive_thread.start()
        clear()
        if status == "available":
            internal_menu(client,nickname)
        elif status == "busy":
            busy_user_menu(client,nickname)
    
    elif choose == "3":
        write_file(nickname+'.txt')
        clear()
        print('Exit program')
        quit = True
        exit()
    
    else:
        print(f"Invalid Input\n")
        main_menu()


main_menu()