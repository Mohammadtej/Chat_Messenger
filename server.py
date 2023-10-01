from xmlrpc.server import SimpleXMLRPCServer
from pymongo import MongoClient
from pprint import pprint
from dotenv import load_dotenv
import time
import os
from threading import Thread
from datetime import datetime, timezone, timedelta


def check_response():
    return


def register(username, password):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']

    query = {'username': username}
    projection = {}

    user_data = user.find(query, projection)

    if len(list(user_data.clone())) != 0:
        client.close()
        return 0

    else:
        user.insert_one({
            'username': username,
            'password': password,
            'single_chats': [],
            'group_chats': []
            })
        client.close()
        return 1


def login(username, password):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']

    query = {'username': username,
            'password': password}

    projection = {'_id': 0}

    user_data = user.find(query, projection)

    if len(list(user_data.clone())) == 1:
        ret = list(user_data.clone())
        client.close()
        return ret

    client.close()
    return None


def create_single_chat(username, username2):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']
    single_chat = db['single_chat']
    
    query = {'username': username}
    projection = {}

    user_data = user.find(query, projection)

    if username2 in user_data[0]['single_chats']:
        client.close()
        return 2

    query = {'username': username2}
    projection = {}

    user2_data = user.find(query, projection)

    if len(list(user2_data.clone())) == 0:
        client.close()
        return 0

    sort_username1 = username
    sort_username2 = username2

    if username2 < username:
        sort_username1, sort_username2 = username2, username

    query = {'username': username}
    value = {'$addToSet': {'single_chats': username2}}

    user.update_one(query, value)

    query = {'username': username2}
    value = {'$addToSet': {'single_chats': username}}

    user.update_one(query, value)

    single_chat.insert_one({
        'username1': sort_username1,
        'username2': sort_username2,
        'timestamps': {
            username: 0,
            username2: 0
        }
    })

    client.close()
    return 1


def send_msg_single_chat(username, username2, msg):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']
    single_chat = db['single_chat']
    single_chat_conversations = db['single_chat_conversations']

    query = {'username': username}
    projection = {}

    user_data = user.find(query, projection)

    if username2 not in user_data[0]['single_chats']:
        client.close()
        return 0

    sort_username1 = username
    sort_username2 = username2

    if username2 < username:
        sort_username1, sort_username2 = username2, username

    query = {
        'username1': sort_username1,
        'username2': sort_username2
    }

    projection = {}

    chat_data = single_chat.find(query, projection)

    timestamp_username = chat_data[0]['timestamps'][username]
    timestamp_username2 = chat_data[0]['timestamps'][username2]

    timestamp_username += 1
    timestamp_username2 = max(timestamp_username2, timestamp_username) + 1

    value = {
        '$set': {
            'timestamps.'+username: timestamp_username,
            'timestamps.'+username2: timestamp_username2
        }
    }
    single_chat.update_one(query, value)

    dt = datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)
    utc_timestamp = utc_time.timestamp()

    single_chat_conversations.insert_one({
        'username1': sort_username1,
        'username2': sort_username2,
        'msg': msg,
        'timestamp': timestamp_username,
        'sent_by': username,
        'utc_timestamp': utc_timestamp
    })

    client.close()
    return 1


def display_single_chat(username, username2, prev_timestamp, single_chats):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']
    single_chat_conversations = db['single_chat_conversations']

    query = {'username': username}
    projection = {}

    user_data = user.find(query, projection)

    if username2 not in user_data[0]['single_chats']:
        client.close()
        return None

    sort_username1 = username
    sort_username2 = username2

    if username2 < username:
        sort_username1, sort_username2 = username2, username

    query = {
        'username1': sort_username1,
        'username2': sort_username2,
        'timestamp': {
            '$gt': prev_timestamp
        }
    }

    projection = {'_id': 0}
    chat_data = single_chat_conversations.find(query, projection).sort('timestamp', 1)
    ret = list(chat_data.clone())
    client.close()
    return ret


def create_group(group_name, username):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']
    groups = db['groups']

    query = {
        'group_name': group_name
    }

    projection = {'_id': 1}

    group_check = groups.find(query, projection)

    if len(list(group_check.clone())) != 0:
        client.close()
        return 0

    query = {
        'username': username
    }

    value = {
        '$addToSet': {
            'group_chats': group_name
        }
    }

    user.update_one(query, value)

    groups.insert_one({
        'group_name': group_name,
        'timestamps': {
            f'{username}': 0
        }
    })

    client.close()
    return 1


