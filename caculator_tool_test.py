from langchain.chains.llm_math.base import LLMMathChain
from langchain.llms.base import BaseLLM
from langchain.tools.base import BaseTool
from langchain.llms import OpenAI
from langchain.agents.tools import Tool

import configparser
import openai


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
def gcd(a, b):
  if b == 0:
    return a
  else:
    r = a % b
    return gcd(b, r)
print(37593*67//gcd(37593,67))
```
```output
2518731
```
Answer: 2518731

Begin.



Question: {question}
"""
	return  PromptTemplate(input_variables=["question"], template=_PROMPT_TEMPLATE)


class MyLLMMathChain(LLMMathChain):
	prompt = _get_math_prompt()

def _get_my_llm_math(llm: BaseLLM) -> BaseTool:
    return Tool(
        name="Calculator",
        description="Useful for when you need to answer questions about math.",
        func=MyLLMMathChain(llm=llm, callback_manager=llm.callback_manager).run,
        coroutine=MyLLMMathChain(llm=llm, callback_manager=llm.callback_manager).arun,
    )

llm = OpenAI(model_name=model_name, temperature=0.0,openai_api_key=openai.api_key)

tool= _get_my_llm_math(llm)


result=tool.run('"largest prime number smaller than 65"')
print(result)

