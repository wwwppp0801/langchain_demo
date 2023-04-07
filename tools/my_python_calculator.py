import sys
import subprocess
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

def get_python_coder_tool(python_path:str) -> BaseTool:
    name="CodeInterpreter"
    #description="you can write python code to solve the problem,you must write, you must write a complete python program , print the answer to stdout"
    description="Write python code to solve math questions. You MUST write a COMPLETE python program in every step, include all import and variable initialization. You can't use network. You MUST print the final result."
    def extract_code_blocks(string):
        import re
        pattern = r'```(?:python)?\s*(.*?)\s*```' 
        code_blocks = re.findall(pattern, string, flags=re.DOTALL)
        # Return the list of code blocks as output
        return code_blocks

    def run_python_code(code:str):
        #python_executor = PythonREPL()
        #code = code.split("```")[1].strip("\n\t\r ")
        #print(code)
        code_blocks=extract_code_blocks(code)
        
        if len(code_blocks)==0:
            return "no code for "+name+" to resolve the problem"
            #raise NotImplementedError("no code here",code)
        code_str="\n".join(code_blocks)
        p = subprocess.Popen([python_path, '-c', code_str], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        output = out.decode() + err.decode()
        if output.strip(" \t\n")=="":
            output="no print out answers"
        return output


    async def _arun(self, tool_input: str) -> str:
        raise NotImplementedError("Tool does not support async")

    return Tool(
        name=name,
        description=description,
        func=run_python_code,
        coroutine=_arun,
    )
if __name__=="__main__":
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
    import _env
    code='''
```

import sympy as sp

x = sp.Symbol('x')
f = 5*x**2 + 8*x - 16
f_prime = sp.diff(f, x)
critical_points = sp.solve(f_prime, x)
second_derivatives = [sp.diff(f, x, 2).subs(x, cp) for cp in critical_points]

for i in range(len(critical_points)):
    if second_derivatives[i] > 0:
        print(f"The critical point {critical_points[i]} is a minimum")
    elif second_derivatives[i] < 0:
        print(f"The critical point {critical_points[i]} is a maximum")
    else:
        print(f"The critical point {critical_points[i]} is an inflection point")
```

'''
    code='''
```
# Let's use Python to solve this problem
# We can use a loop to iterate through all possible combinations of coins
# We will start with 0 to 100 10 cent coins and calculate the number of 5 cent coins needed to make 7 yuan
# We will stop when we find a combination that adds up to 7 yuan

for i in range(101):
    for j in range(101):
        if i*10 + j*5 == 700:
            print("Number of 10 cent coins:", i)
            print("Number of 5 cent coins:", j)
            break
```
'''
#    code='''
#
#```
## Round the number of coins to the nearest integer
#num_5_cents = round(sol[x])
#num_10_cents = round(sol[y])
#
## Print the final answer
#print("Number of 5 cent coins:", num_5_cents)
#print("Number of 10 cent coins:", num_10_cents)
#```
#'''

    result=get_python_coder_tool(_env.python_path)._run(code)
    
#    code='''
#
#```python
#import hashlib
#
#string = "123456"
#hash_object = hashlib.md5(string.encode())
#print(hash_object.hexdigest())
#```
#'''
#    result=get_python_coder_tool()._run(code)
    print(result)
