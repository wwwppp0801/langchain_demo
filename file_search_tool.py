import _env
import filetype
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
from langchain.document_loaders import UnstructuredPDFLoader, OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
        raise NotImplementedError("CustomFileSearchTool does not support async")
    def load_from_file(self,filename:str) ->None:
        #loader = TextLoader("./data/PaulGrahamEssays/worked.txt")
        persist_directory="./persist_directory/"+os.path.basename(filename)
        if os.path.exists(persist_directory):
            print("The path exists:"+persist_directory)
            self.ruff_db = Chroma(collection_name="ruff",persist_directory=persist_directory)
        else:
            print("The path does not exist:"+persist_directory)
            os.makedirs(persist_directory, exist_ok=True)
            kind = filetype.guess(filename)
            file_extension = os.path.splitext(filename)[1]
            if kind is not None and kind.extension == "pdf":
                loader = UnstructuredPDFLoader(filename)
                print("The file is a pdf")
            elif kind is None and file_extension==".txt":
                loader = TextLoader(filename)
                print("The file is a txt")
            else:
                raise NotImplementedError("CustomFileSearchTool does not support type")
            docs = loader.load()
            text_splitter = CharacterTextSplitter(chunk_size=800, separator="\n", chunk_overlap=0)
            ruff_texts = text_splitter.split_documents(docs)
            self.ruff_db = Chroma.from_documents(ruff_texts, collection_name="ruff",persist_directory=persist_directory)
            self.ruff_db.persist()
        #self.ruff_db = Chroma.from_documents(ruff_texts, collection_name="ruff")
        self.ruff = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=self.ruff_db)
        #self.ruff = VectorDBQA.from_chain_type(llm=llm, chain_type="map_reduce", vectorstore=self.ruff_db)
    # TODO: this is for backwards compatibility, remove in future
    def __init__(
        self, name: str, description: str, **kwargs: Any
    ) -> None:
        super(CustomFileSearchTool, self).__init__(
            name=name, description=description, **kwargs
        )
        #self.ruff_db = Chroma.from_documents([], collection_name="ruff",persist_directory="./persist_directory")
        #self.ruff_db = Chroma(collection_name="ruff",persist_directory="./persist_directory")
        #self.ruff_db.persist()
        #self.ruff_db = Chroma.from_documents(ruff_texts, collection_name="ruff")
        #self.ruff = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=self.ruff_db)
        #ruff_db = Chroma.from_documents(ruff_texts, embeddings, collection_name="ruff",persist_directory=persist_directory)




if __name__ == '__main__': 
    print("Welcome to OpenAI, please ask your question")
    tool = CustomFileSearchTool(
            name = "File",
            #description = "you must use it first, when you need to answer questions about product after sale",
            description = "Any question must first use this tool, using the original question as Action Input",
            )
    #tool.load_from_file("./upload/progit.pdf")

    #tool.load_from_file("./data/PaulGrahamEssays/worked.txt")
    tool.load_from_file("./data/PaulGrahamEssays/worked.txt")
    #result=tool._run("after sale")
    import openai
    openai.log="debug"
    result=tool._run("McCarthy means what?")
    #result=tool._run("who setup Y Combinator")
    #result=tool._run("progit 的作者是谁？如果git pull的时候发生了冲突要怎么解决?")
    print(result)

