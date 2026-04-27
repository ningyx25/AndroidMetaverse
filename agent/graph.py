from langgraph.graph import StateGraph, START, END

from agent.state import SuiteState
from agent.suite_agent import SuiteAgent
from agent.gui_agent import GUIAgent
from agent.android_agent import AndroidAgent


def build_graph(suite_agent: SuiteAgent, gui_agent: GUIAgent, android_agent: AndroidAgent):
    graph = StateGraph(SuiteState)

    graph.add_node("initialize_task", suite_agent.initialize_task)
    graph.add_node("get_task_goal", suite_agent.get_task_goal)
    graph.add_node("plan_action", gui_agent.plan_action)
    graph.add_node("execute_action", android_agent.execute_action)
    graph.add_node("get_task_score", suite_agent.get_task_score)

    graph.add_edge(START, "initialize_task")
    graph.add_edge("initialize_task", "get_task_goal")
    graph.add_edge("get_task_goal", "plan_action")
    graph.add_conditional_edges(
        "plan_action",
        suite_agent.should_continue,
        {"execute_action": "execute_action", "get_task_score": "get_task_score"}
    )
    graph.add_edge("execute_action", "plan_action")
    graph.add_edge("get_task_score", END)

    return graph.compile()
