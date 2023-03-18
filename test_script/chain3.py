### 修改点：
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import _env

import os
import openai


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


from langchain.document_loaders import UnstructuredFileLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.chains.question_answering import load_qa_chain


sm_loader = UnstructuredFileLoader("./data/muir_lake_tahoe_in_winter.txt")
sm_doc = sm_loader.load()

lg_loader = UnstructuredFileLoader("./data/PaulGrahamEssays/worked.txt")
lg_doc = lg_loader.load()

def doc_summary(docs):
    print (f'You have {len(docs)} document(s)')

    num_words = sum([len(doc.page_content.split(' ')) for doc in docs])

    print (f'You have roughly {num_words} words in your docs')
    print ()
    print (f'Preview: \n{docs[0].page_content.split(". ")[0]}')

doc_summary(sm_doc)
doc_summary(lg_doc)
#print(sm_doc)
#print(lg_doc)




# 设置组织ID和API密钥
os.environ["SERPAPI_API_KEY"] = _env.google_search_api_key

## llm
llm = OpenAI(model_name=_env.model_name, temperature=1.0,openai_api_key=_env.api_key)


### demo4
#chain = load_summarize_chain(llm, chain_type="stuff", verbose=True)

#chain.run(sm_doc)

## 出错，文章太长，最大4096个token
#chain.run(lg_doc)


chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=True)
openai.log="debug"
#chain.run(sm_doc)

## 出错，文章太长，最大4096个token
#chain.run(lg_doc)

from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size = 400,
    chunk_overlap = 0
)


lg_docs = text_splitter.split_documents(lg_doc)

doc_summary(lg_docs)
doc_summary(lg_docs[:5])
chain.run(lg_docs[:5])
#### mapreduce 报错

#File "/opt/homebrew/Caskroom/miniforge/base/lib/python3.9/site-packages/langchain/llms/openai.py", line 627, in _generate
#    messages, params = self._get_chat_params(prompts, stop)
#  File "/opt/homebrew/Caskroom/miniforge/base/lib/python3.9/site-packages/langchain/llms/openai.py", line 613, in _get_chat_params
#    raise ValueError(
#ValueError: OpenAIChat currently only supports single prompt, go

#修改了langchain/llms/openai.py的代码，把多个prompt join成一个



