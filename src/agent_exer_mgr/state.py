from typing import Annotated, Any, Dict, Sequence, TypedDict, List, Union
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, START,END
import operator

from langchain_core.messages import BaseMessage
def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}


class Plan(BaseModel):
    tasks: List[str]
    duration: List[int]
    intensity: List[int]

class Insight(BaseModel):
    content: str
    score: int 

    
class AgentState(TypedDict):
    goal: str
    behavior_summary: Dict[str, Any]
    metrics_summary: Dict[str, Any]
    plan: Union[Plan, None]
    insights: Union[Insight, None]
    schedule: Dict[str, Any]
    history_info: Dict[str, Any]
    max_iteration: int
    iteration_number: int
    insight_scores_iterations:list[int]


if __name__ == "__main__":
    state = AgentState(data=[1, 2, 3])
    print(state["data"])