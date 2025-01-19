from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv
from langgraph.graph import END

import logging
import pandas as pd
from typing import List, Dict
import sys

sys.path.append("/data/sydong/code/agent/project")
from src.tools.exer_mgr_api import calculate_metrics
from src.agent_exer_mgr.state import AgentState, Plan, Insight


logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv(override=True)
# define the llm
llm = ChatZhipuAI(temperature=0.5, model="glm-4-flash")


EXERCISE_TASK = ["run", "cycle", "yoga", "stretch", "swim", "hike", "dance", "pilates", "boxing", "weightlifting"]
EXERCISE_CALORIES = {
    "run": 100,
    "cycle": 80,
    "yoga": 50,
    "stretch": 30,
    "swim": 120,
    "hike": 90,
    "dance": 70,
    "pilates": 60,
    "boxing": 100,
    "weightlifting": 80
}



def exer_history_write():
    """
    Write the user's behavior history to a file
    """
    data = {
        "date": pd.date_range(start="2024-12-15", periods=31).strftime("%Y-%m-%d").tolist(),
        "tasks": [["run", "stretch"] if i % 2 == 0 else ["cycle", "yoga"] for i in range(31)],
        "duration": [[30, 10] if i % 2 == 0 else [45, 15] for i in range(31)],
        "intensity": [[5, 3] if i % 2 == 0 else [6, 4] for i in range(31)],
        "calories": [[50, 30] if i % 2 == 0 else [60, 40] for i  in range(31)],
        "mood": ["moderate" if i % 3 == 0 else "intense" if i % 3 == 1 else "easy" for i in range(31)],
        "sleep": [8 - i % 3 for i in range(31)],
    }
    df = pd.DataFrame(data)
    df.to_csv("/data/sydong/code/agent/project/src/data/exer_data/behavior_history.csv", index=False)

def read_behavior_history(file_path: str):
    data = pd.read_csv(file_path)
    return data

def exer_analyze_behavior_node(state: AgentState):
    """
    Analyze the behavior history of the user and return a summary of the last week
    """
    history_info = state["history_info"] 
    data = read_behavior_history(history_info['file_path'])
    end_data = history_info['end_data'] if 'end_data' in history_info else None
    if end_data is None:
        end_data = pd.Timestamp.now()  - pd.Timedelta(days=1)
    start_data = end_data - pd.Timedelta(days=8)
    # 时间从昨天开始算，往前推7天
    # last_week = data[data['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
    last_week = data[(data['date'] >= start_data.strftime("%Y-%m-%d")) & (data['date'] <= end_data.strftime("%Y-%m-%d"))]
    task_counts = {}
    for tasks in last_week["tasks"]:
        for task in eval(tasks):
            if task in task_counts:
                task_counts[task] += 1
            else:
                task_counts[task] = 1
    task_counts_each_day = []
    task_each_day = []
    for tasks in last_week["tasks"]:
        task_counts_each_day.append(len(eval(tasks)))
        task_each_day.append(eval(tasks))

    duration_list = [eval(duration) for duration in last_week['duration'].tolist()]
    intensity_list = [eval(intensity) for intensity in last_week['intensity'].tolist()]
    calories_list = [eval(calories) for calories in last_week['calories'].tolist()]

    behavior_summary = {
        "sessions": task_counts,
        "sessions_each_day": task_counts_each_day,
        "task_list": task_each_day,
        "duration_list": duration_list,
        "intensity_list": intensity_list,
        "calories_list": calories_list,
        "mood_list": [mood for mood in last_week['mood']],
        "sleep_list": [sleep for sleep in last_week['sleep']]
    }
    # 根据用户的行为历史，生成用户运动指数
    metrics = calculate_metrics(behavior_summary)
    # state["behaviour_sumary"] = behavior_summary
    # state["metrics_summary"] = metrics
    # return state
    return {"behavior_summary": behavior_summary, "metrics_summary": metrics}

