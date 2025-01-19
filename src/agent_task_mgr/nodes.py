# Workflow Nodes
from src.agent_task_mgr.state import (
    AgentState,
    TaskList, 
    TaskDependency,
    DependencyList,
    ScheduleList,
    TaskSchedule,
    TaskAllocationList,
    RiskList,
    Risk,
    TeamMember,
    Task,
    TaskAllocation,
    TaskDependency,
    TaskSchedule,
)

from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv
from langgraph.graph import END
import logging

logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv(override=True)
# define the llm
llm = ChatZhipuAI(temperature=0.5,model="glm-4-flash")


def task_generation_node(state: AgentState):
    """LangGraph node that will extract tasks from given project description"""
    description = state["project_description"]
    prompt = f"""
        You are an expert project manager tasked with analyzing the following project description: {description}
        Your objectives are to: 
        1. **Extract Actionable Tasks:**
            - Identify and list all actionable and realistic tasks necessary to complete the project.
            - Provide an estimated number of days required to complete each task.
        2. **Refine Long-Term Tasks:**
            - For any task estimated to take longer than 5 days, break it down into smaller, independent sub-tasks.
        **Requirements:** - Ensure each task is clearly defined and achievable.
            - Maintain logical sequencing of tasks to facilitate smooth project execution."""

    structure_llm = llm.with_structured_output(TaskList)
    try:
        tasks: TaskList = structure_llm.invoke(prompt)
    except Exception as e:
        # If the LLM fails to generate tasks, break the loop
        logger.error(f"API 调用失败: {str(e)}")
        logger.error(f"错误详情: {str(e)}")
        raise e
    return {"tasks": tasks}

def task_dependency_node(state: AgentState):
    """Evaluate the dependencies between the tasks"""
    tasks = state["tasks"]
    prompt = f"""
        You are a skilled project scheduler responsible for mapping out task dependencies.
        Given the following list of tasks: {tasks}
        Your objectives are to:
            1. **Identify Dependencies:**
                - For each task, determine which other tasks must be completed before it can begin (blocking tasks).
            2. **Map Dependent Tasks:** 
                - For every task, list all tasks that depend on its completion.
            3. **you should strictly only output the dict("dependencies": dependencies_list) dependencies_list: list of TaskDependency each item is a dict contains tasks (follow the inputs tasks format) and their dependent_tasks list (a list of task， do not contain other symbol) respectively, and do not output other information.**
            4. ** Do not output the code, you need output the results**
        """
    structure_llm = llm.with_structured_output(DependencyList)
    try:
        dependencies: DependencyList = structure_llm.invoke(prompt)
    except Exception as e:
        dependencies = get_default_dependencies(tasks)
    if dependencies is None:
        dependencies = get_default_dependencies(tasks)
    # vanilla_output = llm.invoke(prompt).content
    # dependencies = []
    # for line in vanilla_output.split("\n"):
    #     if "task" in line:
    #         task, dependent_tasks = line.split(":")
    #         task = task.strip()
    #         dependent_tasks = dependent_tasks.strip().split(", ")
    #         dependencies.append(TaskDependency(task=task, dependent_tasks=dependent_tasks))
    # try:
    #     dependencies: DependencyList = structure_llm.invoke(prompt)
    # except Exception as e:
    #     # If the LLM fails to generate dependencies, break the loop
    #     logger.error(f"API 调用失败: {str(e)}")
    #     logger.error(f"错误详情: {str(e)}")
    #     raise e
    return {"dependencies": dependencies}


