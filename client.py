import xmlrpc.client
import time
import random

def get_server_connection():
    url = ['http://localhost:8000/', 'http://localhost:8000/']
    choice = random.choice([0, 1])

    try:
        proxy = xmlrpc.client.ServerProxy(url[choice]) 
        proxy.check_response()
        print(f'Connected to Server {choice}')
    except:
        try:
            proxy = xmlrpc.client.ServerProxy(url[not choice]) 
            proxy.check_response()
            print(f'Connected to Server {not choice}')
        except:
            print('Unable to connect to the server at the moment. Please try again later.')
            proxy = None
    
    return proxy

if __name__ == '__main__':
	proxy = get_server_connection()

	if proxy is None:
		exit()

	menu1 = '''Chose one of the following options:
	1) Registration
	2) Login
	3) Exit'''

	while True:
		print(menu1)
		choice = int(input())

		if choice == 1:
			username = input('Enter your username: ')
			password = input('Enter the password: ')

			ret = proxy.register(username, password)

			if ret == 0:
				print('Username already exists in the system! Please try again with a different username')

			else:
				print('User registered successfully')

		elif choice == 2:
			username = input('Enter your username: ')
			password = input('Enter the password: ')

			user_data = proxy.login(username, password)

			if user_data is None:
				print('Invalid username or password')
				continue

			print('Logged in successfully')

			menu2 = '''Chose one of the following options:
				1) Single chat
				2) Group chat
				3) Go back to the previous menu
				4) Exit
				''' 

			while True:
				print(menu2)

				subchoice1 = int(input())

				# Single Chat
				if subchoice1 == 1:
					# Code to be written to check if any chats exist

					if not user_data[0]['single_chats']:
						print('No current single chats exist')

					else:
						print('The current chats are:')
						
						for val in user_data[0]['single_chats']:
							print(val)
						# Can use something better here
						print('\n')

					menu3 = '''Chose one of the following options:
					1) Create a chat with other username
					2) Display an existing chat
					3) Send Message
					4) Go back to the previous menu
					5) Exit
					''' 	

					while True:
						print(menu3)
						subchoice2 = int(input())

						if subchoice2 == 1:
							username2 = input('Enter the username: ')

							ret = proxy.create_single_chat(username, username2)

							if ret == 0:
								print(f'Username {username2} does not exist in the system')

							elif ret == 1:
								print(f'Chat created with {username2} successfully')
								user_data[0]['single_chats'].append(username2)

							else:
								print(f'Chat with {username2} already exists')
						
						elif subchoice2 == 2:	
							username2 = input('Enter the username: ')
							prev_timestamp = 0

							ret = proxy.display_single_chat(username, username2, prev_timestamp, user_data[0]['single_chats'])

							if ret is None:
								print(f'Username {username2} does not exists. Please create a chat first')
								continue

							print('\nPress Ctrl + c to go back to the previous menu\n\n')

							try:
								while True:
									ret_len = len(ret)

									if ret_len != 0:
										prev_timestamp = ret[ret_len - 1]['timestamp']
										for message in ret:
											if message['sent_by'] == username:
												print('You: ', end = '')

											else:
												print(f'{username2}: ', end = '')
											print(message['msg'])

									time.sleep(1)
									ret = proxy.display_single_chat(username, username2, prev_timestamp, user_data[0]['single_chats'])

							except KeyboardInterrupt:
								pass

						elif subchoice2 == 3:
							username2 = input('Enter the username: ')
							msg = input('Enter the message: ')

							ret = proxy.send_msg_single_chat(username, username2, msg)

							if ret == 0:
								print(f'Username {username2} does not exists. Please create a chat first')

							else:
								print(f'Message sent to {username2} successfully')

						elif subchoice2 == 4:
							break

						else:
							exit()

				# Group chat
				elif subchoice1 == 2:
					if not user_data[0]['group_chats']:
						print('No current group chats exist')

					else:
						print('The current chats are:')
						
						for val in user_data[0]['group_chats']:
							print(val)
						# Can use something better here
						print('\n')

					menu3 = '''Chose one of the following options:
					1) Create a group
					2) Join a group
					3) Display an existing group chat
					4) Send Message
					5) Go back to the previous menu
					6) Exit
					''' 	

					while True:
						print(menu3)
						subchoice2 = int(input())	

						if subchoice2 == 1:
							group_name = input('Enter the group name: ')

							ret = proxy.create_group(group_name, username)

							if ret == 0:
								print(f'Group {group_name} exists in the system. Please chose a different name')
							else:
								print(f'Group {group_name} created successfully')
							
						elif subchoice2 == 2:
							group_name = input('Enter the group name: ')

							ret = proxy.join_group(username, group_name)

							if ret == 0:
								print(f'Group {group_name} does not exist in the system. Please create a group first.')
							elif ret == 1:
								print(f'You joined Group {group_name} successfully')
							else:
								print(f'You already are part of the group {group_name}')
							
						elif subchoice2 == 3:
							group_name = input('Enter the group name: ')

							prev_timestamp = 0

							ret = proxy.display_group_chat(username, group_name, prev_timestamp)

							if ret is None:
								print(f'Group {group_name} does not exist in the system. Please create a group first.')
								continue

							print('\nPress Ctrl + c to go back to the previous menu\n\n')

							try:
								while True:
									ret_len = len(ret)

									if ret_len != 0:
										prev_timestamp = ret[ret_len - 1]['timestamp']
										for message in ret:
											if message['sent_by'] == username:
												print('You: ', end = '')

											else:
												print(f'{message["sent_by"]}: ', end = '')
											print(message['msg'])

									time.sleep(1)
									ret = proxy.display_group_chat(username, group_name, prev_timestamp)

							except KeyboardInterrupt:
								pass

						elif subchoice2 == 4:
							group_name = input('Enter the group name: ')
							msg = input('Enter the message: ')

							ret = proxy.send_msg_group_chat(username, group_name, msg)

							if ret == 0:
								print(f'Group {group_name} does not exist. Please create a group first')
							else:
								print(f'Message sent to {group_name} successfully')
						elif subchoice2 == 5:
							break
						else:
							exit()
				elif subchoice1 == 3:
					break
				else:
					exit()
		else:
			exit()


