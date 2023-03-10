import _env
from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple
import os
import sys
import time
import datetime
from langchain.chains import VectorDBQA
from langchain.llms import OpenAI
from langchain.document_loaders import TextLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter

from langchain.agents import initialize_agent, Tool
from langchain.tools import BaseTool
from langchain import LLMMathChain, SerpAPIWrapper
from langchain.document_loaders import WebBaseLoader

llm = OpenAI(model_name="gpt-3.5-turbo", temperature=1.0,openai_api_key=_env.api_key)

#load Profile，hard code

#定义本地文件搜索  -> 加载 fitness doc
#loader = TextLoader("after_sale.txt")
#loader = TextLoader("./data/PaulGrahamEssays/worked.txt")
#docs = loader.load()
#text_splitter = CharacterTextSplitter(chunk_size=800, separator="\n", chunk_overlap=0)
#embeddings = OpenAIEmbeddings()
#ruff_texts = text_splitter.split_documents(docs)
#
#ruff_db = Chroma.from_documents(ruff_texts, embeddings, collection_name="ruff")
#ruff = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=ruff_db)
#
#search = SerpAPIWrapper()



from pathlib import Path
import os
current_dir = os.getcwd()


import json
#Tool3
class CustomFileSearchTool(BaseTool):
    #description = customFileSearchIntent
    persist_directory:str = ""
    ruff_db:Chroma = None
    ruff:VectorDBQA= None
    def _run(self, query: str) -> str:
        """Use the tool."""
        
        return self.ruff.run(query)
    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BingSearchRun does not support async")
    def load_from_file(self,filename:str) ->None:
        #loader = TextLoader("./data/PaulGrahamEssays/worked.txt")
        loader = TextLoader(filename)
        docs = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=800, separator="\n", chunk_overlap=0)
        ruff_texts = text_splitter.split_documents(docs)
        self.ruff_db = Chroma.from_documents(ruff_texts, collection_name="ruff")
        self.ruff = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=self.ruff_db)
    # TODO: this is for backwards compatibility, remove in future
    def __init__(
        self, name: str, description: str, **kwargs: Any
    ) -> None:
        super(CustomFileSearchTool, self).__init__(
            name=name, description=description, **kwargs
        )
        #ruff_db = Chroma.from_documents(ruff_texts, embeddings, collection_name="ruff",persist_directory=persist_directory)




if __name__ == '__main__': 
    print("Welcome to OpenAI, please ask your question")
    tool = CustomFileSearchTool(
            name = "File",
            #description = "you must use it first, when you need to answer questions about product after sale",
            description = "Any question must first use this tool, using the original question as Action Input",
            )
    tool.load_from_file("./data/PaulGrahamEssays/worked.txt")
    #result=tool._run("after sale")
    import openai
    openai.log="debug"
    #result=tool._run("McCarthy means what?")
    result=tool._run("who setup Y Combinator")
    print(result)

