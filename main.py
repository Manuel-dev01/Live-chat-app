from flask import app
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
socketio = SocketIO(app)
    
app.config['SECRET_KEY'] = 'HSSJSSJSJ'
rooms = {}

def generate_unique_code(length):
    while True:
        code = ''
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break

    return code

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)
        data = {'name': name, 'code': code, 'join': join, 'create': create}
        print(data)

        if not name:
            return render_template('home.html', error="Please enter a name!", code=code, name=name)

        if join != False and not code:
            return render_template('home.html', error='Please enter a room code!', code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
           
            print(rooms)
        elif code not in rooms:
            return render_template('home.html', error="Room does not exist", code=code, name=name)

        session['room'] = room
        session['name'] = name
        return redirect(url_for('room'))

    return render_template('home.html')

@app.route('/room')
def room():
    room = session.get('room')
    print(room)
    name = session.get('name')
    print(name)
   
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home'))
    else:
        return render_template('room.html', room=room, messages=rooms[room]["messages"])

@socketio.on('message')
def message(data):
    room = session.get('room')
    name = session.get('name')

    if room not in rooms:
        return

    message_data = data.get('data')
    content = {"name": name, "message": message_data}
    send(content, to=room)
    rooms[room]['messages'].append(content)
    print(f"{session.get('name')} said: {data['data']}")

    
# When we initallize socket io, we are going to connect to the socket associated to the server that the website is on
# As soon as we connect, there is an event that is admitted to our backend server called connect, the first thing we want to do is listen for that connection event and when the connection event occurs, we want to put the user into the specific room they are going to be in

@socketio.on("connect") #The reason we are using socketio is because thats what we used for the initialization object for the socketIo library
def connect(auth):
    room = session.get('room')
    name = session.get('name')

    if not room and not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left room {room}")


if __name__ ==  '__main__':
    socketio.run(app, debug=True)

