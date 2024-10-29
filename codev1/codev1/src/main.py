
import os
from codev1.src.utils import cprint
from codev1.src.play import play_audio
from codev1.src.audio import get_user_input
from codev1.src.rag import  loadRAG
from codev1.src.graph import init_graph
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

LANGCHAIN_TRACING_V2=True
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="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"
LANGCHAIN_PROJECT="pr-mealy-length-60"
    
cprint("Models are ready ....", "success")
loadRAG()
cprint("Code base is loaded ....", "success")
graph = init_graph()
cprint("Graph is up ....", "success")


def map_print(msg):
    if isinstance(msg, AIMessage):
        if len(msg.tool_calls) > 0:
            msg.pretty_print()
        else:
            cprint(f"======================Assistant========================",  "assistant")
            cprint(msg.content, "assistant")
    elif isinstance(msg, HumanMessage):
        cprint(f"======================Human========================",  "user")
        cprint(msg.content, "user")
    elif isinstance(msg, ToolMessage):
        cprint(f"======================Tool========================",  "info")
        cprint(msg.content, "info")
    else:
        return msg

def initialize():
    
    query = get_user_input()

    # query = input("Human: ")
    current_path = os.getcwd()
    modified_query = f""" current_path - {current_path} query - {query}"""
    input_msg = {
                    "messages": [{
                        "role" : "user",
                        "content" : modified_query
                    }],
                    "show_msg": True,
                    "question": modified_query,
                }
    # Thread
    thread = {"configurable": {"thread_id": "2"}}
    last_message = None

    def handle_event(graph, last_message):
        if isinstance(last_message, AIMessage):
            if graph.get_state(thread).next:
                is_tool = len(last_message.tool_calls) > 0
                if is_tool:
                    confirm = input("Confirm Action: ")
                    if confirm == "":
                        confirm = "yes"
                    else:
                        confirm = "no"
                    if "yes" in confirm :
                        for event in graph.stream(None, thread, stream_mode="values"):
                            last_message = event['messages'][-1]
                            map_print(last_message)
               
                        if isinstance(last_message, AIMessage):
                            if len(last_message.tool_calls) > 0:
                                handle_event(graph, last_message)
                        
                    else:
                        state = graph.get_state(thread)
                        tool_calls= state.values["messages"][-1].tool_calls
                        tool_msgs = []
                        cprint("Why? ", "user")
                        why = get_user_input()


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
                            map_print(last_message)
                            handle_event(graph, last_message)

                    

    # Run the graph until the first interruption
    for event in graph.stream(input_msg, thread, stream_mode="values"):
        if event["show_msg"]:
            if isinstance(event["messages"][-1], AIMessage):
                play_audio("msg")
            last_message = event['messages'][-1]
            map_print(last_message)

        handle_event(graph, last_message)  

    initialize()   
