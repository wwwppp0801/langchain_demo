#### Ask A Book Questions


import os
import openai
openai.log="debug"

import configparser

from langchain.document_loaders import UnstructuredPDFLoader, OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter



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



from langchain.vectorstores import Chroma, Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
#import pinecone


from langchain.text_splitter import CharacterTextSplitter
from langchain import VectorDBQA

import magic
import os
import nltk






# 创建一个ConfigParser对象
config = configparser.ConfigParser()

# 读取一个INI文件
config.read("config.ini")

# 设置组织ID和API密钥
openai.organization=config.get("main", "organization")
openai.api_key=config.get("main", "api_key")
model_name=config.get("main", "model")
google_search_api_key=config.get("main","google_search_api_key")
os.environ["SERPAPI_API_KEY"] = google_search_api_key

## llm
llm = OpenAI(model_name=model_name, temperature=1.0,openai_api_key=openai.api_key)



loader = UnstructuredPDFLoader("./data/field-guide-to-data-science.pdf")
data = loader.load()
print (f'You have {len(data)} document(s) in your data')
print (f'There are {len(data[0].page_content)} characters in your document')

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(data)

print (f'Now you have {len(texts)} documents')





embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)

#pinecone.init(
#    api_key=PINECONE_API_KEY,  # find at app.pinecone.io
#    environment=PINECONE_API_ENV  # next to api key in console
#)
#index_name = "langchain2"
##### 还没申请PINECONE_API_KEY，晚点搞这个


docsearch = Chroma.from_documents(texts, embeddings)
qa = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=docsearch)


query = "who is the author?"
result = qa({"query": query})

print(result)
