import logging

from langgraph.graph import END, START, StateGraph

from agent.nodes.executor import execute_sql_node
from agent.nodes.nl_sql import generate_sql_node
from agent.nodes.planner import plan_query
from agent.nodes.repair import repair_sql_node
from agent.nodes.retriever import retrieve_node
from agent.nodes.router import route_query
from agent.state import AgentState

logger = logging.getLogger("GraphHybrid")


class RetailAnalyticsWorkflow:
    """
    Builds and compiles the LangGraph workflow.
    Current Phase: Router -> ... -> Executor -> Repair Loop
    """

    def __init__(self):
        self.builder = StateGraph(AgentState)
        self.graph = None

    def __load_nodes(self):
        self.builder.add_node("router", route_query)
        self.builder.add_node("retriever", retrieve_node)
        self.builder.add_node("planner", plan_query)
        self.builder.add_node("sql_gen", generate_sql_node)
        self.builder.add_node("executor", execute_sql_node)
        self.builder.add_node("repair", repair_sql_node)

    def __load_edges(self):
        self.builder.add_edge(START, "router")

        # Router Logic
        def router_decision(state):
            return state.get("route", "hybrid")

        self.builder.add_conditional_edges(
            "router",
            router_decision,
            {
                "rag": "retriever",
                "hybrid": "retriever",
                "sql": "sql_gen",
            },
        )

        # Retriever Logic
        def post_retrieval_decision(state):
            route = state.get("route")
            if route == "hybrid":
                return "planner"
            return "end"  # RAG ends here for now

        self.builder.add_conditional_edges(
            "retriever", post_retrieval_decision, {"planner": "planner", "end": END}
        )

        # Planner -> SQL Gen
        self.builder.add_edge("planner", "sql_gen")

        # SQL Gen -> Executor
        self.builder.add_edge("sql_gen", "executor")

        # Executor Logic (The Loop)
        def post_execution_decision(state):
            is_error = state.get("is_sql_error", False)
            steps = state.get("repair_steps", 0)

            if is_error and steps < 2:
                return "repair"  # Loop back
            return "end"  # Proceed (success or give up)

        self.builder.add_conditional_edges(
            "executor", post_execution_decision, {"repair": "repair", "end": END}
        )

        # Repair -> Executor (Retry the new query)
        self.builder.add_edge("repair", "executor")

    def get_graph(self):
        self.__load_nodes()
        self.__load_edges()
        self.graph = self.builder.compile()
        return self.graph


# Visualization
try:
    from IPython.display import Image

    workflow = RetailAnalyticsWorkflow()
    app = workflow.get_graph()
    image_bytes = app.get_graph(xray=True).draw_mermaid_png()
    with open("workflow_diagram.png", "wb") as f:
        f.write(image_bytes)
except Exception:
    pass
