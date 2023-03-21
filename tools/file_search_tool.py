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
from langchain.llms.base import BaseLLM

from langchain.agents import initialize_agent, Tool
from langchain.tools import BaseTool
from langchain import LLMMathChain, SerpAPIWrapper
from langchain.document_loaders import WebBaseLoader

from langchain.embeddings.base import Embeddings


from typing import Any, Dict, List, Optional





from pathlib import Path
import os
current_dir = os.getcwd()


import json


class MyVectorDBQA(VectorDBQA):

    def _call(self, inputs: Dict[str, str]) -> Dict[str, Any]:
        """Run similarity search and llm on input query.

        If chain has 'return_source_documents' as 'True', returns
        the retrieved documents as well under the key 'source_documents'.

        Example:
        .. code-block:: python

        res = vectordbqa({'query': 'This is my query'})
        answer, docs = res['result'], res['source_documents']
        """
        question = inputs[self.input_key]

        if self.search_type == "similarity":
            docs = self.vectorstore.similarity_search(
                question, k=self.k, **self.search_kwargs
            )
        elif self.search_type == "mmr":
            docs = self.vectorstore.max_marginal_relevance_search(
                question, k=self.k, **self.search_kwargs
            )
        else:
            raise ValueError(f"search_type of {self.search_type} not allowed.")
        

        docs=docs[:3]
        
        print(docs,file=sys.stderr)
        
        #raise ValueError(f"stop here")
        
        answer, _ = self.combine_documents_chain.combine_docs(docs, question=question)

        if self.return_source_documents:
            return {self.output_key: answer, "source_documents": docs}
        else:
            return {self.output_key: answer}





class CustomFileSearchTool(BaseTool):
    #description = customFileSearchIntent
    persist_directory:str = ""
    ruff_db:Chroma = None
    ruff:VectorDBQA= None
    llm:BaseLLM= None
    embeddings:Embeddings =None
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
            self.ruff_db = Chroma(collection_name="ruff",persist_directory=persist_directory,embedding_function=self.embeddings)
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
            #text_splitter = CharacterTextSplitter(chunk_size=800, separator="\n", chunk_overlap=0)
            text_splitter = CharacterTextSplitter(chunk_size=800, separator="", chunk_overlap=0)
            ruff_texts = text_splitter.split_documents(docs)
            self.ruff_db = Chroma.from_documents(ruff_texts,self.embeddings, collection_name="ruff",persist_directory=persist_directory)
            self.ruff_db.persist()
        #self.ruff_db = Chroma.from_documents(ruff_texts, collection_name="ruff")
        
        #self.ruff = MyVectorDBQA.from_chain_type(llm=self.llm, chain_type="stuff", vectorstore=self.ruff_db)
        #self.ruff.k=3
        
        self.ruff = MyVectorDBQA.from_chain_type(llm=self.llm, chain_type="map_reduce", vectorstore=self.ruff_db)
        self.ruff.k=6
        #self.ruff = VectorDBQA.from_chain_type(llm=llm, chain_type="map_reduce", vectorstore=self.ruff_db)
    # TODO: this is for backwards compatibility, remove in future
    def __init__(
            self, name: str, description: str,llm: BaseLLM,embeddings, **kwargs: Any
    ) -> None:
        super(CustomFileSearchTool, self).__init__(
            name=name, description=description, **kwargs
        )
        self.embeddings=embeddings
        self.llm=llm
        #self.ruff_db = Chroma.from_documents([], collection_name="ruff",persist_directory="./persist_directory")
        #self.ruff_db = Chroma(collection_name="ruff",persist_directory="./persist_directory")
        #self.ruff_db.persist()
        #self.ruff_db = Chroma.from_documents(ruff_texts, collection_name="ruff")
        #self.ruff = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=self.ruff_db)
        #ruff_db = Chroma.from_documents(ruff_texts, embeddings, collection_name="ruff",persist_directory=persist_directory)


def get_tool(filename,llm,embeddings):
    search = CustomFileSearchTool(
            name = "",
            description = "",
            llm=llm,
            embeddings=embeddings,
            )

    name="FileSearchTool"
    description :str = "Any question must first use this tool, using the original question, in original language, as Action Input"
    
    search.load_from_file(filename)

    def run(query:str):
        docs=search.ruff_db.similarity_search(query)
        doc_strings = [doc.page_content for doc in docs]
        result="\n".join(doc_strings)
        print(len(result),result)
        return result

    async def arun(self, tool_input: str) -> str:
        raise NotImplementedError("Tool does not support async")

    return Tool(
        name=name,
        description=description,
        func=run,
        coroutine=arun,
    )


if __name__ == '__main__': 
    print("Welcome to OpenAI, please ask your question")
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
    import _env
    llm = OpenAI(model_name=_env.model_name, temperature=0.0,openai_api_key=_env.api_key)
    embeddings = OpenAIEmbeddings(openai_api_key=_env.api_key)
    
    #tool=get_tool('./upload/2022中国大陆薪酬趋势报告-CGP-2022-120页.pdf',llm,embeddings)
    #result=tool._run("工资最高的公司")
    
    #tool=get_tool('./upload/worked.txt',llm,embeddings)
    #result=tool._run("who is McCarthy")

    #tool=get_tool('./upload/连城诀.txt',llm,embeddings)
    #result=tool._run("狄云学会了血刀刀法吗")
    
    #tool = CustomFileSearchTool(
    #        name = "File",
    #        #description = "you must use it first, when you need to answer questions about product after sale",
    #        description = "Any question must first use this tool, using the original question as Action Input",
    #        )
    #tool.load_from_file("./upload/progit.pdf")

    #tool.load_from_file("./data/PaulGrahamEssays/worked.txt")
    #tool.load_from_file("./data/PaulGrahamEssays/worked.txt")
    #tool.load_from_file("./upload/射雕utf8.txt")
    #tool.load_from_file("./upload/2022中国大陆薪酬趋势报告-CGP-2022-120页.pdf")
    #result=tool.ruff_db.similarity_search("工资最高的公司")
    #result=tool._run("after sale")
    #import openai
    #openai.log="debug"
    #result=tool._run("郭靖的母亲是谁")
    #result=tool._run("progit 的作者是谁？如果git pull的时候发生了冲突要怎么解决?")



    filename='./upload/连城诀.txt'
    question="狄云学会了血刀刀法吗"
    tool = CustomFileSearchTool(
            name = "File",
            #description = "you must use it first, when you need to answer questions about product after sale",
            description = "Any question must first use this tool, using the original question as Action Input",
            llm=llm,
            embeddings=embeddings,
            )
    tool.load_from_file(filename)

    result=tool._run(question)
    print()
    print()
    print()
    print("Result:")
    from termcolor import colored
    print(colored(result, "green"))
    print()
    print()
    print()


    #print(result)

