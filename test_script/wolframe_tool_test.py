import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import _env
from langchain.tools.wolfram_alpha.tool import WolframAlphaQueryRun
from langchain.utilities.wolfram_alpha import WolframAlphaAPIWrapper
import configparser
import openai



class MyWolframAlphaQueryRun(WolframAlphaQueryRun):
    name = "Calculator"
    description = "Useful for when you need to answer questions about math."
    verbose: bool = True
#    name = "Wolfram Alpha"
#    description = (
#        "A wrapper around Wolfram Alpha. "
#        "Useful for when you need to answer questions about Math, "
#        "Science, Technology, Culture, Society and Everyday Life. "
#        "Input should be a search query."
#    )


wolframalpha_tool = MyWolframAlphaQueryRun(api_wrapper=WolframAlphaAPIWrapper(wolfram_alpha_appid = _env.wolframalpha_appid))
#result=wolframalpha_tool.run('"largest prime number smaller than 65"')
result=wolframalpha_tool.run('largest prime number smaller than 65')
print(result)
