import _env
import openai
openai.log="debug"
import file_search_tool
from file_search_tool import CustomFileSearchTool
import sys

from termcolor import colored

if __name__ == '__main__': 
    if len(sys.argv)!=3:
        print("param error:"+sys.argv)
        print(sys.argv[0]+" {question} {file}")
    question=sys.argv[1]
    filename=sys.argv[2]
    print(sys.argv)
    
    tool = CustomFileSearchTool(
            name = "File",
            #description = "you must use it first, when you need to answer questions about product after sale",
            description = "Any question must first use this tool, using the original question as Action Input",
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

