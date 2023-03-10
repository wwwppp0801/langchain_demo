import _env
import click
import sys
import time
from flask import Flask, render_template, Response, request
import subprocess 

from flask_socketio import SocketIO

#import websockets


app = Flask(__name__)
app.config["CACHE_TYPE"]="null"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
socketio = SocketIO(app)

@app.route("/")
def index():
    # render a template with a div element for displaying output and an input element and a button for submitting name parameter
    return render_template("index.html")


import os
os.environ ['PYTHONUNBUFFERED'] = '1'

current_dir = os.getcwd()

UPLOAD_FOLDER=current_dir+"/upload"
app.config["UPLOAD_FOLDER"]=UPLOAD_FOLDER


import select

@socketio.on('submit')
def handle_submit(data):
    command = data['command']
    tools = data['tools']
    print(data)
    process = subprocess.Popen([_env.python_path ,"-u","my_chain2.py", command, tools], stdout=subprocess.PIPE, stderr=subprocess.PIPE , bufsize=0)
    # 创建一个空集合，用于存放已经结束的文件对象
    stdout = process.stdout
    stderr = process.stderr
    
    done = set()

    # 循环直到两个文件对象都结束
    while done != {stdout, stderr}:
        # 用select模块来检查哪些文件对象有可读数据
        rlist, _, _ = select.select([stdout, stderr], [], [])
        # 遍历可读的文件对象
        for f in rlist:
            # 读取一行数据
            line = f.readline()
            # 如果数据为空，说明文件对象已经结束，将其加入done集合
            if not line:
                done.add(f)
            # 否则，根据是stdout还是stderr来输出数据，并加上前缀以区分
            else:
                if f == stdout:
                    socketio.emit('result', {'line': line.decode()}, room=request.sid)
                    print (line)
                if f == stderr:
                    socketio.emit('errorlog', {'line': line.decode()}, room=request.sid)
                    print (line)
    print("end submit")
#    while True:
#        ready = select.select ([process.stdout,process.stderr], [], [], 0.1) # 检查stdout是否可读，设置超时时间为0.1秒
#        if ready [0]:
#            line = process.stdout.readline () # 读取一行stdout
#            socketio.emit('result', {'line': line.decode()})
#            print (line)
#        if ready [1]:
#            line = process.stderr.readline () # 读取一行stdout
#            socketio.emit('errorlog', {'line': line.decode()})
#            print (line)
#        else:
#            break # 如果没有可读的数据，就退出循环
#    for line in iter(process.stdout.readline, b''):
#        socketio.emit('result', {'line': line.decode()})

# 定义上传成功路由，处理文件上传请求
@app.route("/upload", methods=["POST"])
def upload():
    if request.method == "POST":
        # 获取表单中的文件对象
        file = request.files["file"]
        # 检查文件是否存在并且合法
        if file and file.filename:
            # 保存文件到指定目录
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
            # 返回成功信息和下载链接
            return f""" <p>File <b>{file.filename}</b> uploaded successfully.</p> """
            #<a href="/download/{file.filename}">Download</a>
        else:
            # 返回错误信息
            return "<p>No file selected or invalid file.</p>"

# 定义下载路由，发送已经保存的文件给客户端
@app.route("/download/<filename>")
def download(filename):
    # 从指定目录发送文件给客户端
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)



if __name__ == "__main__":
     # run the app or the command depending on the arguments
    app.run(host=_env.host, port=_env.port,debug=True)
