import _env
import openai
openai.log="debug"
from langchain.llms import OpenAI
import sys
import json

from termcolor import colored
from langchain.embeddings import OpenAIEmbeddings
from agent.call_plugin_agent import CallPluginAgent,CallPluginAgentExecutor
from llm.my_open_ai import MyOpenAIChat
import time
import plugin_profiles.profiles as profiles

import hashlib

def md5(string):
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()


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
    #print("session_data: ",json.dumps(session_data,ensure_ascii=False),file=sys.stderr)

    plugin_profile=None
    if plugin_name in ["iot2.dueros.com","iot3.dueros.com"]:
        plugin_profile=profiles.read_profile(f"built-in/{plugin_name}")
    if len(sys.argv)>=5:
        plugin_profile_name=sys.argv[4]
        if plugin_profile_name:
            plugin_profile=profiles.read_profile(plugin_profile_name)
            print("plugin_profile: ",json.dumps(plugin_profile,ensure_ascii=False),file=sys.stderr)
            #print("plugin_profile: ",json.dumps(plugin_profile_name,ensure_ascii=False),file=sys.stderr)
    if len(sys.argv)>=6 and sys.argv[5]!="":
        api_key=sys.argv[5]
        _env.api_key=api_key
        openai.api_key=api_key

    ### use user_id to get device list
    if len(sys.argv)>=7 and sys.argv[6]!="":
        user_id=sys.argv[6]
        plugin_profile['my_devices']=plugin_profile['devices_db'][user_id]
    
#    if len(sys.argv)>=8 and sys.argv[7]!="":
#        if sys.argv[7]=="reduce_devices":
    if _env.embedding_search:    
        import iot_device_search
        plugin_profile['my_devices']=iot_device_search.reduce_devices(command,
                                                                      plugin_profile['my_devices'],
                                                                      md5(json.dumps(plugin_profile['my_devices'])))


    print(sys.argv,file=sys.stderr)
    



    llm = MyOpenAIChat(model_name=_env.model_name, temperature=0.0,
            request_timeout=60000,
            timeout=60000,
             openai_api_key=_env.api_key)
    
    print(command)
    agent = CallPluginAgent.from_llm_and_plugin(
        llm, plugin_name=plugin_name,plugin_profile=plugin_profile, verbose=True
    )


    
#    llm.prefix_messages = [{
#        "role": "system",
#        "content": agent.create_system_prompt()
#    },]
#    my_devices=None
#    if plugin_name=="iot2.dueros.com":
#        import sample_data
#        my_devices=json.dumps(sample_data.iotDevices,ensure_ascii=False)
#    if plugin_profile and 'device_list' in plugin_profile:
#        my_devices=json.dumps(plugin_profile['device_list'],ensure_ascii=False)
#    if my_devices:
#        content="""context:
#{{"iotDeviceList":{my_devices}}}
#"""
#        content=content.format(my_devices=my_devices)
#        llm.prefix_messages.insert(0,{
#            "role": "system",
#            "content": content,
#        })
    llm.prefix_messages = agent.create_system_prompt()
    
    if session_data is not None and 'prefix_messages' in session_data:
        llm.prefix_messages=session_data['prefix_messages']


    executer = CallPluginAgentExecutor.from_agent_and_plugin_name(
        agent=agent,
        plugin_name=plugin_name,
        plugin_profile=plugin_profile,
        verbose=True,
    )
    executer.max_iterations=1
    
    executer.run(command)

    ## 把last_messages写到session_tmp目录下,以session_id命名的文件中
    session_data['prefix_messages']=llm.last_messages
    with open(session_filename,"w") as f:
        f.write(json.dumps(session_data,ensure_ascii=False))
