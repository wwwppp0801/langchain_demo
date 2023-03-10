import click
import sys
import time
from flask import Flask, render_template, Response, request
import subprocess 

from flask_socketio import SocketIO

#import websockets


app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/")
def index():
    # render a template with a div element for displaying output and an input element and a button for submitting name parameter
    return render_template("index.html")

#@app.route("/stream")
#def stream():
#    # get the name parameter from the request or use default value "world"
#    name = request.args.get("name", "world")
#    # create a response object with chunked transfer encoding and call stream_output function with name parameter
#    return Response(stream_output(name), mimetype="text/plain")
#
#def stream_output(name):
#    # call the hello command line tool with name parameter and yield its output line by line
#    #process = Popen(["python","webui.py", "--name", name], stdout=PIPE)
#    process = Popen(["python","my_chain2.py", name], stdout=PIPE)
#    for line in iter(process.stdout.readline, b""):
#        yield line.decode("utf-8")

import os
os.environ ['PYTHONUNBUFFERED'] = '1'

@socketio.on('submit')
def handle_submit(data):
    command = data['command']
    process = subprocess.Popen(["python","my_chain2.py", command], stdout=subprocess.PIPE , bufsize=1)
    for line in iter(process.stdout.readline, b''):
        socketio.emit('result', {'line': line.decode()})



# define a click command with an option
@click.command()
@click.option("--name", default="world", help="The name to greet.")
def hello(name):
    # print a greeting message to stdout every second
    while True:
        click.echo(f"Hello {name}!")
        time.sleep(1)

if __name__ == "__main__":
     # run the app or the command depending on the arguments
     if len(sys.argv) > 1:
         hello()
     else:
         app.run()
