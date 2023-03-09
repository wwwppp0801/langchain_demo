from langchain.utilities.serpapi import SerpAPIWrapper
from langchain.tools.base import BaseTool
from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple
from langchain.agents.tools import Tool
import json


def remove_http_keys(d):
  # 如果d是一个字典
  if isinstance(d, dict):
    # 遍历d的所有键
    for key in list(d.keys()):
      # 如果键对应的值是以"http"开头的字符串
      if isinstance(d[key], str) and d[key].startswith("http"):
        # 使用pop()方法删除该键，并提供一个空字符串作为默认值
        d.pop(key, "")
      # 否则，递归地对该键对应的值进行处理
      else:
        remove_http_keys(d[key])
  # 如果d是一个列表
  elif isinstance(d, list):
    # 遍历d的所有元素
    for item in d:
      # 递归地对每个元素进行处理
      remove_http_keys(item)
  # 返回处理后的d
  return d


class MySerpAPIWrapper(SerpAPIWrapper):
    @staticmethod
    def _process_response(res: dict) -> str:
        """Process response from SerpAPI."""
        print("")
        print("")
        print("")
        json_str = json.dumps(list(res.keys()))
        print(json_str)
        print("")
        print("")
        print("")
        if "error" in res.keys():
            raise ValueError(f"Got error from SerpAPI: {res['error']}")
        if "answer_box" in res.keys() and "answer" in res["answer_box"].keys():
            toret = res["answer_box"]["answer"]
        elif "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret = res["answer_box"]["snippet"]
        elif (
            "answer_box" in res.keys()
            and "snippet_highlighted_words" in res["answer_box"].keys()
        ):
            toret = res["answer_box"]["snippet_highlighted_words"][0]
        ## 直接把结构化数据放在Thought里，llm能认的，这个能回答北京天气了
        elif (
            "answer_box" in res.keys()
        ):

            toret = str(res["answer_box"])
        elif (
            "sports_results" in res.keys()
            and "game_spotlight" in res["sports_results"].keys()
        ):
            toret = res["sports_results"]["game_spotlight"]
        elif (
            "knowledge_graph" in res.keys()
            and "description" in res["knowledge_graph"].keys()
        ):
            toret = res["knowledge_graph"]["description"]
        elif (
            "knowledge_graph" in res.keys()
        ):
            toret = json.dumps(remove_http_keys(res["knowledge_graph"]))
        elif "snippet" in res["organic_results"][0].keys():
            toret = res["organic_results"][0]["snippet"]
            #### 看了一下结果，感觉相关问题的质量比较高
            if 'related_questions' in res:
                toret += "\n".join(map(lambda r:
                                       "\n".join([r.get(key, '') for key in ['question','snippet','title']]),
                                       res['related_questions'][:3])
                                   )
        else:
            toret = "No good search result found"
        return toret

def _get_serpapi(**kwargs: Any) -> BaseTool:
    return Tool(
        name="Search",
        description="A search engine. Useful for when you need to answer questions about current events. Input should be a search query.",
        func=MySerpAPIWrapper(**kwargs).run,
        coroutine=MySerpAPIWrapper(**kwargs).arun,
    )

if __name__=="__main__":
    import _env
    tool=_get_serpapi(serpapi_api_key=_env.google_search_api_key)
    #res=tool._run("Who discovered the molecular formula of amino acids?")
    
    #res=tool._run("Order of planets by mass")
    #print(res)


    import json

    # 打开json文件
    with open("test3.json", "r") as f:
      # 读取并解析json数据，返回一个dict
      data = json.load(f)

    # 打印dict
    print(remove_http_keys({"a":data['planets_by_mass']}))

