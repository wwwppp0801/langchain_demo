from langchain.agents.tools import Tool
from langchain.chains.llm_math.base import LLMMathChain
from langchain.llms.base import BaseLLM
from langchain.tools.base import BaseTool
from langchain.python import PythonREPL



class MyLLMMathChain(LLMMathChain):
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


"Answer:" MUST be include in last line

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
    prompt = _get_math_prompt()


def _get_my_llm_math(llm: BaseLLM) -> BaseTool:
    return Tool(
        name="Calculator",
        description="Useful for when you need to answer questions about math.",
        func=MyLLMMathChain(llm=llm, callback_manager=llm.callback_manager).run,
        coroutine=MyLLMMathChain(llm=llm, callback_manager=llm.callback_manager).arun,
    )

def get_python_coder_tool() -> BaseTool:
    def extract_code_blocks(string):
        import re
        pattern = r'```(?:python)?\s*(.*?)\s*```' 
        code_blocks = re.findall(pattern, string, flags=re.DOTALL)
        # Return the list of code blocks as output
        return code_blocks

    def run_python_code(code:str):
        python_executor = PythonREPL()
        #code = code.split("```")[1].strip("\n\t\r ")
        code_blocks=extract_code_blocks(code)
        if len(code_blocks)==0:
            raise NotImplementedError("no code here",code)
        output = python_executor.run(code_blocks[0])
        #print(code)
        #print(output)
        return output


    async def _arun(self, tool_input: str) -> str:
        raise NotImplementedError("Tool does not support async")

    return Tool(
        name="PythonCoder",
        description="you can write python code to solve the problem",
        func=run_python_code,
        coroutine=_arun,
    )
if __name__=="__main__":
    code='''

```
import hashlib

string = "123456"
hash_object = hashlib.md5(string.encode())
print(hash_object.hexdigest())
```
'''
    result=get_python_coder_tool()._run(code)
    
    code='''

```python
import hashlib

string = "123456"
hash_object = hashlib.md5(string.encode())
print(hash_object.hexdigest())
```
'''
    result=get_python_coder_tool()._run(code)
    print(result)