def exer_plan_node(state: AgentState):
    """
    Plan the exercise routine based on the user's behavior history
    """
    
    behavior_summary = state['behavior_summary']
    metrics_summary = state['metrics_summary']
    goal = state["goal"] if "goal" in state else ""
    pre_insight_content: Insight = state["insights"].content if "insights" in state else ""
    # 根据历史信息，以及用户运动指数 指定第二天锻炼计划
    prompt = f"""
        You are an expert Fitness coach and you need help to achieve: {goal}
        1. give you user's historical behavioral data {behavior_summary}, metrics {metrics_summary} and previous insight: {pre_insight_content} and the scores.
        2. Develop a reasonable exercise plan for one day, choose the exercise tasks from {EXERCISE_TASK} and set the duration(minutes) and intensity(0~1) of each task.
        3. your should only output the tasks: list of 'tasks', duration: list of their corresponding duration and intensity: list of 'intensity, **do no return other content**.
        """

    # 生成计划
    # structure_llm = llm.with_structured_output(Plan)
    # plan: Plan = structure_llm.invoke(prompt)
    output = llm.invoke(prompt)

    # example: "tasks: ['run', 'cycle', 'yoga', 'stretch']\nduration: [45, 30, 20, 15]\nintensity: [0.7, 0.6, 0.5, 0.4]""
    plan = {}
    lines = output.content.split('\n')
    for line in lines:
        if line.startswith("tasks:"):
            plan["tasks"] = eval(line.split("tasks:")[1].strip())
        elif line.startswith("duration:"):
            plan["duration"] = eval(line.split("duration:")[1].strip())
        elif line.startswith("intensity:"):
            plan["intensity"] = eval(line.split("intensity:")[1].strip())
            
    return {"plan": plan}
    




def insight_generation_node(state: AgentState):
    """
    Generate insights for the user based on the analysis and risk assessment
    """
   
    behavior_summary = state["behavior_summary"]
    metrics_summary = state["metrics_summary"]
    plan = state["plan"]
    goal = state["goal"] if "goal" in state else ""
    prompt = f"""
    You are an expert Fitness coach responsible for generating actionable insights to enhance the user's exercise routine and help them achieve: {goal}
        1. **Analysis the user's historical data:**
            identify the most effective interventions based on the user's historical behavioral data {behavior_summary}, metrics {metrics_summary} and the next day exercise plan {plan}.
        2. ** Recommend Enhancements:**
            Give insight to exercise plan and Rate your current plan from 1 to 10.
        3. you should only output the insight: str and score: int, **do no return other content**.

    """

    # structure_llm = llm.with_structured_output(Insight)
    # insight: Insight = structure_llm.invoke(prompt)
    insight_scores_iterations = state["insight_scores_iterations"] if "insight_scores_iterations" in state else []
    output = llm.invoke(prompt)
    lines = output.content.split('\n')
    insight = {}
    for line in lines:
        if line.startswith("Insight:") or line.startswith("insight:"):
            insight_content = line.split(":")[1].strip()
            insight["content"] = insight_content
        elif line.startswith("Score:") or line.startswith("score:"):
            score = int(line.split(":")[1].strip())
            insight["score"] = score if isinstance(score, int) else 9
    # state["insight"] = insight
    # return state

    insight = Insight(**insight)
    insight_scores_iterations.append(insight.score)
    iteration_number = state["iteration_number"] + 1
    return {"insights": insight, "insight_scores_iterations": insight_scores_iterations, "iteration_number": iteration_number}

def router(state: AgentState):
    """
    Router function to route the conversation based on the user's input
    """
    
    max_iteration = state["max_iteration"]
    iteration_number = state["iteration_number"]
    # state["iteration_number"] = iteration_number + 1

    if iteration_number < max_iteration:
        if len(state["insight_scores_iterations"])>1:
            if state["insight_scores_iterations"][-1] < state["insight_scores_iterations"][0]:
                return END
            else:
                return "exercise_plan"
        else:
            return "exercise_plan"
    else:
        return END
    

if __name__ == "__main__":
    exer_history_write()
    init_data = {
        "goal": "lose weight",
        "behavior_history_file": "/data/sydong/code/agent/project/src/data/exer_data/behavior_history.csv"
    }
    # state = AgentState(data=init_data)
    # state = exer_analyze_behavior_node(state)
    # print(state['behavior_history_summary'])

    # state.plan = exer_plan_node(state)
    # state.schedule = exer_schedule_node(state)
    # state.nutrition_plan = exer_nutrition_node(state)
    # state.risks = risk_assessment_node(state)
    # state.insights = insight_generation_node(state)
    # state["max_iteration"] = 1
    # state["iteration_number"] = 0
    # state["insight_scores_iterations"] = []
    # print(state)
    # print(router(state))