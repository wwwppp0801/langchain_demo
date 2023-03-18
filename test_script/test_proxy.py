import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import _env
import os
os.environ["OPENAI_API_BASE"]=_env.openai_api_base
import openai
openai.api_key="asjkajs"
import configparser


question="write a python code for quick sort"


openai.log="debug"

context={
        "messages":[
            ]
        }
context["messages"].append(
        {"role": "user", "content": question}
        )
print(context)
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=context["messages"],
    temperature=0,
)
print(response)
