import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

#### Ask A Book Questions
import _env

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


from langchain.text_splitter import CharacterTextSplitter
from langchain import VectorDBQA
from langchain.document_loaders import DirectoryLoader
#import pinecone

import magic
import os
import nltk






os.environ["SERPAPI_API_KEY"] = _env.google_search_api_key


## llm
llm = OpenAI(model_name=_env.model_name, temperature=1.0,openai_api_key=_env.api_key)

#loader = UnstructuredFileLoader("./data/muir_lake_tahoe_in_winter.txt")
#sm_doc = loader.load()

loader = DirectoryLoader('./data/PaulGrahamEssaySmall/', glob='**/*.txt')

documents = loader.load()

text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

texts = text_splitter.split_documents(documents)

#embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)

#docsearch = Chroma.from_documents(texts, embeddings)
docsearch = Chroma.from_documents(texts)


qa = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=docsearch)

#query = "What did McCarthy discover?"
query = "McCarthy means what?"
#query = "write a sort function in python:"
print(qa.run(query))


qa = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=docsearch, return_source_documents=True)
query = "What did McCarthy discover?"
result = qa({"query": query})

print(result)