def join_group(username, group_name):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']
    groups = db['groups']
    group_chat_conversations = db['group_chat_conversations']
    
    query = {'username': username}
    projection = {}

    user_data = user.find(query, projection)

    if group_name in user_data[0]['group_chats']:
        client.close()
        return 2

    query = {
        'group_name': group_name
    }

    projection = {}

    group_check = groups.find(query, projection)

    if len(list(group_check.clone())) == 0:
        client.close()
        return 0
    
    query = {
        'username': username
    }

    value = {
        '$addToSet': {
            'group_chats': group_name
        }
    }

    user.update_one(query, value)

    query = {
        'group_name': group_name
    }

    projection = {}

    existing_chats = group_chat_conversations.find(query, projection)
    
    max_existing_msg_timestamp = 0

    for msg in existing_chats:
        max_existing_msg_timestamp = max(max_existing_msg_timestamp, msg['timestamp'])

    query = {
        'group_name': group_name
    }

    value = {
        '$set': {
            f'timestamps.{username}': max_existing_msg_timestamp + 1
        }
    }

    groups.update_one(query, value)

    client.close()
    return 1

def send_msg_group_chat(username, group_name, msg):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']
    groups = db['groups']
    group_chat_conversations = db['group_chat_conversations']

    query = {'username': username}
    projection = {}

    user_data = user.find(query, projection)

    if group_name not in user_data[0]['group_chats']:
        client.close()
        return 0

    
    query = {
        'group_name': group_name
    }

    projection = {}

    chat_data = groups.find(query, projection)

    timestamp = {}

    timestamp[username] = chat_data[0]['timestamps'][username]
    timestamp[username] += 1


    for user, ts in chat_data[0]['timestamps'].items():
        if user != username:
            timestamp[user] = max(timestamp[username], ts) + 1

    value = {
        '$set': {

        }
    }

    for user in chat_data[0]['timestamps']:
        value['$set'][f'timestamps.{user}'] = timestamp[user]

    groups.update_one(query, value)

    dt = datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)
    utc_timestamp = utc_time.timestamp()

    group_chat_conversations.insert_one({
        'group_name': group_name,
        'msg': msg,
        'timestamp': timestamp[username],
        'sent_by': username,
        'utc_timestamp': utc_timestamp
    })

    client.close()
    return 1

def display_group_chat(username, group_name, prev_timestamp):
    client = MongoClient('mongodb://localhost:27017')
    db = client['chat_messenger']
    user = db['user']
    group_chat_conversations = db['group_chat_conversations']
    
    query = {'username': username}
    projection = {}

    user_data = user.find(query, projection)

    if group_name not in user_data[0]['group_chats']:
        client.close()
        return None

    
    query = {
        'group_name': group_name,
        'timestamp': {
            '$gt': prev_timestamp
        }
    }

    projection = {'_id': 0}

    chat_data = group_chat_conversations.find(query, projection).sort('timestamp', 1)
    ret = list(chat_data.clone())
    client.close()
    return ret

def delete_msg():
    try:
        while True:
            client = MongoClient('mongodb://localhost:27017')
            db = client['chat_messenger']
            single_chat_conversations = db['single_chat_conversations']
            group_chat_conversations = db['group_chat_conversations']

            dt = datetime.now(timezone.utc) + timedelta(days=-2)
            utc_time = dt.replace(tzinfo=timezone.utc)
            utc_timestamp = utc_time.timestamp()

            query = {
                'utc_timestamp': {
                    '$lte': utc_timestamp
                }
            }

            single_chat_conversations.delete_many(query)
            group_chat_conversations.delete_many(query)
            print('The Thread has deleted messages two days prior')
            time.sleep(60 * 60)
    
    finally:
        pass

server = SimpleXMLRPCServer(("localhost", 8000), logRequests=True, allow_none=True)
server.register_function(check_response, "check_response")
server.register_function(register, "register")
server.register_function(login, "login")
server.register_function(create_single_chat, "create_single_chat")
server.register_function(send_msg_single_chat, "send_msg_single_chat")
server.register_function(display_single_chat, "display_single_chat")
server.register_function(create_group, "create_group")
server.register_function(join_group, "join_group")
server.register_function(send_msg_group_chat, "send_msg_group_chat")
server.register_function(display_group_chat, "display_group_chat")

stop_threads = False
thread = Thread(target = delete_msg)

try:
    thread.start()
    print("Starting and listening on port 8000...")
    print("Press Ctrl + C to exit.")
    server.serve_forever()

except:
    stop_threads = True
    thread.join()
    print("Exit.")

