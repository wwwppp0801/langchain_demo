
from langchain.tools.wolfram_alpha.tool import WolframAlphaQueryRun
from langchain.utilities.wolfram_alpha import WolframAlphaAPIWrapper

class MyWolframAlphaQueryRun(WolframAlphaQueryRun):
#    name = "Calculator"
#    description = "Useful for when you need to answer questions about math."
    name = "WolframAlpha"
    description = (
        "A wrapper around Wolfram Alpha. "
        "Useful for when you need to answer questions about Math, "
        "Science, Technology, Culture, Society and Everyday Life. "
        "Input should be a search query."
    )
    def _run(self, query: str) -> str:
        """Use the WolframAlpha tool."""
        query=query.strip(" \t\n\"'“”‘’")
        return self.api_wrapper.run(query)


def get_tool(wolfram_alpha_appid):
    return MyWolframAlphaQueryRun(api_wrapper=WolframAlphaAPIWrapper(wolfram_alpha_appid = wolfram_alpha_appid))

