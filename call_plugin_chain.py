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
