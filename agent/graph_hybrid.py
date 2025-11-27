import logging

from langgraph.graph import END, START, StateGraph

from agent.nodes.nl_sql import generate_sql_node  # <--- NEW IMPORT
from agent.nodes.planner import plan_query
from agent.nodes.retriever import retrieve_node
from agent.nodes.router import route_query
from agent.state import AgentState

logger = logging.getLogger("GraphHybrid")


class RetailAnalyticsWorkflow:
    """
    Builds and compiles the LangGraph workflow.
    Current Phase: Router -> (Retriever->Planner) -> SQL Gen
    """

    def __init__(self):
        self.builder = StateGraph(AgentState)
        self.graph = None

    def __load_nodes(self):
        self.builder.add_node("router", route_query)
        self.builder.add_node("retriever", retrieve_node)
        self.builder.add_node("planner", plan_query)
        self.builder.add_node("sql_gen", generate_sql_node)  # <--- NEW NODE

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
                "sql": "sql_gen",  # <--- Direct SQL path
            },
        )

        # Retriever Logic
        def post_retrieval_decision(state):
            route = state.get("route")
            if route == "hybrid":
                return "planner"
            return "end"  # RAG (policy questions) end here for now

        self.builder.add_conditional_edges(
            "retriever", post_retrieval_decision, {"planner": "planner", "end": END}
        )

        # Planner -> SQL Gen (Hybrid Path)
        self.builder.add_edge("planner", "sql_gen")

        # SQL Gen -> END (For verification)
        self.builder.add_edge("sql_gen", END)

    def get_graph(self):
        self.__load_nodes()
        self.__load_edges()
        self.graph = self.builder.compile()
        return self.graph


# Visualization (same as before)
try:
    from IPython.display import Image

    workflow = RetailAnalyticsWorkflow()
    app = workflow.get_graph()
    image_bytes = app.get_graph(xray=True).draw_mermaid_png()
    with open("workflow_diagram.png", "wb") as f:
        f.write(image_bytes)
except Exception:
    pass
