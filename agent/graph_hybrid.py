import logging

from langgraph.graph import END, START, StateGraph

from agent.nodes.router import route_query
from agent.state import AgentState

logger = logging.getLogger("GraphHybrid")


class RetailAnalyticsWorkflow:
    """
    Builds and compiles the LangGraph workflow.
    Current Phase: Router Logic Verification (Start -> Router -> End)
    """

    def __init__(self):
        self.builder = StateGraph(AgentState)
        self.graph = None

    def __load_nodes(self):
        # Only the Router Node for this test
        self.builder.add_node("router", route_query)

    def __load_edges(self):
        # 1. Start -> Router
        self.builder.add_edge(START, "router")

        # 2. Router -> END
        # We use a conditional edge to prove the router output is valid
        # even though all paths lead to END for now.
        def get_next_step(state):
            # This confirms the state has the 'route' key we expect
            return state.get("route", "hybrid")

        self.builder.add_conditional_edges(
            "router", get_next_step, {"rag": END, "sql": END, "hybrid": END}
        )

    def get_graph(self):
        self.__load_nodes()
        self.__load_edges()
        self.graph = self.builder.compile()
        return self.graph


# --- Visualization (Optional) ---
try:
    from IPython.display import Image

    workflow = RetailAnalyticsWorkflow()
    app = workflow.get_graph()
    image_bytes = app.get_graph(xray=True).draw_mermaid_png()
    with open("workflow_diagram.png", "wb") as f:
        f.write(image_bytes)
    logger.info("✅ Graph diagram saved to 'workflow_diagram.png'")
except Exception:
    pass
