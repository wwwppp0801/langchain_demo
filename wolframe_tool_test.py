from langchain.tools.wolfram_alpha.tool import WolframAlphaQueryRun
from langchain.utilities.wolfram_alpha import WolframAlphaAPIWrapper
import configparser
import openai


# 创建一个ConfigParser对象
config = configparser.ConfigParser()

# 读取一个INI文件
config.read("config.ini")

# 设置组织ID和API密钥
openai.organization=config.get("main", "organization")
openai.api_key=config.get("main", "api_key")
model_name=config.get("main", "model")
google_search_api_key=config.get("main","google_search_api_key")
wolframalpha_appid=config.get("main","wolframalpha_appid")

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


wolframalpha_tool = MyWolframAlphaQueryRun(api_wrapper=WolframAlphaAPIWrapper(wolfram_alpha_appid = wolframalpha_appid))
#result=wolframalpha_tool.run('"largest prime number smaller than 65"')
result=wolframalpha_tool.run('largest prime number smaller than 65')
print(result)
