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
    

class MyZeroShotAgent(ZeroShotAgent):
    """Agent for the MRKL chain."""
    ##  Action Input多返回了一个换行符，导致匹配失效
    ## 提取出来的Action Input是largest prime number smaller than 65"
    ## 多了一个引号没处理掉，导致后面的caculator很容易出错（WolframAlpha就接受不了这种输入）
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
            regex = r"Action: (.*?)\nAction Input: (.*)"
            match = re.search(regex, llm_output, re.DOTALL)
            if not match:
                raise ValueError(f"Could not parse LLM output: `{llm_output}`")
            action = match.group(1).strip()
            action_input = match.group(2)
            return action, action_input.strip("\n").strip(" ").strip('"')
        return get_action_and_input(text)

from langchain.agents.loading import AGENT_TO_CLASS
AGENT_TO_CLASS["my-zero-shot"]=MyZeroShotAgent






## llm
llm = OpenAI(model_name=_env.model_name, temperature=1.0,openai_api_key=_env.api_key)


### demo4

tools = load_tools(["serpapi"], llm=llm, serpapi_api_key=_env.google_search_api_key)



from langchain.tools.wolfram_alpha.tool import WolframAlphaQueryRun
from langchain.utilities.wolfram_alpha import WolframAlphaAPIWrapper

class MyWolframAlphaQueryRun(WolframAlphaQueryRun):
    name = "Calculator"
    description = "Useful for when you need to answer questions about math."
#    name = "Wolfram Alpha"
#    description = (
#        "A wrapper around Wolfram Alpha. "
#        "Useful for when you need to answer questions about Math, "
#        "Science, Technology, Culture, Society and Everyday Life. "
#        "Input should be a search query."
#    )


wolframalpha_tool = MyWolframAlphaQueryRun(api_wrapper=WolframAlphaAPIWrapper(wolfram_alpha_appid = _env.wolframalpha_appid))
tools.append(wolframalpha_tool)

FORMAT_INSTRUCTIONS = """To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, MUST be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
{ai_prefix}: [your response here]
```"""

#agent = initialize_agent(tools, llm, agent="my-zero-shot", verbose=True,
#                         agent_kwargs={"format_instructions":FORMAT_INSTRUCTIONS,"prefix":PREFIX})
agent = initialize_agent(tools, llm, agent="conversational-react-description", verbose=True,
                         agent_kwargs={"format_instructions":FORMAT_INSTRUCTIONS})
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

