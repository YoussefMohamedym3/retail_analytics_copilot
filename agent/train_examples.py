import dspy

SCHEMA_CONTEXT = """
Table: categories
Columns: CategoryID (INTEGER) [PK], CategoryName (TEXT), Description (TEXT)

Table: customers
Columns: CustomerID (TEXT) [PK], CompanyName (TEXT), ContactName (TEXT), Country (TEXT), City (TEXT)

Table: order_items
Columns: OrderID (INTEGER) [PK], ProductID (INTEGER) [PK], UnitPrice (NUMERIC), Quantity (INTEGER), Discount (REAL)

Table: orders
Columns: OrderID (INTEGER) [PK], CustomerID (TEXT), OrderDate (DATETIME), ShippedDate (DATETIME), Freight (NUMERIC), ShipCountry (TEXT)

Table: products
Columns: ProductID (INTEGER) [PK], ProductName (TEXT), SupplierID (INTEGER), CategoryID (INTEGER), UnitPrice (NUMERIC), UnitsInStock (INTEGER), Discontinued (TEXT)

Table: suppliers
Columns: SupplierID (INTEGER) [PK], CompanyName (TEXT), Country (TEXT)
"""

train_examples = [
    # ==============================================================================
    # GROUP 1: Revenue & Basic Math
    # Rule: Revenue = SUM(UnitPrice * Quantity * (1 - Discount))
    # Rule: Always ROUND(..., 2) for currency/floats.
    # Rule: Use 'AS' for aliases.
    # ==============================================================================
    dspy.Example(
        question="What is the total revenue of all time?",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="float",
        sql_query="SELECT ROUND(SUM(UnitPrice * Quantity * (1 - Discount)), 2) FROM order_items",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Total revenue for 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"year": "1997"}',
        format_hint="float",
        # Note: Using BETWEEN for dates is safer and more standard than strftime
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate BETWEEN '1997-01-01' AND '1997-12-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Calculate total freight cost for all orders.",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="float",
        sql_query="SELECT ROUND(SUM(Freight), 2) FROM orders",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Total discounted amount (money saved) in 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"year": "1997"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * oi.Discount), 2) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate BETWEEN '1997-01-01' AND '1997-12-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 2: Gross Margin (The 0.7 Approximation Rule)
    # Rule: CostOfGoods = UnitPrice * 0.7
    # Math: Margin = (Revenue) - (Cost). Discount applies to Revenue ONLY.
    # Formula: (Price * Qty * (1-Disc)) - (Price * 0.7 * Qty)
    # ==============================================================================
    dspy.Example(
        question="Calculate total Gross Margin for 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"year": "1997", "cost_approx": "0.7 * UnitPrice"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM((oi.UnitPrice * oi.Quantity * (1 - oi.Discount)) - (oi.UnitPrice * 0.7 * oi.Quantity)), 2) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate BETWEEN '1997-01-01' AND '1997-12-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Top customer by Gross Margin.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"margin_logic": "Revenue - Cost (0.7 approx)"}',
        format_hint="{customer:str, margin:float}",
        sql_query="SELECT c.CompanyName AS customer, ROUND(SUM((oi.UnitPrice * oi.Quantity * (1 - oi.Discount)) - (oi.UnitPrice * 0.7 * oi.Quantity)), 2) AS margin FROM customers c JOIN orders o ON c.CustomerID = o.CustomerID JOIN order_items oi ON o.OrderID = oi.OrderID GROUP BY c.CustomerID ORDER BY margin DESC LIMIT 1",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Gross margin for 'Beverages' category in June 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"category": "Beverages", "date_range": "1997-06-01 to 1997-06-30"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM((oi.UnitPrice * oi.Quantity * (1 - oi.Discount)) - (oi.UnitPrice * 0.7 * oi.Quantity)), 2) FROM order_items oi JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID JOIN orders o ON oi.OrderID = o.OrderID WHERE c.CategoryName = 'Beverages' AND o.OrderDate BETWEEN '1997-06-01' AND '1997-06-30'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Which product generated the highest gross margin all time?",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="{product:str, margin:float}",
        sql_query="SELECT p.ProductName AS product, ROUND(SUM((oi.UnitPrice * oi.Quantity * (1 - oi.Discount)) - (oi.UnitPrice * 0.7 * oi.Quantity)), 2) AS margin FROM products p JOIN order_items oi ON p.ProductID = oi.ProductID GROUP BY p.ProductID ORDER BY margin DESC LIMIT 1",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 3: Category Joins (Anti-Hallucination)
    # Rule: NEVER use p.CategoryName. ALWAYS join Categories c.
    # ==============================================================================
    dspy.Example(
        question="List all products in the 'Beverages' category.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"category": "Beverages"}',
        format_hint="list",
        sql_query="SELECT p.ProductName FROM products p JOIN categories c ON p.CategoryID = c.CategoryID WHERE c.CategoryName = 'Beverages'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Total revenue for 'Dairy Products' in Summer 1997?",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"category": "Dairy Products", "date_range": "1997-06-01 to 1997-08-31"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) FROM order_items oi JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID JOIN orders o ON oi.OrderID = o.OrderID WHERE c.CategoryName = 'Dairy Products' AND o.OrderDate BETWEEN '1997-06-01' AND '1997-08-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Count of distinct products sold in 'Seafood'.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"category": "Seafood"}',
        format_hint="int",
        sql_query="SELECT COUNT(DISTINCT p.ProductID) FROM order_items oi JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE c.CategoryName = 'Seafood'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 4: Date Handling
    # Rule: Use BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
    # ==============================================================================
    dspy.Example(
        question="Total revenue in May 1997?",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"start_date": "1997-05-01", "end_date": "1997-05-31"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate BETWEEN '1997-05-01' AND '1997-05-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="How many orders were shipped after Dec 1st 1997?",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"date": "1997-12-01"}',
        format_hint="int",
        sql_query="SELECT COUNT(*) FROM orders WHERE ShippedDate > '1997-12-01'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Orders placed in Q1 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"start": "1997-01-01", "end": "1997-03-31"}',
        format_hint="int",
        sql_query="SELECT COUNT(*) FROM orders WHERE OrderDate BETWEEN '1997-01-01' AND '1997-03-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 5: Customers & Suppliers (NO Employees)
    # ==============================================================================
    dspy.Example(
        question="Who is the best customer by total revenue?",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="{customer:str, revenue:float}",
        sql_query="SELECT c.CompanyName AS customer, ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) AS revenue FROM customers c JOIN orders o ON c.CustomerID = o.CustomerID JOIN order_items oi ON o.OrderID = oi.OrderID GROUP BY c.CustomerID ORDER BY revenue DESC LIMIT 1",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="List top 3 customers from Germany by order count.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"country": "Germany"}',
        format_hint="list",
        sql_query="SELECT c.CompanyName, COUNT(o.OrderID) AS order_count FROM customers c JOIN orders o ON c.CustomerID = o.CustomerID WHERE c.Country = 'Germany' GROUP BY c.CustomerID ORDER BY order_count DESC LIMIT 3",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="How many products does 'Exotic Liquids' supply?",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"supplier": "Exotic Liquids"}',
        format_hint="int",
        sql_query="SELECT COUNT(*) FROM products p JOIN suppliers s ON p.SupplierID = s.SupplierID WHERE s.CompanyName = 'Exotic Liquids'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Revenue from customers in Western Europe (France, Germany).",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"countries": ["France", "Germany"]}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN customers c ON o.CustomerID = c.CustomerID WHERE c.Country IN ('France', 'Germany')",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 6: KPI Definitions (AOV)
    # Rule: AOV = Revenue / COUNT(DISTINCT OrderID)
    # ==============================================================================
    dspy.Example(
        question="What is the Average Order Value (AOV)?",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"formula": "TotalRevenue / DistinctOrders"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(UnitPrice * Quantity * (1 - Discount)) / COUNT(DISTINCT OrderID), 2) FROM order_items",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="AOV for Winter 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"start": "1997-12-01", "end": "1997-12-31"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)) / COUNT(DISTINCT o.OrderID), 2) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate BETWEEN '1997-12-01' AND '1997-12-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 7: Product Specifics (Inventory, Discontinued)
    # ==============================================================================
    dspy.Example(
        question="Which product has sold the most units all time?",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="{product:str, units:int}",
        sql_query="SELECT p.ProductName AS product, SUM(oi.Quantity) AS total_units FROM products p JOIN order_items oi ON p.ProductID = oi.ProductID GROUP BY p.ProductID ORDER BY total_units DESC LIMIT 1",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Revenue from discontinued products.",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="float",
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) FROM order_items oi JOIN products p ON oi.ProductID = p.ProductID WHERE p.Discontinued = '1'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Total value of inventory (at cost 0.7 approx).",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"cost_approx": "0.7 * UnitPrice"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(UnitsInStock * UnitPrice * 0.7), 2) FROM products",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 8: Marketing Calendar & Hybrid Constraints (Important!)
    # ==============================================================================
    dspy.Example(
        question="Which product category had the highest quantity sold in Summer Beverages 1997?",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"date_range": "1997-06-01 to 1997-06-30", "focus": "Beverages"}',
        format_hint="{category:str, quantity:int}",
        sql_query="SELECT c.CategoryName AS category, SUM(oi.Quantity) AS quantity FROM orders o JOIN order_items oi ON o.OrderID = oi.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate BETWEEN '1997-06-01' AND '1997-06-30' AND c.CategoryName IN ('Beverages') GROUP BY c.CategoryID ORDER BY quantity DESC LIMIT 1",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Total revenue from 'Beverages' category during 'Summer Beverages 1997'.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"category": "Beverages", "date_range": "1997-06-01 to 1997-06-30"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) FROM order_items oi JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID JOIN orders o ON oi.OrderID = o.OrderID WHERE c.CategoryName = 'Beverages' AND o.OrderDate BETWEEN '1997-06-01' AND '1997-06-30'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Top customer by gross margin in 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"year": "1997", "cost_approx": "0.7 * UnitPrice"}',
        format_hint="{customer:str, margin:float}",
        # Correct logic: (Rev - Cost)
        sql_query="SELECT c.CompanyName AS customer, ROUND(SUM((oi.UnitPrice * oi.Quantity * (1 - oi.Discount)) - (oi.UnitPrice * 0.7 * oi.Quantity)), 2) AS margin FROM customers c JOIN orders o ON c.CustomerID = o.CustomerID JOIN order_items oi ON o.OrderID = oi.OrderID WHERE o.OrderDate BETWEEN '1997-01-01' AND '1997-12-31' GROUP BY c.CustomerID ORDER BY margin DESC LIMIT 1",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 9: Trap Examples (Teaching what NOT to do)
    # ==============================================================================
    dspy.Example(
        question="Count products in Beverages category",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"category": "Beverages"}',
        format_hint="int",
        # Trap: Do not use p.CategoryName. Join categories.
        sql_query="SELECT COUNT(*) FROM products p JOIN categories c ON p.CategoryID = c.CategoryID WHERE c.CategoryName = 'Beverages'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Top customer by revenue (name only)",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="str",
        # Trap: Must join Customers table for CompanyName
        sql_query="SELECT c.CompanyName FROM customers c JOIN orders o ON c.CustomerID = o.CustomerID JOIN order_items oi ON o.OrderID = oi.OrderID GROUP BY c.CustomerID ORDER BY SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)) DESC LIMIT 1",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Revenue for orders in June 1997",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"start": "1997-06-01", "end": "1997-06-30"}',
        format_hint="float",
        # Trap: Use BETWEEN, not non-standard syntax like BETWEWEN
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate BETWEEN '1997-06-01' AND '1997-06-30'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    # ==============================================================================
    # GROUP 10: Formatting & Type Specifics
    # ==============================================================================
    dspy.Example(
        question="Count of distinct countries we ship to.",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="int",
        sql_query="SELECT COUNT(DISTINCT ShipCountry) FROM orders",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Top 3 products by revenue in 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"year": "1997"}',
        format_hint="list",
        sql_query="SELECT p.ProductName, ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) AS revenue FROM order_items oi JOIN products p ON oi.ProductID = p.ProductID JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate BETWEEN '1997-01-01' AND '1997-12-31' GROUP BY p.ProductID ORDER BY revenue DESC LIMIT 3",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Customers who bought 'Chai' in 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"product": "Chai", "year": "1997"}',
        format_hint="list",
        sql_query="SELECT DISTINCT c.CompanyName FROM customers c JOIN orders o ON c.CustomerID = o.CustomerID JOIN order_items oi ON o.OrderID = oi.OrderID JOIN products p ON oi.ProductID = p.ProductID WHERE p.ProductName = 'Chai' AND o.OrderDate BETWEEN '1997-01-01' AND '1997-12-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Revenue from 'Beverages' vs 'Condiments' in 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"categories": ["Beverages", "Condiments"], "year": 1997}',
        format_hint="list",
        sql_query="SELECT c.CategoryName, ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) AS revenue FROM order_items oi JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID JOIN orders o ON oi.OrderID = o.OrderID WHERE c.CategoryName IN ('Beverages', 'Condiments') AND o.OrderDate BETWEEN '1997-01-01' AND '1997-12-31' GROUP BY c.CategoryName",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Count of orders shipped to Canada.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"country": "Canada"}',
        format_hint="int",
        sql_query="SELECT COUNT(*) FROM orders WHERE ShipCountry = 'Canada'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Average freight cost per country.",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="list",
        sql_query="SELECT ShipCountry, ROUND(AVG(Freight), 2) AS avg_freight FROM orders GROUP BY ShipCountry ORDER BY avg_freight DESC",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Number of suppliers in USA.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"country": "USA"}',
        format_hint="int",
        sql_query="SELECT COUNT(*) FROM suppliers WHERE Country = 'USA'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="How many categories do we have?",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="int",
        sql_query="SELECT COUNT(*) FROM categories",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Orders with freight over 100.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"min_freight": 100}',
        format_hint="int",
        sql_query="SELECT COUNT(*) FROM orders WHERE Freight > 100",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Products with zero stock.",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="list",
        sql_query="SELECT ProductName FROM products WHERE UnitsInStock = 0",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Average discount given in 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"year": "1997"}',
        format_hint="float",
        sql_query="SELECT ROUND(AVG(oi.Discount), 4) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate BETWEEN '1997-01-01' AND '1997-12-31'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Revenue from 'Grains/Cereals' in Q2 1997.",
        db_schema=SCHEMA_CONTEXT,
        constraints='{"category": "Grains/Cereals", "start": "1997-04-01", "end": "1997-06-30"}',
        format_hint="float",
        sql_query="SELECT ROUND(SUM(oi.UnitPrice * oi.Quantity * (1 - oi.Discount)), 2) FROM order_items oi JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID JOIN orders o ON oi.OrderID = o.OrderID WHERE c.CategoryName = 'Grains/Cereals' AND o.OrderDate BETWEEN '1997-04-01' AND '1997-06-30'",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
    dspy.Example(
        question="Top customer by order count.",
        db_schema=SCHEMA_CONTEXT,
        constraints="{}",
        format_hint="{customer:str, count:int}",
        sql_query="SELECT c.CompanyName AS customer, COUNT(o.OrderID) AS order_count FROM customers c JOIN orders o ON c.CustomerID = o.CustomerID GROUP BY c.CustomerID ORDER BY order_count DESC LIMIT 1",
    ).with_inputs("question", "db_schema", "constraints", "format_hint"),
]
