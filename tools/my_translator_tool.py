from langchain.tools.base import BaseTool
from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple
from langchain.agents.tools import Tool
import requests # 导入requests模块
import hashlib # 导入hashlib模块
import random # 导入random模块
import time


def trans(text:str,_from:str ="zh", _to:str="en",baidu_trans_app_id:str="",baidu_trans_secret_key:str=""):
    text=text.strip(" \t\n\"\'“”‘’")
    # 定义要翻译的源语言和目标语言
    from_lang = _from # 中文
    to_lang = _to  # 英文

    # 定义百度翻译API的URL
    url = "http://api.fanyi.baidu.com/api/trans/vip/translate"

    # 定义APP ID和密钥（替换为自己申请的）
    app_id = baidu_trans_app_id
    secret_key = baidu_trans_secret_key

    # 生成随机数
    salt = random.randint(32768, 65536)

    # 计算签名（根据百度翻译API的文档）
    sign = app_id + text + str(salt) + secret_key
    sign = hashlib.md5(sign.encode()).hexdigest()

    # 构造请求参数
    params = {
        "q": text,
        "from": from_lang,
        "to": to_lang,
        "appid": app_id,
        "salt": salt,
        "sign": sign
    }

    # 发送请求并获取响应
    response = requests.get(url, params=params)
    response_json = response.json()
    #print(response_json)

    # 解析响应并打印结果
    result = response_json["trans_result"][0]["dst"]
    ### 免费版限制访问频率
    time.sleep(1)
    
    return result



class TranslatorTool(BaseTool):
    """Tool that takes in function or coroutine directly."""
    name: str = "Translator"
    description: str = "A tool that can translate Chinese to English"
    func: Callable[[str], str]

    def _run(self, tool_input: str) -> str:
        """Use the tool."""
        return self.func(tool_input)

    async def _arun(self, tool_input: str) -> str:
        raise NotImplementedError("Tool does not support async")

    # TODO: this is for backwards compatibility, remove in future
    def __init__(
        self, name: str, func: Callable[[str], str], description: str, **kwargs: Any
    ) -> None:
        """Initialize tool."""
        super(TranslatorTool, self).__init__(
            name=name, func=func, description=description, **kwargs
        )


def ch_en_translator(baidu_trans_app_id,baidu_trans_secret_key):

    def ch_en_trans(text:str):
        return trans(text,_from="zh",_to="en",
                     baidu_trans_app_id=baidu_trans_app_id,
                     baidu_trans_secret_key=baidu_trans_secret_key)
    return TranslatorTool(
            name="ChEnTranslator",
            description="A tool that can translate Chinese to English",
            func=ch_en_trans,
            )
def en_ch_translator(baidu_trans_app_id,baidu_trans_secret_key): 
    def en_ch_trans(text:str):
        return trans(text,_from="en",_to="zh",
                     baidu_trans_app_id=baidu_trans_app_id,
                     baidu_trans_secret_key=baidu_trans_secret_key)
    return TranslatorTool(
        name="EnChTranslator",
        description="A tool that can translate English to Chinese ",
        func=en_ch_trans,
        )

if __name__ == "__main__":
    # 定义要翻译的文本
    text = "使用python语言，调用百度提供的翻译api，把中文翻译成英文"
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
    import _env
    print(trans(text,
                baidu_trans_app_id=_env.baidu_trans_app_id,
                baidu_trans_secret_key=_env.baidu_trans_secret_key))
    print(ch_en_translator(baidu_trans_app_id=_env.baidu_trans_app_id,
                baidu_trans_secret_key=_env.baidu_trans_secret_key)._run(text))
    print(en_ch_translator(baidu_trans_app_id=_env.baidu_trans_app_id,
                baidu_trans_secret_key=_env.baidu_trans_secret_key)._run(text))
