### react-store
# pip install wikipedia -i https://pypi.tuna.tsinghua.edu.cn/simple
# 同样是要修复 text=text.strip("\n \t") 的问题
# 访问wikipedia需要翻墙



import os
import re
from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple

### 少锋的代理
#os.environ["OPENAI_API_BASE"]="http://54.191.171.6:13031/api/closeai/v1"
import openai
#openai.api_key=""
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


from langchain.docstore.base import Docstore

from langchain.agents.agent import Agent, AgentExecutor





# 创建一个ConfigParser对象
config = configparser.ConfigParser()

# 读取一个INI文件
config.read("config.ini")

# 设置组织ID和API密钥
openai.organization=config.get("main", "organization")
openai.api_key=config.get("main", "api_key")
model_name=config.get("main", "model")
google_search_api_key=config.get("main","google_search_api_key")
wolframalpha_appid=config.get("main","wolframalpha_appid")


## llm
llm = OpenAI(model_name=model_name, temperature=0.0,openai_api_key=openai.api_key)


### demo4




#agent = initialize_agent(tools, llm, agent="react-docstore", verbose=True)
from langchain.agents.react.base import ReActChain, ReActDocstoreAgent, DocstoreExplorer
class MyReActDocstoreAgent(ReActDocstoreAgent):
    def _extract_tool_and_input(self, text: str) -> Optional[Tuple[str, str]]:
        text=text.strip("\n \t")
        action_prefix = f"Action {self.i}: "
        if not text.split("\n")[-1].startswith(action_prefix):
            return None
        self.i += 1
        action_block = text.split("\n")[-1]

        action_str = action_block[len(action_prefix) :]
        # Parse out the action and the directive.
        re_matches = re.search(r"(.*?)\[(.*?)\]", action_str)
        if re_matches is None:
            raise ValueError(f"Could not parse action directive: {action_str}")
        return re_matches.group(1), re_matches.group(2)

class MyReActChain(AgentExecutor):
    def __init__(self, llm: BaseLLM, docstore: Docstore, **kwargs: Any):
        """Initialize with the LLM and a docstore."""
        docstore_explorer = DocstoreExplorer(docstore)
        tools = [
            Tool(
                name="Search",
                func=docstore_explorer.search,
                description="Search for a term in the docstore.",
            ),
            Tool(
                name="Lookup",
                func=docstore_explorer.lookup,
                description="Lookup a term in the docstore.",
            ),
        ]
        agent = MyReActDocstoreAgent.from_llm_and_tools(llm, tools)
        super().__init__(agent=agent, tools=tools, **kwargs)



from langchain.docstore import InMemoryDocstore, Wikipedia
docstore=Wikipedia()
agent = MyReActChain(llm=llm, docstore=docstore)




#agent.run("Who is the current leader of Japan? What is the largest prime number that is smaller than their age")
agent.run({"input":"Who is the current leader of Japan? What is the largest prime number that is smaller than their age","chat_history":""})
#agent.run("中国人里，最有名的打过NBA的球员, 现在在干啥？")
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