# TODO: schdule node do not return the correct result
def task_scheduler_node(state: AgentState):
    """LangGraph node that will schedule tasks based on dependencies and team availability"""
    dependencies = state["dependencies"]
    tasks = state["tasks"]
    insights = state["insights"] #"" if state["insights"] is None else state["insights"].insights[-1]
    prompt = f"""
        You are an experienced project scheduler tasked with creating an optimized project timeline.
        **Given the Structured Information:**
            - Tasks: {tasks.tasks}
            - Dependencies: {dependencies.dependencies}
            - Previous Insights: {insights}
            - Previous Schedule Iterations (if any): {state["schedule_iteration"]}
        **Your objectives are to:**
            you should strictly only output the schedule: list of TaskSchedule that each item is a dict that contains task , start_day (int) and end_day(int) respectively, and do not output other information.
        ** Do not output the code, you need output the results**
        """
      
    try:
        schedule = []
        output = llm.invoke(prompt).content
        output = output.replace("python\n", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "").replace("\n", "").replace(" ", "").replace("'", "").replace("```", "")
        output = output.split(",")
        for i in range(0, len(output), 3):
            schedule.append(TaskSchedule(task=output[i].replace("task:", ""), start_day=int(output[i+1][10:]), end_day=int(output[i+2][8:])))
    except Exception as e:
        schedule = get_default_schedule(tasks, dependencies)
    # schedule_llm = llm.with_structured_output(ScheduleList)
    # schedule: ScheduleList = schedule_llm.invoke(prompt)
    # try:
    #     schedule: ScheduleList = schedule_llm.invoke(prompt)
    # except Exception as e:
    #     raise e
    
    state["schedule"] = schedule
    state["schedule_iteration"].append(schedule)
    return state

def task_allocation_node(state: AgentState):
    """LangGraph node that will allocate tasks to team members"""
    tasks = state["tasks"]
    schedule = state["schedule"]
    team = state["team"]
    insights = state["insights"] #"" if state["insights"] is None else state["insights"].insights[-1]
    prompt = f"""
        You are a proficient project manager responsible for allocating tasks to team members efficiently.
        **Given:** 
            - **Tasks:** {tasks} 
            - **Schedule:** {schedule} 
            - **Team Members:** {team} 
            - **Previous Insights:** {insights} 
            - **Previous Task Allocations (if any):** {state["task_allocations_iteration"]} 
        **Your objectives are to:** 
            1. **Allocate Tasks:** 
                - Assign each task to a team member based on their expertise and current availability. 
            2. **Optimize Assignments:** 
                - Utilize insights from previous iterations to improve task allocations. 
            3. **you should strictly only output the task_allocations: list of TaskAllocation that each item is a dict that contains task and  team_member (dict contain name and profile), and do not output other information.**
                
        """
    structure_llm = llm.with_structured_output(TaskAllocationList)
    # vanila_output = llm.invoke(prompt).content
    task_allocations: TaskAllocationList = structure_llm.invoke(prompt)
    if task_allocations is None:
        task_allocations = get_default_task_allocations(tasks, schedule, team)
    # task_allocations = []
    # try:
    #     task_allocations: TaskAllocationList = structure_llm.invoke(prompt)
    # except Exception as e:
    #     # If the LLM fails to generate task allocations, break the loop
    #     logger.error(f"API 调用失败: {str(e)}")
    #     logger.error(f"错误详情: {str(e)}")
    #     raise e
    state["task_allocations"] = task_allocations
    state["task_allocations_iteration"].append(task_allocations)
    return state

def risk_assessment_node(state: AgentState):
    """LangGraph node that analyse risk associated with schedule and allocation of task"""
    schedule = state["schedule"]
    task_allocations=state["task_allocations"]
    prompt = f"""
        You are a seasoned project risk analyst tasked with evaluating the risks associated with the current project plan.
        **Given:**
            - **Task Allocations:** {task_allocations}
            - **Schedule:** {schedule}
            - **Previous Risk Assessments (if any):** {state['risks_iteration']}
        **Your objectives are to:**
            1. **Assess Risks:**
                - Analyze each allocated task and its scheduled timeline to identify potential risks.
            2. **Assign Risk Scores:**
                - Assign a risk score to each task on a scale from 0 (no risk) to 10 (high risk).
            3. **you should strictly only output the risks: list of Risk that each item is a dict that contains task and score, and do not output other information.**
        """
   
    structure_llm = llm.with_structured_output(RiskList)
    try:
        risks: RiskList = structure_llm.invoke(prompt)
    except Exception as e:
        risks = get_default_risks(task_allocations, schedule)
    if risks is None:
        risks = get_default_risks(task_allocations, schedule)
    project_task_risk_scores = [int(risk.score) for risk in risks.risks]
    project_risk_score = sum(project_task_risk_scores)
    state["risks"] = risks
    state["project_risk_score"] = project_risk_score
    state["iteration_number"] += 1
    state["project_risk_score_iterations"].append(project_risk_score)
    state["risks_iteration"].append(risks)
    return state

