import _env
import subprocess
import select
import datetime
import json
import time
import os
import threading
import queue
import re
import pandas as pd
import sys


def ansi_escape(line:str):
    ansi_esc = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_esc.sub('', line)



def test_a_query(command:str,plugin_name="iot3.dueros.com",session_id=None,plugin_file=None,verbose=True,debug=False):
    if session_id==None:
        session_id=time.strftime("session_%Y-%m-%d-%H-%M-%S",time.gmtime())
    # 创建一个队列
    q = queue.Queue()
    params=[_env.python_path ,"-u","call_plugin_chain.py",command, plugin_name,session_id,plugin_file]
    print(params)
    process = subprocess.Popen(params, stdout=subprocess.PIPE, stderr=subprocess.PIPE , bufsize=0)
    result=[]
    errorlog=[]

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
                result.append(ansi_escape(line.decode()))
                if verbose:
                    print(line.decode())
            if label=="stderr":
                errorlog.append(line.decode())
                if debug:
                    print(line.decode(),file=sys.stderr)
            q.task_done()
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
    return "".join(result),"".join(errorlog)
    

def write_file(s:str,filename:str):
    if s:
        filename=os.getcwd()+"/report/"+filename
        file = open(filename, "w")
        file.write(s)
        file.close()
        import process_json
        process_json.convert_json_to_excel(filename, filename+".xlsx")

def get_final_answer(my_string,sub_string="Final Answer:"):
    last_index = my_string.rfind(sub_string) # find the last index of sub_string
    if last_index == -1: # if sub_string is not found
        result = my_string # result is the whole string
    else: # if sub_string is found
        result = my_string[last_index + len(sub_string):] # slice the string from last 
    return result

def get_llm_count(raw_result):
    sub_string = "Observation:"
    count = raw_result.count(sub_string) # find the last index of sub_string
    return count+1


def validate(i:str,validator:str)->bool:
    #print(validator)
    def m(regexp:str)->bool:
        return re.search(regexp, i, re.IGNORECASE) != None
    try:
        return eval(validator)
    except:
        return False

if __name__=="__main__":
    print ("start")
    testcase_filename="upload/iot_test_case.json"
    plugin_name="iot3.dueros.com"
    plugin_file=""
    
    if len(sys.argv)>=2:
        plugin_name=sys.argv[1]
    if len(sys.argv)>=3 and sys.argv[2]!="":
        testcase_filename=sys.argv[2]
    if len(sys.argv)>=4 and sys.argv[3]!="":
        plugin_file=sys.argv[3]


    with open(testcase_filename, 'r') as f:
        testcases = json.load(f)
    rows=[]
    filename="report"+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+"_"+plugin_name+"_"+plugin_file+".json"
    print('{"json_filename":"'+filename+'"}')
    print('{"excel_filename":"'+filename+'.xlsx"}')
    for case in testcases:
        query=""
        if "query" in case:
            query=case["query"]
        else:
            query=case["question"]
        print(query)
        row={}
        result,errorlog=test_a_query(query,plugin_name=plugin_name,plugin_file=plugin_file,debug=False)
        row['query']=query
        row['raw_result']=result
        if result=="timeout error":
            row['raw_result']=errorlog
#        if "validator" in case:
#            row['validator']=case["validator"]
#            row['validate_result']=validate(row['final_result'],case["validator"])
#        if "expect_answer" in case:
#            row['validator']="m(\"\\\\b"+case["expect_answer"]+"\\\\b\")"
#            try:
#                row['validate_result']=validate(row['final_result'],row["validator"])
#            except:
#                row['validate_result']="validate error:"+row['validator']
        #print(result,errorlog)
        rows.append(row)
        raw_file_str=json.dumps(rows)
        write_file(raw_file_str,filename)
        #break
    



