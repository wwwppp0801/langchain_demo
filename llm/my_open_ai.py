from langchain.llms.openai import OpenAIChat
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import _env

class MyOpenAIChat(OpenAIChat):
    last_messages:List[str] = None
    def _get_chat_params(
             self, prompts: List[str], stop: Optional[List[str]] = None
             ) -> Tuple:
        messages, params = super()._get_chat_params(prompts=prompts, stop=stop)
        self.last_messages = messages
        params['request_timeout']=60000
        if _env.azure:
            params['engine']=_env.azure_deploy
        return messages,params

