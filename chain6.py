### 修改点：
# 覆盖_extract_tool_and_input函数，修复了返回值多一个换行的问题
# 逻辑：
#     * 让chatgpt补充Follow up问题和Final answer总结
#       * 请求chatgpt加stop参数，禁止其补充Intermediate answer:的结果
#     * 让搜索来补充Intermediate answer:的结果
import _env


import os
import sys
import time
import datetime
import langchain
from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.agents import Agent
from langchain.agents import load_tools
from langchain import OpenAI
from langchain.agents import initialize_agent, Tool
from langchain import LLMMathChain, SerpAPIWrapper
import openai

from langchain.agents.self_ask_with_search.base import SelfAskWithSearchAgent


openai.log="debug"




llm = OpenAI(model_name=_env.model_name, temperature=0,openai_api_key=_env.api_key)

search = SerpAPIWrapper(serpapi_api_key=_env.google_search_api_key)
tools = [
    Tool(
        name="Intermediate Answer",
        func=search.run,
        description = "useful for when you need to answer questions about current events"
    )
]



class MySelfAskWithSearchAgent(SelfAskWithSearchAgent):
    """Agent for the MRKL chain."""
    def _extract_tool_and_input(self, text: str) -> Optional[Tuple[str, str]]:
        followup = "Follow up:"
        last_line = text.strip(" ").strip("\n").split("\n")[-1]
        print(f'text:{text}')
        print(f'last_line:{last_line}')


        if followup not in last_line:
            finish_string = "So the final answer is: "
            if finish_string not in last_line:
                return None
            return "Final Answer", last_line[len(finish_string) :]

        after_colon = text.split(":")[-1]

        if " " == after_colon[0]:
            after_colon = after_colon[1:]

        return "Intermediate Answer", after_colon


from langchain.agents.loading import AGENT_TO_CLASS
AGENT_TO_CLASS["my-self-ask-with-search"]=MySelfAskWithSearchAgent


self_ask_with_search = initialize_agent(tools, llm, agent="my-self-ask-with-search", verbose=True)





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
