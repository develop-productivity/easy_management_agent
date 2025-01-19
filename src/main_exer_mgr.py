from datetime import datetime, timedelta
import os
import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.agent_exer_mgr.state import AgentState
from src.agent_exer_mgr.nodes import (
    exer_analyze_behavior_node,
    exer_plan_node,
    # exer_schedule_node,
    insight_generation_node,
    router,
)


os.environ['HTTP_PROXY'] = 'http://127.0.0.1:1082'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1082'

logger = logging.getLogger('MAIN')
logger.setLevel(logging.DEBUG)


# Define the new workflow
workflow = StateGraph(AgentState)
workflow.add_node("exercise_history_analyze", exer_analyze_behavior_node)
workflow.add_node("exercise_plan", exer_plan_node)
workflow.add_node("insight_generator", insight_generation_node)

workflow.set_entry_point("exercise_history_analyze")
workflow.add_edge("exercise_history_analyze", "exercise_plan")
workflow.add_edge("exercise_plan", "insight_generator")
# workflow.add_edge("insight_generator", END)
workflow.add_conditional_edges("insight_generator", router, ["exercise_plan", END])

# workflow.add_edge("exercise_plan", "nutrition_plan")
# workflow.add_edge("exercise_schedule", "insight_generation")
# workflow.add_edge("nutrition_plan", "insight_generation")
# workflow.add_conditional_edges("insight_generation", router, ["exercise_plan", END])


# set memoty saver
memory = MemorySaver()

# Compile the workflow
logger.info("Compiling the workflow")
# Compile the workflow
graph_plan = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    # Define the initial state
    state_input = {
        "goal": "lose weight",
        "history_info": {
            "file_path": "/data/sydong/code/agent/project/src/data/exer_data/behavior_history.csv",
            "end_date": datetime.now() - timedelta(days=1),
        },
        "max_iteration": 3,
        "iteration_number":0
    }
    # state = AgentState(data=state_input)
    logger.info("Starting the workflow")
    config = {"configurable": {"thread_id": "1"}}
    for event in graph_plan.stream(state_input, config, stream_mode=["updates"]):
        "Print the different nodes as the agent progresses"
        print(f"Current node: {next(iter(event[1]))}")

    final_state = graph_plan.get_state(config).values
    plan = final_state["plan"]
    insights = final_state["insights"]
    print(f"Next day exercise plan: {plan}")
    print("Next day exercise insight: ", insights.content)
    print("Next day exercise score : ", insights.score)