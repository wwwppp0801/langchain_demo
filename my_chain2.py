### 修改点：
# * 修改agent的主prompt：format_instructions，重复了一次格式，避免“Action 1:”，“Thought 1:”这样的回复
# * 修改LLMMathChain的主prompt：强制生成python代码，避免语言模型自行推断
# * 修改temperature 参数为0
# * 修改MyZeroShotAgent，解决多余的"字符
# * 修改MyWolframAlphaQueryRun, 把它当成Calculator来用
# * 修改MyLLMMathChain的prompt, 确保它会生成python代码

import _env

import os
import re
from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple

import openai

openai.log="debug"

import configparser





#FORMAT_INSTRUCTIONS = """Use the following format:
#
#Question: the input question you must answer
#Thought: you should always think about what to do
#Action: the action to take, should be one of [{tool_names}]
#Action Input: the input to the action
#Observation: the result of the action
#... (this Thought/Action/Action Input/Observation can repeat N times)
#Thought: I now know the final answer
#Final Answer: the final answer to the original input question"""
#SUFFIX = """Begin!
#
#Question: {input}
#Thought:{agent_scratchpad}"""

    


from langchain.agents.tools import Tool
from langchain.agents.agent import Agent
from langchain.chains.llm_math.base import LLMMathChain

from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from langchain.agents import load_tools
from langchain.agents import initialize_agent


from langchain.llms.base import BaseLLM
from langchain.tools.base import BaseTool


from langchain.agents.mrkl.base import ZeroShotAgent

from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple
from langchain.tools.base import BaseTool
from langchain.callbacks.base import BaseCallbackManager
    

class MyZeroShotAgent(ZeroShotAgent):
    """Agent for the MRKL chain."""
    ##  Action Input多返回了一个换行符，导致匹配失效
    ## 提取出来的Action Input是largest prime number smaller than 65"
    ## 多了一个引号没处理掉，导致后面的caculator很容易出错（WolframAlpha就接受不了这种输入）
    PREFIX = """Answer the following questions as best you can. You have access to the following tools, no manually actions, :"""

    FORMAT_INSTRUCTIONS = """Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, MUST be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action can repeat N times, N>0)
Thought: I now know the final answer
Final Answer: the final answer to the original input question


"Final Answer:" MUST be include in last line

"""
    SUFFIX = """Begin!

Question: {input}
Thought:{agent_scratchpad}"""


    def _extract_tool_and_input(self, text: str) -> Optional[Tuple[str, str]]:
        def get_action_and_input(llm_output: str) -> Tuple[str, str]:
            """Parse out the action and input from the LLM output.

            Note: if you're specifying a custom prompt for the ZeroShotAgent,
            you will need to ensure that it meets the following Regex requirements.
            The string starting with "Action:" and the following string starting
            with "Action Input:" should be separated by a newline.
            """
            FINAL_ANSWER_ACTION = "Final Answer:"
            if FINAL_ANSWER_ACTION in llm_output:
                return "Final Answer", llm_output.split(FINAL_ANSWER_ACTION)[-1].strip()
            if "final answer" in llm_output:
                return llm_output
            if "Final answer" in llm_output:
                return llm_output
            regex = r"Action: (.*?)\nAction Input: (.*)"
            match = re.search(regex, llm_output, re.DOTALL)
            if not match:
                raise ValueError(f"Could not parse LLM output: `{llm_output}`")
            action = match.group(1).strip()
            action_input = match.group(2)
            return action, action_input.strip("\n").strip(" ").strip('"')
        return get_action_and_input(text)
    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLLM,
        tools: Sequence[BaseTool],
        callback_manager: Optional[BaseCallbackManager] = None,
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Agent:
        return ZeroShotAgent.from_llm_and_tools(llm,tools,callback_manager,prefix,suffix,format_instructions,input_variables,**kwargs)

from langchain.agents.loading import AGENT_TO_CLASS
AGENT_TO_CLASS["my-zero-shot"]=MyZeroShotAgent






## llm
llm = OpenAI(model_name=_env.model_name, temperature=0.0,openai_api_key=_env.api_key)


### demo4

#os.environ["SERPAPI_API_KEY"] = google_search_api_key

tools=[]
#tools = load_tools(["serpapi", "my-llm-math","wolfram-alpha"], llm=llm, serpapi_api_key=google_search_api_key,wolfram_alpha_appid=wolframalpha_appid)
#tools = load_tools(["serpapi"], llm=llm, serpapi_api_key=_env.google_search_api_key)

from langchain.utilities.google_serper import GoogleSerperAPIWrapper
def _get_google_serper(**kwargs: Any) -> BaseTool:
    return Tool(
        name="Serper Search",
        func=GoogleSerperAPIWrapper(**kwargs).run,
        description="A low-cost Google Search API. Useful for when you need to answer questions about current events. Input should be a search query.",
    )


from langchain.tools.google_search.tool import GoogleSearchResults, GoogleSearchRun
from langchain.utilities.google_search import GoogleSearchAPIWrapper

def _get_google_search(**kwargs: Any) -> BaseTool:
    return GoogleSearchRun(api_wrapper=GoogleSearchAPIWrapper(**kwargs))


import my_serp_api_wrapper

#tools.append(_get_google_serper(serper_api_key=_env.google_search_api_key))
#tools.append(_get_google_search(google_api_key=_env.google_search_api_key))

import my_python_calculator


from langchain.tools.wolfram_alpha.tool import WolframAlphaQueryRun
from langchain.utilities.wolfram_alpha import WolframAlphaAPIWrapper