def insight_generation_node(state: AgentState):
    """LangGraph node that generate insights from the schedule, task allocation, and risk associated"""
    schedule = state["schedule"]
    task_allocations=state["task_allocations"]
    risks = state["risks"]
    # insights = state["insights"]
    prompt = f"""
        You are an expert project manager responsible for generating actionable insights to enhance the project plan.
        **Given:**
            - **Task Allocations:** {task_allocations}
            - **Schedule:** {schedule}
            - **Risk Analysis:** {risks}
        **Your objectives are to:**
            1. **Generate Critical Insights:**
            - Analyze the current task allocations, schedule, and risk assessments to identify areas for improvement.
            - Highlight any potential bottlenecks, resource conflicts, or high-risk tasks that may jeopardize project success.
            2. **Recommend Enhancements:**
            - Suggest adjustments to task assignments or scheduling to mitigate identified risks.
            3. **You should strictly output:**
                - List of insights, keep the result short and to the point
            
        """
    try:
        insights = llm.invoke(prompt).content
    except Exception as e:
        # If the LLM fails to generate insights, break the loop
        logger.error(f"API 调用失败: {str(e)}")
        logger.error(f"错误详情: {str(e)}")
        raise e
    return {"insights": insights}

def router(state: AgentState):
    """LangGraph node that will route the agent to the appropriate node based on the project description"""
    max_iteration = state["max_iteration"]
    iteration_number = state["iteration_number"]

    if iteration_number < max_iteration:
        if len(state["project_risk_score_iterations"])>1:
            if state["project_risk_score_iterations"][-1] <= state["project_risk_score_iterations"][0]:
                return END
            else:
                return "insight_generator"
        else:
            return "insight_generator"
    else:
        return END
    

def get_default_dependencies(task):
    """Generate default dependencies for tasks"""
    dependencies = []
    for i in range(len(task.tasks)):
        if i == 0:
            dependencies.append(TaskDependency(task=task.tasks[i], dependent_tasks=[]))
        else:
            dependencies.append(TaskDependency(task=task.tasks[i], dependent_tasks=[task.tasks[i-1]]))
    return DependencyList(dependencies=dependencies)


def get_default_schedule(tasks, dependencies):
    """Generate default schedule for tasks"""
    schedule = []
    start_day = 1
    for task in tasks.tasks:
        end_day = start_day + task.estimated_day
        schedule.append(TaskSchedule(task=task, start_day=start_day, end_day=end_day))
        start_day = end_day+1
    return ScheduleList(schedule=schedule)


def get_default_task_allocations(tasks, schedule, team):
    """Generate default task allocations for tasks"""
    task_allocations = []
    for i, task in enumerate(tasks.tasks):
        team_member = team.team_members[i % len(team.team_members)]
        task_allocations.append(TaskAllocation(task=task, team_member=team_member))
    return TaskAllocationList(task_allocations=task_allocations)

def get_default_risks(task_allocations, schedule):
    """Generate default risks for tasks"""
    risks = []
    for i, task_allocation in enumerate(task_allocations.task_allocations):
        risk_score = 1  # Default risk score
        risks.append(Risk(task=task_allocation.task, score=risk_score))
    return RiskList(risks=risks)