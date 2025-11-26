import os
import sqlite3
from typing import Optional

# Define path relative to THIS file
# Logic: utils/ -> agent/ -> root -> data/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "northwind.sqlite")


class NorthwindDB:
    """
    Centralized service for Northwind database interactions.
    Handles connection lifecycle, view setup, and schema abstraction.
    """

    _views_setup = False

    @classmethod
    def get_connection(cls) -> Optional[sqlite3.Connection]:
        """Establishes a connection and ensures views are ready."""
        if not cls._views_setup:
            cls._setup_views()
            cls._views_setup = True

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            print(f"DB Connection Error: {e}")
            return None

    @classmethod
    def _setup_views(cls):
        """Creates compatibility views to simplify table names for the AI."""
        conn = None
        try:
            # Connect directly to avoid recursion loop
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            views = [
                "CREATE VIEW IF NOT EXISTS orders AS SELECT * FROM Orders;",
                'CREATE VIEW IF NOT EXISTS order_items AS SELECT * FROM "Order Details";',
                "CREATE VIEW IF NOT EXISTS products AS SELECT * FROM Products;",
                "CREATE VIEW IF NOT EXISTS customers AS SELECT * FROM Customers;",
                "CREATE VIEW IF NOT EXISTS categories AS SELECT * FROM Categories;",
                "CREATE VIEW IF NOT EXISTS suppliers AS SELECT * FROM Suppliers;",
            ]
            for v in views:
                cursor.execute(v)
            conn.commit()
        except Exception as e:
            print(f"View setup error: {e}")
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_schema(cls) -> str:
        """
        Returns schema using SIMPLIFIED view names but ORIGINAL table metadata.
        """
        conn = cls.get_connection()
        if not conn:
            return ""

        # Map Original Tables (Source of Truth) -> Simplified Views (What AI sees)
        TABLE_MAP = {
            "Orders": "orders",
            "Order Details": "order_items",
            "Products": "products",
            "Customers": "customers",
            "Categories": "categories",
            "Suppliers": "suppliers",
        }

        schema = []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'"
            )
            tables = cursor.fetchall()

            for row in tables:
                original_name = row["name"]
                if original_name not in TABLE_MAP:
                    continue

                # Get Metadata (FKs) from original table
                cursor.execute(f"PRAGMA foreign_key_list('{original_name}')")
                fk_rows = cursor.fetchall()

                fk_map = {}
                for fk in fk_rows:
                    local_col = fk[3]
                    target_table_raw = fk[2]
                    target_col = fk[4] if fk[4] else "PK"
                    target_table_view = TABLE_MAP.get(
                        target_table_raw, target_table_raw
                    )
                    fk_map[local_col] = f"{target_table_view}.{target_col}"

                # Get Columns
                cursor.execute(f"PRAGMA table_info('{original_name}')")
                cols = cursor.fetchall()

                col_definitions = []
                for c in cols:
                    name = c["name"]
                    type_ = c["type"]
                    is_pk = c["pk"]
                    col_str = f"{name} ({type_})"
                    if is_pk:
                        col_str += " [PK]"
                    if name in fk_map:
                        col_str += f" [FK -> {fk_map[name]}]"
                    col_definitions.append(col_str)

                view_name = TABLE_MAP[original_name]
                schema.append(
                    f"Table: {view_name}\nColumns: {', '.join(col_definitions)}"
                )

        except sqlite3.Error as e:
            return f"Error retrieving schema: {e}"
        finally:
            conn.close()

        return "\n\n".join(schema)
