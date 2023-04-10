import _env
import click
import sys
import time
from flask import Flask, render_template, Response, request
import flask
import subprocess 
import json
import random

from flask_socketio import SocketIO

#import websockets


app = Flask(__name__)
app.config["CACHE_TYPE"]="null"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
socketio = SocketIO(app)

@app.route("/")
def index():
    # render a template with a div element for displaying output and an input element and a button for submitting name parameter
    return render_template("index.html",
                           nav_tabs=get_nav_tabs(request.path),)



import os
#os.environ ['PYTHONUNBUFFERED'] = '1'

current_dir = os.getcwd()

UPLOAD_FOLDER=current_dir+"/upload"
app.config["UPLOAD_FOLDER"]=UPLOAD_FOLDER


import select
import queue
import threading

def pipe_process_to_socket_io(process,sid):
    stdout = process.stdout
    stderr = process.stderr
    result=[]
    errorlog=[]
    
    #done = set()
    #
    ## 循环直到两个文件对象都结束
    #while done != {stdout, stderr}:
    #    # 用select模块来检查哪些文件对象有可读数据
    #    rlist, _, _ = select.select([stdout, stderr], [], [])
    #    # 遍历可读的文件对象
    #    for f in rlist:
    #        # 读取一行数据
    #        line = f.readline()
    #        # 如果数据为空，说明文件对象已经结束，将其加入done集合
    #        if not line:
    #            done.add(f)
    #        # 否则，根据是stdout还是stderr来输出数据，并加上前缀以区分
    #        else:
    #            if f == stdout:
    #                socketio.emit('result', {'line': line.decode()}, room=sid)
    #                print (line)
    #            if f == stderr:
    #                socketio.emit('errorlog', {'line': line.decode()}, room=sid)
    #                print (line)
    
    # 定义一个函数，用于从流中读取数据并加到队列中
    def read_stream(stream, q,label):
        try:
            for line in stream:
                q.put([label,line])
            stream.close()
        except ValueError:
            print("read error")

    # 定义一个函数，用于从队列中读取数据并处理结果
    def process_queue(q):
        while True:
            obj = q.get()
            if obj is None: # 队列为空，退出循环
                break
            label,line=obj
            #print(line.decode().strip()) # 打印结果
            if label=="stdout":
                ## result.append(ansi_escape(line.decode()))
                print(line.decode())
                socketio.emit('result', {'line': line.decode()}, room=sid)
            if label=="stderr":
                print(line.decode())
                ## errorlog.append(line.decode())
                socketio.emit('errorlog', {'line': line.decode()}, room=sid)
            q.task_done()
    
    q = queue.Queue()
    # 创建两个子线程，分别读取stdout和stderr的值，并加到队列中
    t1 = threading.Thread(target=read_stream, args=(process.stdout, q,"stdout"))
    t2 = threading.Thread(target=read_stream, args=(process.stderr, q,"stderr"))
    t1.daemon=True
    t2.daemon=True
    t1.start()
    t2.start()

    # 创建一个主线程，从队列中读取数据并处理结果
    t3 = threading.Thread(target=process_queue, args=(q,))
    t3.start()

    # 定义一个超时时间（秒）
    timeout = 180

    # 记录开始时间
    start_time = time.time()

    # 循环检查进程是否结束或超时
    while True:
        # 如果进程已经结束，退出循环
        if process.poll() is not None:
            break
        # 如果超过了超时时间，终止进程并退出循环
        if time.time() - start_time > timeout:
            process.terminate()
            process.stdout.close()
            process.stderr.close()
            print("进程超时，已终止")
            t1.join()
            t2.join()
            q.put(None)

            # 等待主线程结束
            t3.join()
            print("进程超时，已终止")
            return "timeout error", "".join(result)
            break
#        else:
#            print("time spent:"+str(time.time() - start_time) )
        time.sleep(1)

    # 等待进程结束，并关闭所有流
    process.wait()
    process.stdout.close()
    process.stderr.close()

    # 等待子线程结束，并向队列发送None信号
    t1.join()
    t2.join()
    q.put(None)

    # 等待主线程结束
    t3.join()
    ret= "".join(result),"".join(errorlog)
    print(ret)
    return ret

