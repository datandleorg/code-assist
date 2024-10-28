
import os
from src.rag import  loadRAG
from src.graph import init_graph
from langchain_core.messages import AIMessage

LANGCHAIN_TRACING_V2=True
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="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"
LANGCHAIN_PROJECT="pr-mealy-length-60"
    
print("Models are ready ....")
loadRAG()
print("Rag is Loaded ....")
graph = init_graph()
print("Graph is up ....")

def initialize():
    
    query = input("Human: ")
    current_path = os.getcwd()
    modified_query = f""" current_path - {current_path} 
                          query - {query}"""
    input_msg = {
                    "messages": [{
                        "role" : "user",
                        "content" : modified_query
                    }],
                    "show_msg": True,
                    "question": modified_query,
                }
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
        if event["show_msg"]:
            last_message = event['messages'][-1]
            last_message.pretty_print()
        handle_event(graph, last_message)  

    initialize()   


initialize()