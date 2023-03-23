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

from langchain.agents.tools import InvalidTool

from langchain.schema import AgentAction, AgentFinish

class MyZeroShotAgent(ZeroShotAgent):
    """Agent for the MRKL chain."""
    ##  Action Input多返回了一个换行符，导致匹配失效
    ## 提取出来的Action Input是largest prime number smaller than 65"
    ## 多了一个引号没处理掉，导致后面的caculator很容易出错（WolframAlpha就接受不了这种输入）
    PREFIX = """Answer the following question as best you can. You have access to the following tools if needed, no manually actions :"""

    FORMAT_INSTRUCTIONS = """MUST Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, MUST be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
Thought: you should always think about what to do
Action: the action to take, MUST be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action/Observation can repeat N times, N>0)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

"Final Answer:" MUST be include in last line, and the answer MUST be in the same line as "Final Answer:". 
e.g. "Final Answer: 42".

You can summarize all Thought and Observation to get the final answer.

The fewer actions, the better


"""
    SUFFIX = """Begin!

Question: {input}
Thought:{agent_scratchpad}"""


    

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Observation:"

    def _extract_tool_and_input(self, text: str) -> Optional[Tuple[str, str]]:
        def get_action_and_input(llm_output: str) -> Tuple[str, str]:
            """Parse out the action and input from the LLM output.

            Note: if you're specifying a custom prompt for the ZeroShotAgent,
            you will need to ensure that it meets the following Regex requirements.
            The string starting with "Action:" and the following string starting
            with "Action Input:" should be separated by a newline.
            """

            FINAL_ANSWER_ACTION = "Final Answer:"
            if FINAL_ANSWER_ACTION in llm_output:
                return "Final Answer", llm_output.split(FINAL_ANSWER_ACTION)[-1].strip()
            regex = r"Action:(.*?)\nAction Input:(.*)"
            match = re.search(regex, llm_output, re.DOTALL)
            if not match:
                #return "Final Answer","<not for sure>" + llm_output
                #强制生成一个final answer
                return "generate","now i can summarize the answer\n"
                #if "final answer" in llm_output:
                #    return "Final Answer", llm_output
                #if "Final answer" in llm_output:
                #    return "Final Answer", llm_output
                #raise ValueError(f"Could not parse LLM output: `{llm_output}`")
            action = match.group(1).strip()
            action_input = match.group(2).strip("\n").strip(" ").strip('"')
            return action, action_input
        return get_action_and_input(text)
    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLLM,
        tools: Sequence[BaseTool],
        callback_manager: Optional[BaseCallbackManager] = None,
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Agent:
        ZeroShotAgent._validate_tools(tools)
        prompt = MyZeroShotAgent.create_prompt(
            tools,
            prefix=prefix,
            suffix=suffix,
            format_instructions=format_instructions,
            input_variables=input_variables,
        )
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        return MyZeroShotAgent(llm_chain=llm_chain, allowed_tools=tool_names, **kwargs)
        #return ZeroShotAgent.from_llm_and_tools(llm,tools,callback_manager,prefix,suffix,format_instructions,input_variables,**kwargs)

    @classmethod
    def create_prompt(
        cls,
        tools: Sequence[BaseTool],
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
    ) -> PromptTemplate:
        """Create prompt in the style of the zero shot agent.

        Args:
            tools: List of tools the agent will have access to, used to format the
                prompt.
            prefix: String to put before the list of tools.
            suffix: String to put after the list of tools.
            input_variables: List of input variables the final prompt will expect.

        Returns:
            A PromptTemplate with the template assembled from the pieces here.
        """
        template = """Question: {input}
Thought:{agent_scratchpad}"""
        if input_variables is None:
            input_variables = ["input", "agent_scratchpad"]
        return PromptTemplate(template=suffix, input_variables=input_variables)

    
    @classmethod
    def create_system_prompt(
        cls,
        tools: Sequence[BaseTool],
        prefix: str = PREFIX,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
    ) -> str:
        """Create prompt in the style of the zero shot agent.

        Args:
            tools: List of tools the agent will have access to, used to format the
                prompt.
            prefix: String to put before the list of tools.
            suffix: String to put after the list of tools.
            input_variables: List of input variables the final prompt will expect.

        Returns:
            A PromptTemplate with the template assembled from the pieces here.
        """
        tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
        tool_names = ", ".join([tool.name for tool in tools])
        format_instructions = format_instructions.format(tool_names=tool_names)
        template = "\n\n".join([prefix, tool_strings, format_instructions])
        return template


def get_generate_tool(**kwargs: Any) -> BaseTool:
    def summarize(text:str):
        ## 不在Observation里填东西，看看会输出啥
        return text
    return Tool(
        name="Generate",
        func=summarize,
        description="Generate a summary of the observation.",
    )

class MyAgentExecutor(AgentExecutor):
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
            observation = InvalidTool().run(
                output.tool,
                verbose=self.verbose,
                color=None,
                llm_prefix="",
                observation_prefix=self.agent.observation_prefix,
            )
            return_direct = False
        if return_direct:
            # Set the log to "" because we do not want to log it.
            return AgentFinish({self.agent.return_values[0]: observation}, "")
        return output, observation