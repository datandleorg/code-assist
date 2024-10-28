import os
from typing import List
from pydantic import BaseModel, Field
from typing_extensions import Literal
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage, HumanMessage
from src.tools import create_or_update_file, retrieve_code_context, run_bash_command
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import tools_condition
from langgraph.graph.message import add_messages
import json

class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )

class DoRetrieve(BaseModel):
    """Simple state."""
    should_retrieve_context: bool

class CodeGraphState(MessagesState):
    """Simple state."""
    question: str
    context: str
    plan: str
    show_msg: bool


main_tools = [create_or_update_file, run_bash_command]

long_model = ChatOpenAI(model="gpt-4o")
short_model = ChatOpenAI(model="gpt-4o-mini")
plan_model = ChatOpenAI(model="gpt-4o-mini").with_structured_output(Plan)
main_model = long_model.bind_tools(main_tools)

def should_retrieve_context(state):
    """
    Invokes the chat model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply end.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with the agent response appended to messages
    """
    system_prompt = SystemMessage(
        """You are a helpful AI code assistant. 
        Check if the user query needs to fetch the code base context
        IF the query is irrelevant to anything related to code base context, then respond to the user query.
        IF the query is relevant to code base context, then retrieve the code base context and respond to the user query."""
    )
    messages = [system_prompt] + state["messages"]
    model = short_model.with_structured_output(DoRetrieve)
    response = model.invoke(messages)

    if response.should_retrieve_context:
        return { "context": retrieve_code_context(state["question"]), "show_msg": False }
    
    return {
        "context": "",
        "show_msg": False
    }

def call_llm(state):
    question = HumanMessage(content=f"""
    question: {state["question"]}
    context: {state["context"]}
    plan: {state["plan"]}                     
    """)
    new_messages = state["messages"] + [question]
    response = main_model.invoke(new_messages)
    new_messages = new_messages + [response]
    return {"messages": new_messages, "show_msg": True}

def planner(
    state
):
    
    # this is similar to customizing the create_react_agent with state_modifier, but is a lot more flexible
    system_prompt = SystemMessage(
        """You are a helpful AI assistant, 
        First check if the query even need a plan to solve it.
        If yes, then generate a step by step plan for the query.
        If no, then plan will be empty
        please respond to the users query to the best of your ability! 
        For the given objective, come up with a simple step by step plan. \
        This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
        The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps."""
    )
    planner_prompt = HumanMessage(
        content="""
        question: {state.question}
        context: {state.context}
        """
    )
    response = plan_model.invoke([system_prompt] + [planner_prompt])

    # We return a list, because this will get added to the existing list
    return { 
        "messages": state["messages"],
        "plan": json.dumps(response.__dict__),
        "show_msg": False
    }

def human_review_node(state):
    
    pass

def run_tool(state):
    new_messages = []
    tools = {
        "create_or_update_file": create_or_update_file,
        "run_bash_command": run_bash_command
        }
    tool_calls = state["messages"][-1].tool_calls
    for tool_call in tool_calls:
        tool = tools[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        new_messages.append(
            {
                "role": "tool",
                "name": tool_call["name"],
                "content": result,
                "tool_call_id": tool_call["id"],
            }
        )
    return { 
        "messages": state["messages"] + new_messages,
        "show_msg": True,
        }


def route_after_llm(state) -> Literal[END, "human_review_node"]:
    if len(state["messages"][-1].tool_calls) == 0:
        return END
    else:
        return "human_review_node"


def route_after_human(state) -> Literal["run_tool", "call_llm"]:
    if isinstance(state["messages"][-1], AIMessage):
        return "run_tool"
    else:
        return "call_llm"
# Set up memory
memory = MemorySaver()

def init_graph():
    builder = StateGraph(CodeGraphState)
    builder.add_node(should_retrieve_context)
    builder.add_node(planner)
    builder.add_node(call_llm)
    builder.add_node(run_tool)
    builder.add_node(human_review_node)
    builder.add_edge(START, "should_retrieve_context")
    builder.add_edge("should_retrieve_context", "planner")
    builder.add_edge("planner", "call_llm")
    builder.add_edge("call_llm", END)
    builder.add_conditional_edges("call_llm", route_after_llm)
    builder.add_conditional_edges("human_review_node", route_after_human)
    builder.add_edge("run_tool", "call_llm")
    graph = builder.compile(checkpointer=memory, 
                            interrupt_before=["human_review_node"]
                            )
    return graph
    