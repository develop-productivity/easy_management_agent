from datetime import datetime, timedelta
import argparse
import os
import time
import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage



from src.agent_task_mgr.state import AgentState, TeamMember, Team
from src.agent_task_mgr.nodes import (
    task_generation_node,
    task_dependency_node,
    task_scheduler_node,
    task_allocation_node,
    risk_assessment_node,
    insight_generation_node,
    router
)
from src.tools.task_mgr_api import visalize_project_timeline
# import akshare as ak
import pandas as pd
import os

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:1080'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1080'


# Set up logging
logger = logging.getLogger('MAIN')
logger.setLevel(logging.DEBUG)

def get_project_description(file_path:str):
    """Read the project description from the file"""
    with open(file_path, 'r') as file:
        content = file.read()

    return content

def get_team(file_path:str):
    """Read the team members from the CSV file"""
    team_df = pd.read_csv(file_path)
    team_members = [
            TeamMember(name=row['Name'], profile=row['Profile Description'])
            for _, row in team_df.iterrows()
        ]
    team = Team(team_members=team_members)

    return team


# Define the new workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("task_generation", task_generation_node)
workflow.add_node("task_dependencies", task_dependency_node)
workflow.add_node("task_scheduler", task_scheduler_node)
workflow.add_node("task_allocator", task_allocation_node)
workflow.add_node("risk_assessor", risk_assessment_node)
workflow.add_node("insight_generator", insight_generation_node)

# Define the workflow
workflow.set_entry_point("task_generation")
workflow.add_edge("task_generation", "task_dependencies")
workflow.add_edge("task_dependencies", "task_scheduler")
workflow.add_edge("task_scheduler", "task_allocator")
workflow.add_edge("task_allocator", "risk_assessor")
workflow.add_conditional_edges("risk_assessor", router, ["insight_generator", END])
workflow.add_edge("insight_generator", "task_scheduler")


# Set up memory
memory = MemorySaver()

# Compile the workflow
logger.info("Compiling the workflow")
graph_plan = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    # read the project description and team members
    project_description = get_project_description("src/data/task_data/project_description.txt")
    team = get_team("src/data/task_data/team.csv")
    logger.info("Project description and team members read successfully")
    logger.info("Project description: {}".format(project_description))
    logger.info("Team members: {}".format(team))


    # # Define the initial state
    # TODO: support args input
    state_input = {
        "project_description": project_description,
        "team": team,
        "insights": "",
        "iteration_number": 0,
        "max_iteration": 1,
        "schedule_iteration": [],
        "task_allocations_iteration": [],
        "risks_iteration": [],
        "project_risk_score_iterations": []
    }


    logger.info("Starting the workflow")
    config = {"configurable": {"thread_id": "1"}}
    for event in graph_plan.stream(state_input, config, stream_mode=["updates"]):
        "Print the different nodes as the agent progresses"
        print(f"Current node: {next(iter(event[1]))}")

    final_state = graph_plan.get_state(config).values
    print("iteration_number", final_state['iteration_number'])
    print("project_risk_score_iterations", final_state['project_risk_score_iterations'])
    print("insights", final_state['insights'])
    visalize_project_timeline(final_state)
