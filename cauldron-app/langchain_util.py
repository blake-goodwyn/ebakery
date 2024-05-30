# langchain_util.py

import operator
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.agents.agent import RunnableAgent
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.prompt import (
    SQL_FUNCTIONS_SUFFIX,
    SQL_PREFIX,
)
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.graph import StateGraph

from dotenv import load_dotenv
import os
from pydantic_util import CauldronPydanticParser
from logging_util import logger

load_dotenv()
LANGCHAIN_TRACING_V2=True
LANGCHAIN_API_KEY=os.getenv("LANGCHAIN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def StringParser():
    logger.debug("Creating StrOutputParser instance.")
    return StrOutputParser()

def AgentParser():
    logger.debug("Creating AgentParser instance.")
    return CauldronPydanticParser

def createAgent(
    llm: ChatOpenAI,
    tools: list,
    system_prompt: str,
) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n\n Your responsibility is the following:\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages")
        ]
    )
    prompt = prompt.partial(system_message=system_prompt)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)

def createSQLAgent(system_prompt, llm_model, db_path, verbose=False):
    assert type(llm_model) == str, "Model must be a string"
    #assert type(prompt) == str, "Prompt must be a string"

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(str(SQL_PREFIX)),
            SystemMessage(str(system_prompt)),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            AIMessage(SQL_FUNCTIONS_SUFFIX)
        ]
    )

    llm = ChatOpenAI(model=llm_model, temperature=0)
    db = SQLDatabase.from_uri(db_path)
    toolkit = SQLDatabaseToolkit(llm=llm, db=db)
    tools = toolkit.get_tools()
    agent = RunnableAgent(
            runnable=create_openai_functions_agent(llm, tools, prompt),
            input_keys_arg=["messages"],
            return_keys_arg=["output"]
        )
    return AgentExecutor(name="SQL Agent Executor", agent=agent, tools=tools)

def createTeamSupervisor(llm: ChatOpenAI, system_prompt, name, members) -> str:
    """An LLM-based router."""
    sender = name
    options = members
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                },
                "sender": {
                    "title": "Sender",
                    "anyOf": [
                        {"string": sender},
                    ]
                }
            },
            "required": ["next", "sender"],
        },
    }
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), team_members=", ".join(members))
    return (
        prompt
        | llm.bind_functions(functions=[function_def], function_call="route")
        | JsonOutputFunctionsParser()
    )

# Helper function to create a node for a given agent
def agent_node(state, agent, name):
    result = agent.invoke(state)
    logger.info(result)
    result = AIMessage(content=result["output"], name=name)
    return {
        "messages": [result],
        "sender": name,
    }

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    next: str

def workflow():
    return StateGraph(AgentState)

def enter_chain(message: str):
    results = {
        "messages": [HumanMessage(content=message)],
    }
    return results