@socketio.on('submit')
def handle_submit(data):
    command = data['command']
    tools = data['tools']
    print(data)
    process = subprocess.Popen([_env.python_path ,"-u","my_chain2.py", command, tools], stdout=subprocess.PIPE, stderr=subprocess.PIPE , bufsize=0)
    pipe_process_to_socket_io(process,request.sid)
    print("end submit")



# 定义上传成功路由，处理文件上传请求
@app.route("/upload", methods=["POST"])
def upload():
    if request.method == "POST":
        # 获取表单中的文件对象
        file = request.files["file"]
        # 检查文件是否存在并且合法
        if file and file.filename:
            if file.filename in ["plugin_example.zip"]:
                return f"<p style='color:red'> <b>{file.filename}</b> 已经存在，请换个文件名 </p>"
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
    return flask.send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# 定义下载路由，发送已经保存的文件给客户端
@app.route("/report/<filename>")
def report(filename):
    # 从指定目录发送文件给客户端
    return flask.send_from_directory(current_dir+"/report/", filename)





@app.route("/run_test_cases")
def run_test_cases_index():
    # render a template with a div element for displaying output and an input element and a button for submitting name parameter
    return render_template("run_test_cases.html",
                           nav_tabs=get_nav_tabs(request.path),)

@app.route("/call_plugin")
def call_plugin_index():
    # render a template with a div element for displaying output and an input element and a button for submitting name parameter
    return render_template("call_plugin.html",
                           plugin_names=[
                               "iot2.dueros.com",
                               "iot.dueros.com",
                               "jd.com",
                               "www.Klarna.com"
                               ],
                           nav_tabs=get_nav_tabs(request.path),
                           )


@app.route("/file_question")
def file_question_index():
    # render a template with a div element for displaying output and an input element and a button for submitting name parameter
    return render_template("file_question.html",
                           nav_tabs=get_nav_tabs(request.path),)

def get_nav_tabs(path:str):
    nav_tabs= [
            {"path":"/","name":"langchain","title":"langchain"},
            {"path":"/run_test_cases","name":"run_test_cases","title":"运行测试用例"},
            {"path":"/call_plugin","name":"call_plugin","title":"调用插件"},
            {"path":"/file_question","name":"file_question","title":"文件问答"},
    ]
    for nav_tab in nav_tabs:
        if nav_tab["path"]==path:
            nav_tab["active"]="active"
    return nav_tabs


### mock dueros iot api
@app.route("/sample_data", methods=["GET"])
def sample_data():
    import sample_data

    result = json.dumps({"iotDevices":sample_data.iotDevices},ensure_ascii=False,indent=4)
    # 返回JSON数据
    return Response(result, mimetype='application/json')


