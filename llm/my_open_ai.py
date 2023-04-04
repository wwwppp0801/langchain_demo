from langchain.llms.openai import OpenAIChat
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


class MyOpenAIChat(OpenAIChat):
    last_messages:List[str] = None
    def _get_chat_params(
             self, prompts: List[str], stop: Optional[List[str]] = None
             ) -> Tuple:
        messages, params = super()._get_chat_params(prompts=prompts, stop=stop)
        self.last_messages = messages
        return messages,params

