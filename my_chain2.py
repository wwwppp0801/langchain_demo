### 修改点：
# * 修改agent的主prompt：format_instructions，重复了一次格式，避免“Action 1:”，“Thought 1:”这样的回复
# * 修改LLMMathChain的主prompt：强制生成python代码，避免语言模型自行推断
# * 修改temperature 参数为1

import os
import openai
openai.log="debug"

import configparser


FORMAT_INSTRUCTIONS = """Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question"""

PREFIX = """Answer the following questions as best you can. You have access to the following tools, no calculate result manually:"""
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
from langchain.chains.llm_math.base import LLMMathChain

from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from langchain.agents import load_tools
from langchain.agents import initialize_agent


from langchain.llms.base import BaseLLM
from langchain.tools.base import BaseTool


from langchain.agents.mrkl.base import ZeroShotAgent


def _get_math_prompt():
	from langchain.prompts.prompt import PromptTemplate
	_PROMPT_TEMPLATE = """You are GPT-3, and you can't do math.

write python code to do the math calculation, and write the output bellow

Question: ${{Question with hard calculation.}}
```python
${{Code that prints what you need to know}}
```
```output
${{Output of your code}}
```
Answer: ${{Answer}}

Example:
Question: What is 37593 * 67?
```python
print(37593 * 67)
```
```output
2518731
```
Answer: 2518731

Begin.



Question: {question}
"""
	return  PromptTemplate(input_variables=["question"], template=_PROMPT_TEMPLATE)
	

class MyZeroShotAgent(ZeroShotAgent):
    """Agent for the MRKL chain."""

from langchain.agents.loading import AGENT_TO_CLASS
AGENT_TO_CLASS["my-zero-shot"]=MyZeroShotAgent

class MyLLMMathChain(LLMMathChain):
	prompt = _get_math_prompt()

def _get_my_llm_math(llm: BaseLLM) -> BaseTool:
    return Tool(
        name="Calculator",
        description="Useful for when you need to answer questions about math.",
        func=MyLLMMathChain(llm=llm, callback_manager=llm.callback_manager).run,
        coroutine=MyLLMMathChain(llm=llm, callback_manager=llm.callback_manager).arun,
    )




# 创建一个ConfigParser对象
config = configparser.ConfigParser()

# 读取一个INI文件
config.read("config.ini")

# 设置组织ID和API密钥
openai.organization=config.get("main", "organization")
openai.api_key=config.get("main", "api_key")
model_name=config.get("main", "model")
google_search_api_key=config.get("main","google_search_api_key")

## llm
llm = OpenAI(model_name=model_name, temperature=1.0,openai_api_key=openai.api_key)


### demo4

os.environ["SERPAPI_API_KEY"] = google_search_api_key

#tools = load_tools(["serpapi", "llm-math"], llm=llm)
from langchain.agents.load_tools import _LLM_TOOLS
_LLM_TOOLS["my-llm-math"]= _get_my_llm_math
tools = load_tools(["serpapi", "my-llm-math"], llm=llm)
agent = initialize_agent(tools, llm, agent="my-zero-shot", verbose=True,
                         agent_kwargs={"format_instructions":FORMAT_INSTRUCTIONS,"prefix":PREFIX})
agent.run("Who is the current leader of Japan? What is the largest prime number that is smaller than their age")
#agent.run(" What is the largest prime number that is smaller than 1293812746")



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
