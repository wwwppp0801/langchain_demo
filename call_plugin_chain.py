import _env
import openai
openai.log="debug"
from langchain.llms import OpenAI
from tools import file_search_tool 
import sys
import json

from termcolor import colored
from langchain.embeddings import OpenAIEmbeddings
from agent.call_plugin_agent import CallPluginAgent,CallPluginAgentExecutor
from llm.my_open_ai import MyOpenAIChat
import time

if __name__ == '__main__': 
    if len(sys.argv)<3:
        print("param error:"+" , ".join(sys.argv))
        print(sys.argv[0]+" {command} {plugin_name}")
        quit()
    command=sys.argv[1]
    plugin_name=sys.argv[2]
    if len(sys.argv)>=4:
        session_id=sys.argv[3]
    else:
        session_id=time.strftime("session_%Y-%m-%d-%H-%M-%S",time.gmtime())
    session_filename="session_tmp/"+session_id+".txt"
    session_data={}
    try:
        with open(session_filename, "r") as f:
            session_data=json.loads(f.read())
    except:
        pass
    print("session_id: ",session_id,file=sys.stderr)
    print("session_data: ",json.dumps(session_data,ensure_ascii=False),file=sys.stderr)
    print(sys.argv,file=sys.stderr)
    



    llm = MyOpenAIChat(model_name=_env.model_name, temperature=0.0,
             openai_api_key=_env.api_key)
    
    print(command)
    agent = CallPluginAgent.from_llm_and_plugin(
        llm, plugin_name=plugin_name, verbose=True
    )


    
    llm.prefix_messages = [{
        "role": "system",
        "content": agent.create_system_prompt()
    },]
    if plugin_name=="iot2.dueros.com":
        my_devices=json.dumps([
                {"id":"12344", "name":"卧室的音箱", "type":"speaker","room":"卧室",},
                {"id":"12345", "name":"卧室的空调", "type":"aircondition","room":"卧室",},
                {"id":"12346", "name":"卧室的吸顶灯", "type":"light","room":"卧室",},
                {"id":"12347", "name":"卧室的台灯", "type":"light","room":"卧室",},
                {"id":"12348", "name":"卧室的加湿器", "type":"humidifier","room":"卧室",},
                {"id":"12349", "name":"卧室的温度传感器", "type":"temperature_sensor","room":"卧室",},
                {"id":"12350", "name":"卧室的窗帘", "type":"curtain","room":"卧室",},

                {"id":"12344", "name":"客厅的音箱", "type":"speaker","room":"客厅",},
                {"id":"12355", "name":"客厅的空调", "type":"aircondition","room":"客厅",},
                {"id":"12356", "name":"客厅的吸顶灯", "type":"light","room":"客厅",},
                {"id":"12357", "name":"客厅的台灯", "type":"light","room":"客厅",},
                {"id":"12358", "name":"客厅的加湿器", "type":"humidifier","room":"客厅",},
                {"id":"12359", "name":"客厅的温度传感器", "type":"temperature_sensor","room":"客厅",},
                {"id":"12360", "name":"客厅的窗帘", "type":"curtain","room":"客厅",},
                ],ensure_ascii=False)
        content="""context:
{{"iotDeviceList":{my_devices}}}
"""
        content=content.format(my_devices=my_devices)
        llm.prefix_messages.insert(0,{
            "role": "system",
            "content": content,
        })
    if session_data is not None and 'prefix_messages' in session_data:
        llm.prefix_messages=session_data['prefix_messages']


    executer = CallPluginAgentExecutor.from_agent_and_plugin_name(
        agent=agent,
        plugin_name=plugin_name,
        verbose=True,
    )
    executer.max_iterations=4
    
    executer.run(command)

    ## 把last_messages写到session_tmp目录下,以session_id命名的文件中
    session_data['prefix_messages']=llm.last_messages
    with open(session_filename,"w") as f:
        f.write(json.dumps(session_data,ensure_ascii=False))
