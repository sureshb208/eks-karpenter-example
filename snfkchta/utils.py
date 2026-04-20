import os
import snowflake.connector
import pandas as pd
from config import SNOWFLAKE_CONFIG

# -----------------------------
# Load all metadata files
# -----------------------------
def load_all_metadata(folder="metadata"):
    metadata = ""
    for file in os.listdir(folder):
        if file.endswith(".md"):
            with open(os.path.join(folder, file), "r") as f:
                metadata += f.read() + "\n\n"
    return metadata

# -----------------------------
# Snowflake connection
# -----------------------------
def get_connection():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

def run_query(sql):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    df = cur.fetch_pandas_all()
    return df

# -----------------------------
# Simple SQL generator (LLM replace later)
# -----------------------------
def generate_sql(question, metadata):
    q = question.lower()

    # Basic logic (extend gradually)
    if "revenue" in q and "yesterday" in q:
        return """
        SELECT SUM(revenue) AS total_revenue
        FROM sales_data
        WHERE order_date = CURRENT_DATE - 1
        """

    if "revenue" in q and "region" in q:
        return """
        SELECT region, SUM(revenue) AS total_revenue
        FROM sales_data
        GROUP BY region
        """

    if "count" in q or "total records" in q:
        return "SELECT COUNT(*) FROM sales_data"

    # fallback
    return "SELECT * FROM sales_data LIMIT 10"