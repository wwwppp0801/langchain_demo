
from langchain.agents.mrkl.base import ZeroShotAgent

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from langchain.tools.base import BaseTool
from langchain.callbacks.base import BaseCallbackManager
from langchain.agents.agent import AgentExecutor
from langchain.llms.base import BaseLLM
from langchain.agents.agent import Agent
from langchain.agents.tools import Tool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import re
import jinja2
import json
import yaml
from pydantic import BaseModel, root_validator
from langchain.llms import OpenAI
from langchain.agents.tools import InvalidTool

from langchain.schema import AgentAction, AgentFinish
import sys
import os
import requests

def get_tools_from_api_doc(api_doc:Dict)->List[BaseTool]:
    
    def generateToolRunFunc(url,method,**args):
        def run(input:str):
            input=input.strip(" \t\n")
            headers = {
                ## 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            }
            #   "auth":{
            #         "type":"service_http",
            #         "authorization_type":"bearer",
            #         "verification_tokens":{
            #         "openai":"43e40eb7b346427b9a3da3050a6c58c5"
            #         }
            #     },
            
            ## https://www.wolframalpha.com/ 用 service_http鉴权，搞不定
            # if manifest_doc["auth"]["type"]=="service_http":
            #     headers["Authorization"]=f"Bearer {manifest_doc["auth"]}"

            headers = {"Content-Type": "application/json","Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"}
            params={}
            if input[0]=="{":
                params=json.loads(input)
            data=json.dumps(json.loads(input))
            # 根据请求方法发送请求
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, params=params, data=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, params=params, data=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError('Unsupported HTTP method: {}'.format(method))
            print(f"call plugin url:{url}, status_code:{response.status_code}, body:{response.text}",file=sys.stderr)
            return f'status_code:{response.status_code}, body:{response.text}'
        return run

    list=[]
    base_url=api_doc["servers"][0]["url"]
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
    import _env
    if _env.plugin_base_url:
        base_url=_env.plugin_base_url
    for path in api_doc["paths"]:
        for method in api_doc["paths"][path]:
            one_api=api_doc["paths"][path][method]
            name=one_api["operationId"]
            description=one_api["summary"]
            url=f'{base_url}{path}'
            tool=Tool(
                name=name,
                func=generateToolRunFunc(url=url,method=method,api_doc=one_api),
                description=description,
                #调用到tool的时候，不需要再次调用llm
                return_direct=True,
            )
            list.append(tool)
    return list
            


class CallPluginAgent(ZeroShotAgent):
    """Agent for the CallPlugin."""

    plugin_profile:Dict=None


    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return self.plugin_profile['prompt']['key_terms']['Thought']+":"

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return self.plugin_profile['prompt']['key_terms']['Observation']+":"

    def _extract_tool_and_input(self, text: str) -> Optional[Tuple[str, str]]:
        key_terms=self.plugin_profile['prompt']["key_terms"]
        def extract_real_action(raw_action:str):
            regex = r"\"(.*?)\""
            match = re.search(regex, raw_action, re.DOTALL)
            if match != None:
                return match.group(1)
            return raw_action
        def get_action_and_input(llm_output: str) -> Tuple[str, str]:

            FINAL_ANSWER_ACTION = f'{key_terms["Final_Answer"]}:'
            if FINAL_ANSWER_ACTION in llm_output:
                return key_terms["Final_Answer"], llm_output.split(FINAL_ANSWER_ACTION)[-1].strip()
            regex = re.compile(f'{key_terms["Action"]}:(.*?)\n{key_terms["Action_Input"]}:(.*)',re.DOTALL)
            match = re.search(regex, llm_output)
            if not match:
                #return "Final Answer","<not for sure>" + llm_output
                #强制生成一个final answer

                #return "generate","now i can summarize the answer\n"
                return key_terms["Final_Answer"], llm_output

                #if "final answer" in llm_output:
                #    return "Final Answer", llm_output
                #if "Final answer" in llm_output:
                #    return "Final Answer", llm_output
                #raise ValueError(f"Could not parse LLM output: `{llm_output}`")
            before_action = llm_output[:match.start()]
            action = match.group(1).strip()
            action = extract_real_action(action)
            action_input = match.group(2).strip("\n \"\t`")
            if action_input.startswith("json"):
                action_input=action_input[4:]
            ## 压缩json里的空格
            try:
                action_input=json.dumps(json.loads(action_input),ensure_ascii=False)
            except Exception as e:
                pass
            return action, action_input , f'{before_action}{key_terms["Action"]}: {action}\n{key_terms["Action_Input"]}: \n```\n{action_input}\n```\n'
        return get_action_and_input(text)
    
    def _get_next_action(self, full_inputs: Dict[str, str]) -> AgentAction:
        full_output = self.llm_chain.predict(**full_inputs)
        parsed_output = self._extract_tool_and_input(full_output)
        while parsed_output is None:
            full_output = self._fix_text(full_output)
            full_inputs["agent_scratchpad"] += full_output
            output = self.llm_chain.predict(**full_inputs)
            full_output += output
            parsed_output = self._extract_tool_and_input(full_output)
        
        if len(parsed_output)>2:
            full_output=parsed_output[2]
        
        return AgentAction(
            tool=parsed_output[0], tool_input=parsed_output[1], log=full_output
        )
    
    @classmethod
    def read_file(cls, filename):
        """read file"""
        filename= "openapi/"+filename
        try:
            with open(filename, 'r') as file:
                documents = yaml.load(file, Loader=yaml.FullLoader)
                return documents
        except Exception as e:
            None

        try:
            with open(filename, 'r') as file:
                documents = json.loads(file.read())
                return documents
        except Exception as e:
            None

        raise Exception(f"can not read file {filename}")


    
    @classmethod
    def from_llm_and_plugin(
        cls,
        llm: BaseLLM,
        plugin_name: str = None,
        plugin_profile: Dict = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ) -> Agent:
        
        if plugin_profile is None:
            plugin_profile={}
            plugin_profile['manifest_doc']=cls.read_file(f"{plugin_name}.json")
            plugin_profile['api_doc']=cls.read_file(f"{plugin_name}.yaml")
            plugin_profile['prompt']={}
            plugin_profile['prompt']['key_terms']={
                "Thought":"Thought",
                "Action":"Action",
                "Action_Input":"Action Input",
                "Observation":"Observation",
                "Question": "Question",
                "Final_Answer": "Final Answer",
            }
            plugin_profile['prompt']['user_prompt']="""{{Question}}: {input}
{{Thought}}:{agent_scratchpad}"""
            plugin_profile['prompt']['system_prompts']=[
                    """context:
{"iotDeviceList":{{my_devices}}}
""",

"""You are {{manifest_doc["name_for_model"]|tojson}}.
Here is what you can do:{{manifest_doc["description_for_model"]|tojson}}
Your api document, in openapi format:{{api_doc|tojson}}

Answer the following question as best as you can. You have access to your apis. Don't make up api that don't exist in the documentation :

MUST Use the following format:

{{Question}}: the input question you must answer
{{Thought}}: you should always think about what to do, better in chinese
{{Action}}: one operationId of api. you can only call ONE api at a time. Only clean api operationId are included, no colloquial expressions.
{{Action_Input}}: "parameters" and "requestBody" of api calling, which is encoding in json format . You can only send ONE request at a time . MUST be include in api document
{{Observation}}: the result of the api calling
{{Thought}}: ...
{{Action}}: ...
{{Action_Input}}: ...
{{Observation}}: ...
... (this {{Thought}}/{{Action}}/{{Action_Input}}/{{Observation}} can repeat N times, N>0)
{{Thought}}: I now know the final answer
{{Final_Answer}}: the final answer to the original input question, better in chinese

"""
]


        prompt = cls.create_prompt(
                plugin_profile=plugin_profile,
                )
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            callback_manager=callback_manager,
        )
        tools=get_tools_from_api_doc(api_doc=plugin_profile['api_doc'])

        tool_names = [tool.name for tool in tools]
        obj=cls(llm_chain=llm_chain, allowed_tools=tool_names, **kwargs)
        obj.plugin_profile=plugin_profile
        return obj
        
        #return cls(llm_chain=llm_chain, allowed_tools=[], **kwargs)
        #return ZeroShotAgent.from_llm_and_tools(llm,tools,callback_manager,prefix,suffix,format_instructions,input_variables,**kwargs)

    @classmethod
    def create_prompt(
        cls,
        plugin_profile: Dict,
    ) -> PromptTemplate:
        template_str = plugin_profile['prompt']['user_prompt']
        
        env = jinja2.Environment(loader=jinja2.BaseLoader)
        env.policies['json.dumps_kwargs']['ensure_ascii']=False
        jinja2_template = env.from_string(template_str)
        _dict=plugin_profile.copy()
        _dict.update(plugin_profile['prompt']['key_terms'])
        template= jinja2_template.render(**_dict)
        ##print(_dict,template)
        
        input_variables = ["input", "agent_scratchpad"]
        return PromptTemplate(template=template, input_variables=input_variables)

    
    def create_system_prompt(
        self,
    ) -> List[str]:
        env = jinja2.Environment(loader=jinja2.BaseLoader)
        env.policies['json.dumps_kwargs']['ensure_ascii']=False
        system_messages = []
        for system_template_str in self.plugin_profile['prompt']['system_prompts']:
            template = env.from_string(system_template_str)
            _dict=self.plugin_profile.copy()
            _dict.update(self.plugin_profile['prompt']['key_terms'])
            system_message = template.render(**_dict)
            system_messages += [{
                "role": "system",
                "content": system_message
            },]

        return system_messages