@socketio.on('file_question')
def file_question(data):
    filename = data['filename']
    question = data['question']
    if filename!='':
        filename="./upload/"+filename
    print(data)
    process = subprocess.Popen([_env.python_path ,"-u","file_question_chain.py",question, filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE , bufsize=0)
    # 创建一个空集合，用于存放已经结束的文件对象
    pipe_process_to_socket_io(process,request.sid)
    print("end")

@socketio.on('call_plugin')
def call_plugin(data):
    plugin_name = data['plugin_name']
    command = data['command']
    session_id = data['session_id']
    api_key = data['api_key']

    env = None
    if api_key and api_key!='':
        env = {}
        env["OPENAI_API_BASE"] = "https://api.openai.com/v1"

    plugin_file = data['plugin_file']
    if plugin_file and plugin_file!='':
        filename="./upload/"+plugin_file
        import plugin_profiles.profiles as profiles
        profiles.unzip_file_to_proile(filename)

    command_line=[_env.python_path ,"-u","call_plugin_chain.py",command, plugin_name,session_id,plugin_file,api_key]
    print(command_line)
    socketio.emit('errorlog', {'line': command_line}, room=request.sid)
    process = subprocess.Popen(command_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE , bufsize=0,env=env)
    # 创建一个空集合，用于存放已经结束的文件对象
    pipe_process_to_socket_io(process,request.sid)
    print("end")


@socketio.on('run_test_cases')
def run_test_cases(data):
    tools = data['tools']
    filename = data['filename']
    if filename!='':
        filename="./upload/"+filename
        
    print(data)
    process = subprocess.Popen([_env.python_path ,"-u","performance.py", tools,filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE , bufsize=0)
    pipe_process_to_socket_io(process,request.sid)

    print("end run testcases")


### mock京东插件的接口
@app.route("/searchProduct", methods=["POST"])
def searchProduct():
     # 将查询结果转换为JSON格式
    print(request.data)
    products = [
        {'id':12345,"name":"100朵白色的花","price":100},
        {'id':12346,"name":"4090显卡","price":12999},
        {'id':12347,"name":"50朵黑色的花","price":80},
        ]
    
    result = json.dumps({"status":0,"result":{"items":products}})
    # 返回JSON数据
    return Response(result, mimetype='application/json')

### mock京东插件的接口
@app.route("/addToCart", methods=["POST"])
def addToCart():
    print(request.data)
    result = json.dumps({"status":0})
    # 返回JSON数据
    return Response(result, mimetype='application/json')


### mock dueros iot api
@app.route("/iotPlan", methods=["POST"])
def iotPlan():
    print(request.data)
    result = json.dumps({"id":random.randint(1000, 9999),"status":0})
    # 返回JSON数据
    return Response(result, mimetype='application/json')

### mock dueros iot api
@app.route("/iotPlans", methods=["POST"])
def iotPlans():
    try:
        req=json.loads(request.data)
        assert(req['plans'] is not None)
    except:
        return Response(json.dumps({"status":-1}), mimetype='application/json')
    result=[]
    for i in range(len(req['plans'])):
        if  "id" in req['plans'][i]:
            result.append(req['plans'][i]['id'])
        else:
            result.append(random.randint(1000, 9999))
    result_str = json.dumps({"id_list":result,"status":0})
    # 返回JSON数据
    return Response(result_str, mimetype='application/json')

### mock dueros iot api
@app.route("/deleteIotPlans", methods=["POST"])
def deleteIotPlans():
    try:
        req=json.loads(request.data)
        assert(req['id_list'] is not None)
    except:
        return Response(json.dumps({"status":-1}), mimetype='application/json')
    result = json.dumps({"status":0})
    # 返回JSON数据
    return Response(result, mimetype='application/json')


### mock dueros iot api
@app.route("/createOrUpdateIotScenes", methods=["POST"])
def createOrUpdateIotScenes():
    messages=[]
    try:
        req=json.loads(request.data)
        assert(req['scenes'] is not None)
    except:
        return Response(json.dumps({"status":-1,message:"scene参数不存在"}), mimetype='application/json')
    result=[]
    for i in range(len(req['scenes'])):
        if  "id" in req['scenes'][i] and len(req['scenes'][i]['id'])>0:
            messages+=[f"覆盖修改了场景，id为{id}"]
            result.append(req['scenes'][i]['id'])
        else:
            id=str(random.randint(1000, 9999))
            messages+=[f"创建了新的场景，id为{id}"]
            result.append(id)
    result_str = json.dumps({"id_list":result,"status":0,"message":"\n".join(messages)},ensure_ascii=False)
    # 返回JSON数据
    return Response(result_str, mimetype='application/json')

### mock dueros iot api
@app.route("/getIotDevices", methods=["POST"])
def getIotDevices():
    try:
        req=json.loads(request.data)
    except:
        return Response(json.dumps({"status":-1}), mimetype='application/json')
    import sample_data
    results=sample_data.iotDevices
    for i in range(len(req['scenes'])):
        if  "id" in req['scenes'][i]:
            result.append(req['scenes'][i]['id'])
        else:
            result.append(str(random.randint(1000, 9999)))
    result_str = json.dumps({"id_list":result,"status":0})
    # 返回JSON数据
    return Response(result_str, mimetype='application/json')





if __name__ == "__main__":
     # run the app or the command depending on the arguments
    app.run(host=_env.host, port=_env.port,debug=True)
