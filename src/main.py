import os
from langchain_openai import ChatOpenAI
from src.rag import getContext, loadRAG
from src.graph import init_graph
from src.tools import init_tools
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field
from typing import (
    List
)

LANGCHAIN_TRACING_V2=True
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="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"
LANGCHAIN_PROJECT="pr-mealy-length-60"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )

model = ChatOpenAI(model="gpt-4o-mini")
plan_model = ChatOpenAI(model="gpt-4o-mini").with_structured_output(Plan)
print("Models are ready ....")
loadRAG()
print("Rag is Loaded ....")
tools = init_tools()
bound_model = model.bind_tools(tools)
graph = init_graph(bound_model, plan_model)
print("Graph is up ....")

def initialize():
    
    query = input("Human: ")
    current_path = os.getcwd()
    context = getContext(query)
    input_msg = {"messages": [{"role": "user", "content": f""" 
                               current_path - {current_path} 
                               context - {context}
                               query - {query}"""}]}
    # Thread
    thread = {"configurable": {"thread_id": "1"}}
    last_message = None

    def handle_event(graph, last_message):
        if isinstance(last_message, AIMessage):
            if graph.get_state(thread).next:
                is_tool = len(last_message.tool_calls) > 0
                if is_tool:
                    confirm = input("Confirm Action: ")
                    if confirm == "yes" or confirm == "y":
                        for event in graph.stream(None, thread, stream_mode="values"):
                            last_message = event['messages'][-1]
                            last_message.pretty_print()
               
                        if isinstance(last_message, AIMessage):
                            if len(last_message.tool_calls) > 0:
                                handle_event(graph, last_message)
                        
                        loadRAG()

                    else:
                        state = graph.get_state(thread)
                        tool_calls= state.values["messages"][-1].tool_calls
                        tool_msgs = []
                        why = input("Why? ")

                        for tool_call in tool_calls:
                            tool_call_id = tool_call["id"]
                            tool_call_name = tool_call["name"]
                            tool_msgs.append({
                                "role": "tool",
                                # This is our natural language feedback
                                "content": why,
                                "name": tool_call_name,
                                "tool_call_id": tool_call_id,
                            })

                        graph.update_state(
                            # This is the config which represents this thread
                            thread,
                            # This is the updated value we want to push
                            {"messages": tool_msgs},
                            # We push this update acting as our human_review_node
                            as_node="human_review_node",
                        )

                        # Let's now continue executing from here
                        for event in graph.stream(None, thread, stream_mode="values"):
                            last_message = event['messages'][-1]
                            last_message.pretty_print()
                            handle_event(graph, last_message)

                    



    # Run the graph until the first interruption
    for event in graph.stream(input_msg, thread, stream_mode="values"):
        last_message = event['messages'][-1]
        last_message.pretty_print()
        handle_event(graph, last_message)  

    initialize()   


initialize()