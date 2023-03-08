
import _env
import os
import openai
openai.log="debug"
import configparser
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from langchain.agents import load_tools
from langchain.agents import initialize_agent





## llm
llm = OpenAI(model_name=_env.model_name, temperature=0.9,openai_api_key=_env.api_key)


### demo4

os.environ["SERPAPI_API_KEY"] = _env.google_search_api_key

tools = load_tools(["serpapi", "llm-math"], llm=llm)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)
#agent.run("Who is the current leader of Japan? What is the largest prime number that is smaller than their age")
agent.run("日本总理是谁？比日本总理的年龄乘以76454123小的最大的质数是多少？")

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


