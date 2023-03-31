import _env
import openai
openai.log="debug"
from langchain.llms import OpenAI
from tools import file_search_tool 
import sys

from termcolor import colored
from langchain.embeddings import OpenAIEmbeddings
from agent.call_plugin_agent import CallPluginAgent,CallPluginAgentExecutor

if __name__ == '__main__': 
    if len(sys.argv)!=3:
        print("param error:"+" , ".join(sys.argv))
        print(sys.argv[0]+" {command} {plugin_name}")
        quit()
    command=sys.argv[1]
    plugin_name=sys.argv[2]
    print(sys.argv)


    

    llm = OpenAI(model_name=_env.model_name, temperature=0.0,openai_api_key=_env.api_key)


    llm = OpenAI(model_name=_env.model_name, temperature=0.0,
             openai_api_key=_env.api_key)
    
    print(command)
    agent = CallPluginAgent.from_llm_and_plugin(
        llm, plugin_name=plugin_name, verbose=True
    )

    
    llm.prefix_messages = [{
        "role": "system",
        "content": agent.create_system_prompt()
    },]

    executer = CallPluginAgentExecutor.from_agent_and_plugin_name(
        agent=agent,
        plugin_name=plugin_name,
        verbose=True,
    )
    executer.max_iterations=4
    
    executer.run(command)
