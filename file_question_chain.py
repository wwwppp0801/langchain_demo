import _env
import openai
openai.log="debug"
from langchain.llms import OpenAI
from tools import file_search_tool 
import sys

from termcolor import colored
from langchain.embeddings import OpenAIEmbeddings

if __name__ == '__main__': 
    if len(sys.argv)!=3:
        print("param error:"+" , ".join(sys.argv))
        print(sys.argv[0]+" {question} {file}")
        quit()
    question=sys.argv[1]
    filename=sys.argv[2]
    print(sys.argv)
    llm = OpenAI(model_name=_env.model_name, temperature=0.0,openai_api_key=_env.api_key)
    openai.organization=_env.organization
    openai.api_key=_env.api_key
    embeddings = OpenAIEmbeddings(openai_api_key=_env.api_key)



    
    tool = file_search_tool.CustomFileSearchTool(
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
    print(colored(result, "green"))
    print()
    print()
    print()

