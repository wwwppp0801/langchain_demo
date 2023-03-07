import os
import sys
import time
import datetime
import langchain
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.agents import Agent
from langchain.agents import load_tools
from langchain import OpenAI
from langchain.agents import initialize_agent, Tool
from langchain import LLMMathChain, SerpAPIWrapper
import openai
import configparser

openai.log="debug"

# 创建一个ConfigParser对象
config = configparser.ConfigParser()

# 读取一个INI文件
config.read("config.ini")
google_search_api_key=config.get("main","google_search_api_key")

os.environ["OPENAI_API_KEY"] = "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"
os.environ["SERPAPI_API_KEY"] = google_search_api_key
llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0)

search = SerpAPIWrapper()
tools = [
    Tool(
        name="Intermediate Answer",
        func=search.run,
        description = "useful for when you need to answer questions about current events"
    )
]

self_ask_with_search = initialize_agent(tools, llm, agent="self-ask-with-search", verbose=True)
print(self_ask_with_search)

self_ask_with_search.run("What is the hometown of the reigning men's U.S. Open champion?")


######### 现在有bug，会死循环

#chain: self-ask-with-search
#
#以上是基础prompt，试图让chatgpt自己生成中间问题，并做回答
#
#但是在测试问题中（Who is the reigning men\'s U.S. Open champion?\），chatgpt分解出了第一层问题：（ Who is the reigning men\'s U.S. Open champion?），但解析代码
#
#
#需要第一次的返回值里有“Follow up:”，但返回值里没有
#
#导致给第二次的prompt拼上了“So the final answer is”
#
#然后每次回答都给了结果：“Unknown, as the follow-up question needs to be answered first.”
#
#然后进入了死循环。。。
#
#
#langchain
#奇怪的返回
