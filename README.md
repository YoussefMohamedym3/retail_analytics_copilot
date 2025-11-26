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

# Create compatibility views (fixes "Order Details" spacing issues)
sqlite3 data/northwind.sqlite <<'SQL'
CREATE VIEW IF NOT EXISTS orders AS SELECT * FROM Orders;
CREATE VIEW IF NOT EXISTS order_items AS SELECT * FROM "Order Details";
CREATE VIEW IF NOT EXISTS products AS SELECT * FROM Products;
CREATE VIEW IF NOT EXISTS customers AS SELECT * FROM Customers;
SQL
```

---

## ⚖️ Assumptions & Trade-offs

**Gross Margin Calculation:** The Northwind database lacks a cost field. We approximate **CostOfGoods = 0.7 × UnitPrice** when calculating margins.

---

## 🏗️ Architecture (In Progress)

- **Hybrid Agent:** Combines SQL (structured data) and RAG (unstructured policy/calendar data).
- **Tools:** SQLite query executor, specialized semantic retriever.
- **Orchestrator:** LangGraph state machine with repair loops.

---

## 📊 Performance (Coming Soon)

DSPy optimization metric deltas will be reported here.