def get_generate_tool(**kwargs: Any) -> BaseTool:
    def summarize(text:str):
        ## 不在Observation里填东西，看看会输出啥
        return text
    return Tool(
        name="Generate",
        func=summarize,
        description="Generate a summary of the observation.",
    )

class CallPluginAgentExecutor(AgentExecutor):
    def _take_next_step(
        self,
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        inputs: Dict[str, str],
        intermediate_steps: List[Tuple[AgentAction, str]],
    ) -> Union[AgentFinish, Tuple[AgentAction, str]]:
        """Take a single step in the thought-action-observation loop.

        Override this to take control of how the agent makes and acts on choices.
        """
        #print("_take_next_step input ",inputs)
        # Call the LLM to see what to do.
        output = self.agent.plan(intermediate_steps, **inputs)
        # If the tool chosen is the finishing tool, then we end and return.
        if isinstance(output, AgentFinish):
            return output
        self.callback_manager.on_agent_action(
            output, verbose=self.verbose, color="green"
        )
        # Otherwise we lookup the tool
        if output.tool in name_to_tool_map:
            tool = name_to_tool_map[output.tool]
            return_direct = tool.return_direct
            color = color_mapping[output.tool]
            llm_prefix = "" if return_direct else self.agent.llm_prefix
            # We then call the tool on the tool input to get an observation
            observation = tool.run(
                output.tool_input,
                verbose=self.verbose,
                color=color,
                llm_prefix=llm_prefix,
                observation_prefix=self.agent.observation_prefix,
            )
        elif output.tool=="generate":
            return output,get_generate_tool().run(
                output.tool_input,
                verbose=self.verbose,
                color=None,
                llm_prefix="",
                observation_prefix=self.agent.observation_prefix,
            )
        else:
#            observation = InvalidTool().run(
#                output.tool,
#                verbose=self.verbose,
#                color=None,
#                llm_prefix="",
#                observation_prefix=self.agent.observation_prefix,
#            )
            observation = f'"{output.tool}" 不是一个有效的api，应该直接用createOrUpdateIotScenes设置场景'
            return_direct = False
        if return_direct:
            # Set the log to "" because we do not want to log it.
            return AgentFinish({self.agent.return_values[0]: "任务已完成"}, "")
        print(output,file=sys.stderr)
        print(observation,file=sys.stderr)
        return output, observation
    @classmethod
    def from_agent_and_plugin_name(
        cls,
        agent: Agent,
        plugin_name: str = None,
        plugin_profile: Dict = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ) -> AgentExecutor:
        """Create from agent and tools."""
        if plugin_profile is None:
            api_doc=CallPluginAgent.read_file(f"{plugin_name}.yaml")
        else:
            api_doc=plugin_profile['api_doc']
        return cls(
            agent=agent, tools=get_tools_from_api_doc(api_doc), callback_manager=callback_manager, **kwargs
        )
if __name__=="__main__":
    # plugin_name="www.wolframalpha.com"
    # query="Find the minimum value of x^2 + 9x - 5"

    # plugin_name="api.speak.com"
    # query="I am a America, I am learning Chinese, translate into Chinese:\n The OpenAI API can be applied to virtually any task that involves understanding or generating natural language, code, or images. We offer a spectrum of models with different levels of power suitable for different tasks, as well as the ability to fine-tune your own custom models. These models can be used for everything from content generation to semantic search and classification."

    # plugin_name="www.Klarna.com"
    # query="where can i buy black flowers"

    # plugin_name="jd.com"
    # query="i want to buy some flowers"
    
    # plugin_name="jd.com"
    # query="i want to buy a graphic card"


    plugin_name="iot.dueros.com"
    query="我每天早上7点半一定要起床，不然会赶不上地铁，周末可以晚一些，大改9点左右，干脆就9点半吧。帮我设一下闹钟。白天家里一般没有人，帮我把窗帘拉上。"

    

    plugin_name="iot.dueros.com"
    query="我平时晚上下班回家前一定要帮我把玄关的灯打开，否则开门之后太黑了。但我不在家的时候一定要记得帮我关上"

    

    plugin_name="iot.dueros.com"
    query="温度的话冬天室内温度不能低于23度，夏天温度可以定在26度，但夏天晚上睡觉后不能总开着，不然很容易感冒，但也不能一直不开，太热很影响睡眠"


    plugin_name="iot.dueros.com"
    query="我晚上睡觉的时间一般都在11点左右，但偶尔会失眠。所以我基本会在睡前半个小时看会书。如果你有什么好的助眠方法也可以给我"

    plugin_name="iot2.dueros.com"
    query="我每天早上7点半一定要起床，不然会赶不上地铁，周末可以晚一些，大改9点左右，干脆就9点半吧。起床要用闹钟叫醒我。另外，白天家里一般没有人，帮我把窗帘拉上。"


    

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
    import _env
    llm = OpenAI(model_name=_env.model_name, temperature=0.0,openai_api_key=_env.api_key)


    print(query)
#    agent = CallPluginAgent.from_llm_and_plugin(
#        llm, plugin_name, verbose=True
#    )
#
#    
#    llm.prefix_messages = [{
#        "role": "system",
#        "content": agent.create_system_prompt()
#    },]
#
#    executer = CallPluginAgentExecutor.from_agent_and_plugin_name(
#        agent=agent,
#        plugin_name=plugin_name,
#        verbose=True,
#    )

    import plugin_profiles.profiles as profiles 
    #plugin_profile=profiles.read_profile("sample")
    plugin_profile=None
    agent = CallPluginAgent.from_llm_and_plugin(
            llm, plugin_profile=plugin_profile, verbose=True,
            plugin_name=plugin_name
            )

    
    llm.prefix_messages = agent.create_system_prompt()

    executer = CallPluginAgentExecutor.from_agent_and_plugin_name(
        agent=agent,
        plugin_profile=plugin_profile,
        plugin_name=plugin_name,
        verbose=True,
    )


    executer.max_iterations=4
    
    executer.run(query)