class MyWolframAlphaQueryRun(WolframAlphaQueryRun):
#    name = "Calculator"
#    description = "Useful for when you need to answer questions about math."
    name = "WolframAlpha"
    description = (
        "A wrapper around Wolfram Alpha. "
        "Useful for when you need to answer questions about Math, "
        "Science, Technology, Culture, Society and Everyday Life. "
        "Input should be a search query."
    )
    def _run(self, query: str) -> str:
        """Use the WolframAlpha tool."""
        query=query.strip(" \t\n\"'“”‘’")
        return self.api_wrapper.run(query)



wolframalpha_tool = MyWolframAlphaQueryRun(api_wrapper=WolframAlphaAPIWrapper(wolfram_alpha_appid = _env.wolframalpha_appid))
import my_translator_tool



#query="Who is the current leader of Japan? What is the largest prime number that is smaller than their age"
#query="什么是比特币？它是如何创造出来的？"
#query="谁发现了苯和氨基酸的分子式？"
#query="2023年，谁最有可能是中国的总理"
#query="去年谁是中国的总理"
#query="2000年,谁是中国的总理"
#query="谁是中国历史上任期最长的总理" ## fail 说的温家宝
#query="周恩来当中国国家总理总共多长时间？"
#query="2023年，速度最快的显卡是什么？价格是多少？"
#query="2023年，价格最贵的显卡是什么？价格是多少？"
#query="中国人里，最有名的打过NBA的球员, 现在在干啥？"
#query="把圆周率计算到小数点后1000位"
#query="圆周率，保留小数点后前1000位"
#query="地球与太阳的距离，是土星与太阳的距离的几倍？"
#query="地球与太阳的距离，与土星与太阳的距离的比例？"
#query="地球与太阳的距离，是水星与太阳的距离的几倍？"
#query="地球与太阳的距离，与水星与太阳的距离的比例？"
#query="把太阳系的行星按照质量排序"
#query="人类发现的最大的恒星，按照质量排序的前十名是哪些？"
query="人类发现的最大的恒星，按照质量排序的前十名是哪些？"
#query="著名的小提琴协奏曲《贝多芬》是由哪位作曲家创作的？它的调号是什么？"
#query="Which composer wrote the famous violin concerto \"Beethoven\"? What is its key signature?"
#query=" What is the largest prime number that is smaller than 1293812746"
#query="北京今天的温度是多少摄氏度？"
#query="推荐5首周杰伦在2002年之前创作的歌"
#query="推荐1首周杰伦在2002年之前创作的歌"
#query="把1234分解质因数" ##fail
#query="Factor 1234 into prime factors" #使用WolframAlpha是可以的
#query="求 x^2+9x-5 的最小值点" #使用WolframAlpha是可以的
#query="已知引力常量为G，地球质量为M，地球半径为R，地球表面重力加速度为g，空间站质量为m，空间站在轨道上做圆周运动的向心加速度是多少？" #calculator算出了实际的数字3.718
#query="已知引力常量为G，地球质量为M，地球半径为R，地球表面重力加速度为g，空间站质量为m，空间站在轨道上做圆周运动的周期是多少？" 
#query="截面为等腰直角三角形的圆锥侧面展开图的圆心角弧度为"
#query="如果（sin a + cos a）/（sin a - cos a）=-3，则tan 2a="
#query="Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?"
#query="The cafeteria had 23 apples. If they used 20 to make lunch and bought 6 more, how many apples do they have?"
#query="It takes Amy 4 minutes to climb to the top of a slide. It takes her 1 minute to slide down. The water slide closes in 15 minutes. How many times can she slide before it closes?"
#query="A needle 35 mm long rests on a water surface at 20◦C. What force over and above the needle’s weight is required to lift the needle from contact with the water surface? σ = 0.0728m"

import sys
if len(sys.argv) > 1:
    query=sys.argv[1]
    if len(sys.argv)>=3:
        toolsStr=sys.argv[2]
        for toolStr in toolsStr.split(","):
            #calculator,search,wolframalpha_tool,ch_en_translator,en_ch_translator
            if toolStr == "calculator":
                tools.append( my_python_calculator._get_my_llm_math(llm) )
            elif toolStr == "wolframalpha_tool":
                tools.append(wolframalpha_tool)
            elif toolStr == "en_ch_translator":
                tools.append(my_translator_tool.en_ch_translator)
            elif toolStr == "ch_en_translator":
                tools.append(my_translator_tool.ch_en_translator)
            elif toolStr == "search":
                tools.append(my_serp_api_wrapper._get_serpapi(serpapi_api_key=_env.google_search_api_key))
else:
    tools.append(my_serp_api_wrapper._get_serpapi(serpapi_api_key=_env.google_search_api_key))
    #tools.append( my_python_calculator._get_my_llm_math(llm) )
    tools.append(wolframalpha_tool)
    #tools.append(my_translator_tool.en_ch_translator)
    tools.append(my_translator_tool.ch_en_translator)




print(query)
agent = initialize_agent(tools, llm, agent="my-zero-shot", verbose=True,)
agent.run(query)



### expect output:
out='''
> Entering new AgentExecutor chain...
I need to find out who the current leader of Japan is and their age before I can use a calculator to find the largest prime number smaller than their age.
Action: Search
Action Input: "current leader of Japan"

Observation: Fumio Kishida
Thought:Now that I know who the current leader of Japan is, I can search for their age
Action: Search
Action Input: "Fumio Kishida age"


Observation: 65 years
Thought:Now that I know the age of Fumio Kishida, I can use a calculator to find the largest prime number smaller than their age
Action: Calculator
Action Input: enter "largest prime number smaller than 65"


Observation: Answer: 61

Thought:I now know the final answer for the largest prime number smaller than Fumio Kishida's age
Final Answer: 61

> Finished chain.

'''
