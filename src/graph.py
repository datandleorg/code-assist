from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, SystemMessage
from IPython.display import Image, display
from src.tools import create_or_update_file, run_bash_command
import json


class State(MessagesState):
    """Simple state."""


def call_llm(state):
    return {"messages": [call_llm.model.invoke(state["messages"])]}

def planner(
    state
):
    # this is similar to customizing the create_react_agent with state_modifier, but is a lot more flexible
    system_prompt = SystemMessage(
        """You are a helpful AI assistant, please respond to the users query to the best of your ability! 
        For the given objective, come up with a simple step by step plan. \
        This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
        The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps."""
    )
    response = planner.model.invoke([system_prompt] + state["messages"])

    # We return a list, because this will get added to the existing list
    return {"messages": [json.dumps(response.__dict__)]}

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
    return {"messages": new_messages}


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

def init_graph(main_model, planner_model):
    builder = StateGraph(State)
    call_llm.model = main_model
    planner.model = planner_model
    builder.add_node(planner)
    builder.add_node(call_llm)
    builder.add_node(run_tool)
    builder.add_node(human_review_node)
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "call_llm")
    builder.add_conditional_edges("call_llm", route_after_llm)
    builder.add_conditional_edges("human_review_node", route_after_human)
    builder.add_edge("run_tool", "call_llm")
    graph = builder.compile(checkpointer=memory, interrupt_before=["human_review_node"])
    return graph
    