# Retail Analytics Copilot

A local, private AI agent that answers retail analytics questions using **RAG** (over local docs) and **SQL** (over a local SQLite database). Built with **LangGraph** and **DSPy**.

## 🛠️ Setup & Installation

### 1. Prerequisites
- **Python 3.10+**
- **Ollama**: Download from https://ollama.com
- **Model**: Pull the required local model:

```bash
ollama pull phi3.5:3.8b-mini-instruct-q4_K_M
```

### 2. Installation
Clone the repo and set up the environment:

```bash
git clone https://github.com/YoussefMohamedym3/retail_analytics_copilot.git
cd retail_analytics_copilot

# Create and activate Conda environment (Python 3.11)
conda create -n retail_copilot python=3.11 -y
conda activate retail_copilot

# Install dependencies
pip install -r requirements.txt
```

### 3. Data Setup
Download the Northwind database and create the documentation corpus:

```bash
# Create data directory and download DB
curl -L -o data/northwind.sqlite https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/main/dist/northwind.db
```

---

## ⚖️ Assumptions & Trade-offs

1.  **Gross Margin:** The Northwind database lacks a cost field. We approximate `CostOfGoods = 0.7 * UnitPrice` when calculating margins.
2.  **Local Retrieval:** We use `rank_bm25` for retrieval instead of vector embeddings. This keeps the agent lightweight (no heavy model downloads) and deterministic, satisfying the "No external calls" constraint.

---

## 🏗️ Architecture (In Progress)

- **Hybrid Agent:** Combines SQL (structured data) and RAG (unstructured policy/calendar data).
- **Orchestrator:** LangGraph state machine with repair loops.

---

## 📊 Performance (Coming Soon)

DSPy optimization metric deltas will be reported here.
