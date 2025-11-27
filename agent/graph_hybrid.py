import logging

from langgraph.graph import END, START, StateGraph

from agent.nodes.planner import plan_query
from agent.nodes.retriever import retrieve_node
from agent.nodes.router import route_query
from agent.state import AgentState

logger = logging.getLogger("GraphHybrid")


class RetailAnalyticsWorkflow:
    """
    Builds and compiles the LangGraph workflow.
    Current Phase: Router -> Retriever -> Planner (Logic Verification)
    """

    def __init__(self):
        self.builder = StateGraph(AgentState)
        self.graph = None

    def __load_nodes(self):
        self.builder.add_node("router", route_query)
        self.builder.add_node("retriever", retrieve_node)
        self.builder.add_node("planner", plan_query)

    def __load_edges(self):
        # 1. Start -> Router
        self.builder.add_edge(START, "router")

        # 2. Router Logic
        # Both 'rag' and 'hybrid' need documents, so they both go to Retriever.
        def router_decision(state):
            return state.get("route", "hybrid")

        self.builder.add_conditional_edges(
            "router",
            router_decision,
            {
                "rag": "retriever",
                "hybrid": "retriever",  # <--- CHANGE: Hybrid now goes to Retriever first
                "sql": END,
            },
        )

        # 3. Retriever Logic (The Fork)
        # After retrieval, where do we go?
        def post_retrieval_decision(state):
            route = state.get("route")
            if route == "hybrid":
                return "planner"
            return "end"  # 'rag' goes to end for now

        self.builder.add_conditional_edges(
            "retriever", post_retrieval_decision, {"planner": "planner", "end": END}
        )

        # 4. Planner -> END (For now)
        self.builder.add_edge("planner", END)

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
