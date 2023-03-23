# -*- coding: utf-8 -*-
# 修改点：
# * 修改agent的主prompt：format_instructions，重复了一次格式，避免“Action 1:”，“Thought 1:”这样的回复
# * 修改LLMMathChain的主prompt：强制生成python代码，避免语言模型自行推断
# * 修改temperature 参数为0
# * 修改MyZeroShotAgent，解决多余的"字符
# * 修改MyWolframAlphaQueryRun, 把它当成Calculator来用
# * 修改MyLLMMathChain的prompt, 确保它会生成python代码

import sys
from tools import baidu_search_tool
from tools import my_translator_tool
from tools import file_search_tool
from tools import my_wolframalpha_tool
from tools import my_python_calculator
from tools import my_serp_api_wrapper
from langchain.utilities.google_search import GoogleSearchAPIWrapper
from langchain.tools.google_search.tool import GoogleSearchResults, GoogleSearchRun
import _env

import os
import re
from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple

import openai

# openai.log="debug"

import configparser
from langchain.agents.agent import AgentExecutor


from langchain.agents.tools import Tool
from langchain.agents.agent import Agent
from langchain.chains.llm_math.base import LLMMathChain

from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from langchain.agents import load_tools
from langchain.agents import initialize_agent


from langchain.tools.base import BaseTool


from agent import my_zero_shot_agent


llm = OpenAI(model_name=_env.model_name, temperature=0.0,
             openai_api_key=_env.api_key)





tools = []


print(sys.argv)
if len(sys.argv) > 1:
    query = sys.argv[1]
    if len(sys.argv) >= 3:
        toolsStr = sys.argv[2]
        for toolStr in toolsStr.split(","):
            # calculator,search,wolframalpha_tool,ch_en_translator,en_ch_translator
            if toolStr == "calculator":
                tools.append(my_python_calculator._get_my_llm_math(llm))
            elif toolStr == "wolframalpha_tool":
                tools.append(my_wolframalpha_tool.get_tool(
                    _env.wolframalpha_appid))
            elif toolStr == "en_ch_translator":
                tools.append(my_translator_tool.en_ch_translator(_env.baidu_trans_app_id,
                                                                 _env.baidu_trans_secret_key))
            elif toolStr == "ch_en_translator":
                tools.append(my_translator_tool.ch_en_translator(_env.baidu_trans_app_id,
                                                                 _env.baidu_trans_secret_key))
            elif toolStr == "search":
                tools.append(my_serp_api_wrapper._get_serpapi(
                    serpapi_api_key=_env.google_search_api_key))
            elif toolStr == "image_search":
                tools.append(my_serp_api_wrapper._get_image_search_tool(
                    serpapi_api_key=_env.google_search_api_key))
            elif toolStr == "python_coder":
                tools.append(
                    my_python_calculator.get_python_coder_tool(_env.python_path))
            elif toolStr == "baidu_search":
                tools.append(baidu_search_tool.get_search_api())
            elif toolStr.startswith("file_search_tool"):
                file = "./data/PaulGrahamEssays/worked.txt"
                tokens = toolsStr.split(":")
                if len(tokens) >= 2:
                    file = "upload/"+tokens[1]
                if len(tokens) >= 3:
                    description = tokens[2]
                tool = file_search_tool.get_tool(file, llm)
                tools.append(tool)
else:
    # tools.append(my_serp_api_wrapper._get_serpapi(serpapi_api_key=_env.google_search_api_key))
    # tools.append(my_translator_tool.en_ch_translator(_env.baidu_trans_app_id,
    #                                                 _env.baidu_trans_secret_key))
    # tools.append(my_translator_tool.ch_en_translator(_env.baidu_trans_app_id,
    #                                                 _env.baidu_trans_secret_key))
    # tools.append(my_wolframalpha_tool.get_tool(_env.wolframalpha_appid))
    tools.append(baidu_search_tool.get_search_api())
    tools.append(my_python_calculator.get_python_coder_tool(_env.python_path))
    # tool = file_search_tool.get_tool("./upload/worked.txt",llm)
    # tools.append(tool)
    query = "北京的天气"


if __name__ == "__main__":
    if _env.use_proxy_logger == "1":
        import my_proxy
        default_backend_server = _env.proxy_default_backend_server
        if default_backend_server == "":
            default_backend_server = "https://api.openai.com"
        # os.environ["http_proxy"]=_env.proxy_logger_host+":"+str(_env.proxy_logger_port)
        # os.environ["https_proxy"]=os.environ["http_proxy"]
        # print(os.environ['http_proxy'])
        my_proxy.start_proxy_on_thread(port=_env.proxy_logger_port,
                                       address=_env.proxy_logger_host,
                                       default_backend_server=default_backend_server,
                                       )

    

    print(query)
    agent = my_zero_shot_agent.MyZeroShotAgent.from_llm_and_tools(
        llm, tools, verbose=True
    )

    llm.prefix_messages = [{
        "role": "system",
        "content": agent.create_system_prompt(tools=tools)
    },]

    executer = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
    )
    executer.run(query)
