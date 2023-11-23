from flask import Flask, render_template, request, url_for

from flask_socketio import SocketIO, emit
from threading import Thread, Lock
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {}
clients_lock = Lock()
clients_score = {}



questions = [
    {
        'text': 'What is the capital of France?',
        'options': ['Paris', 'Berlin', 'London', 'Madrid'],
        'correct': 0
    },
    {
        'text': 'Q2',
        'options': ['A', 'B', 'C', 'D'],
        'correct': 2
    },
    {
        'text': 'Q3',
        'options': ['1', '2', '3', '4'],
        'correct': 3
    },
    
]

def game_thread(sid, username):
    print(f'game_thread - sid: {sid}, username: {username}')
    socketio.emit('start_game',  {'start_game_url': '/game', 'username': username}, room=sid)
    clients_score[username] = {'score':0}
    

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")  
    with clients_lock:
        clients[request.sid] = {'username': None}
        print(f"current online clients:{len(clients)}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    clients.pop(request.sid, None)
    print(f"current online clients:{len(clients)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game', methods=['POST', 'GET'])
def start_game():
    if request.method == 'POST':
        username = request.form.get('username')
        return render_template('game.html', username=username)
    elif request.method == 'GET':
        username = request.args.get('username')
        return render_template('game.html', username=username)


    return render_template('game.html', username=username)

@app.route('/result', methods=['POST', 'GET'])
def game_result():
    if request.method == 'POST':
        username = request.form.get('username')
        return render_template('result.html', username=username)
    elif request.method == 'GET':
        username = request.args.get('username')
        return render_template('result.html', username=username)
    return render_template('result.html', username=username)

@socketio.on('question_request')
def handle_question_request(data):
    question_index = data.get('question_number', 0)
    if question_index < len(questions):
        question_data = questions[question_index]
        sid = request.sid
        socketio.emit('question', {
            'text': question_data['text'],
            'options': question_data['options'],
            'sid': sid
        },room=sid)
    else:
        sid = request.sid
        socketio.emit('result', {'result_url': '/result'}, room=sid)


@socketio.on('answer')
def handle_answer(data):
    username = data['username']
    answer = data['answer']
    question_data = questions[data.get('question_number', 0)]
    if int(answer) == int(question_data["correct"]):
        clients_score[username]["score"] += 1
    print(f"{username} choose answer:{answer}")


@socketio.on('get_score')
def handle_get_score(data):
    sid = request.sid
    username = data['username']  
    score = clients_score.get(username, {}).get('score', 0)
    socketio.emit('result', {'username': username, 'score': score}, room=sid)   

@socketio.on('start_game')
def handle_start_game(data):
    sid = request.sid  
    username = data['username']

    with clients_lock:
        clients[sid]['username'] = username

    game_thread_instance = Thread(target=game_thread, args=(sid, username))
    game_thread_instance.start()


if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
