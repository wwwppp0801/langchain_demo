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



def test_a_query(command:str,tools="search,python_coder",verbose=True,debug=False):
    # 创建一个队列
    q = queue.Queue()
    process = subprocess.Popen([_env.python_path ,"-u","my_chain2.py", command, tools], stdout=subprocess.PIPE, stderr=subprocess.PIPE , bufsize=0)
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
            return "timeout error", ("".join(result)+"".join(errorlog))
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
        file = open(filename, "w")
        file.write(s)
        file.close()
        import report.process_json
        report.process_json.convert_json_to_excel(filename,filename+".xlsx")
        #subprocess.Popen([_env.python_path ,"-u","report/process_json.py", filename ])
        #df_json = pd.read_json(filename)
        #df_json.to_excel(filename+'.xlsx')

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
#    querys=[
#            "google的总市值是多少",
#            "Who is the current leader of Japan? What is the largest prime number that is smaller than their age",
#            "什么是比特币？它是如何创造出来的？",
#            "2023年，谁最有可能是中国的总理",
#            "去年谁是中国的总理",
#            "2000年,谁是中国的总理",
#            "谁是中国历史上任期最长的总理",
#            "周恩来当中国国家总理总共多长时间？",
#            "2023年，速度最快的显卡是什么？价格是多少？",
#            "2023年，价格最贵的显卡是什么？价格是多少？",
#            "中国人里，最有名的打过NBA的球员, 现在在干啥？",
#            "把圆周率计算到小数点后1000位",
#            "圆周率，保留小数点后前1000位",
#            "地球与太阳的距离，是土星与太阳的距离的几倍？",
#            "地球与太阳的距离，与土星与太阳的距离的比例？",
#            "地球与太阳的距离，是水星与太阳的距离的几倍？",
#            "地球与太阳的距离，与水星与太阳的距离的比例？",
#            "把太阳系的行星按照质量排序",
#            "人类发现的最大的恒星，按照质量排序的前十名是哪些？",
#            "人类发现的最大的恒星，按照质量排序的前十名是哪些？",
#            "著名的小提琴协奏曲《贝多芬》是由哪位作曲家创作的？它的调号是什么？",
#            "Which composer wrote the famous violin concerto \"Beethoven\"? What is its key signature?",
#            " What is the largest prime number that is smaller than 1293812746",
#            "北京今天的温度是多少摄氏度？",
#            "推荐5首周杰伦在2002年之前创作的歌",
#            "推荐1首周杰伦在2002年之前创作的歌",
#            "把1234分解质因数",
#            "Factor 1234 into prime factors",
#            "求 x^2+9x-5 的最小值点",
#            "已知引力常量为G，地球质量为M，地球半径为R，地球表面重力加速度为g，空间站质量为m，空间站在轨道上做圆周运动的向心加速度是多少？",
#            "已知引力常量为G，地球质量为M，地球半径为R，地球表面重力加速度为g，空间站质量为m，空间站在轨道上做圆周运动的周期是多少？" ,
#            "截面为等腰直角三角形的圆锥侧面展开图的圆心角弧度为",
#            "如果（sin a + cos a）/（sin a - cos a）=-3，则tan 2a=",
#            "Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?",
#            "The cafeteria had 23 apples. If they used 20 to make lunch and bought 6 more, how many apples do they have?",
#            "It takes Amy 4 minutes to climb to the top of a slide. It takes her 1 minute to slide down. The water slide closes in 15 minutes. How many times can she slide before it closes?",
#            "A needle 35 mm long rests on a water surface at 20◦C. What force over and above the needle’s weight is required to lift the needle from contact with the water surface? σ = 0.",
#            "一个钱包里有100个五分和十分硬币。硬币的总价值是7美元。钱包里有多少个每种硬币？",
#            "There are 100 coins in denominations of 5 cents and 10 cents. The total value of the coin is 7 dollas. How many coins are there each?",
#            "who setup Y Combinator",
#            "Y Combinator的现任ceo是谁",
#            "北京天气",
#            "北京的完整天气，用摄氏度返回",
#            "git pull有冲突应该怎么处理？",
#            ]
    with open('test_case.json', 'r') as f:
        testcases = json.load(f)
    rows=[]
    tools="search,calculator,ch_en_translator"
    import sys
    if len(sys.argv)>=2:
        tools=sys.argv[1]
    filename="report"+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+"_"+tools+".json"
    print('{"json_filename":"'+filename+'"}')
    print('{"excel_filename":"'+filename+'.xlsx"}')
    for case in testcases:
        query=case["query"]
        print(query)
        row={}
        result,errorlog=test_a_query(query,tools=tools,debug=False)
        row['query']=query
        row['final_result']=get_final_answer(result)
        row['llm_count']=get_llm_count(result)
        row['raw_result']=result
        if "validator" in case:
            row['validator']=case["validator"]
            row['validate_result']=validate(result,case["validator"])
        #print(result,errorlog)
        rows.append(row)
        raw_file_str=json.dumps(rows)
        write_file(raw_file_str,filename)
        #break
    


