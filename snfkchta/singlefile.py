import streamlit as st
import snowflake.connector
import pandas as pd
import os

# ==============================
# CONFIG (EDIT THIS)
# ==============================
SNOWFLAKE_CONFIG = {
    "user": "YOUR_USER",
    "password": "YOUR_PASSWORD",
    "account": "YOUR_ACCOUNT",
    "warehouse": "YOUR_WH",
    "database": "YOUR_DB",
    "schema": "YOUR_SCHEMA"
}

METADATA_FOLDER = "metadata"  # folder with .md files

# ==============================
# SNOWFLAKE CONNECTION
# ==============================
@st.cache_resource
def get_connection():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

@st.cache_data
def run_query(sql):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    df = cur.fetch_pandas_all()
    return df

# ==============================
# LOAD METADATA
# ==============================
@st.cache_data
def load_metadata_files():
    metadata_files = {}
    for file in os.listdir(METADATA_FOLDER):
        if file.endswith(".md"):
            with open(os.path.join(METADATA_FOLDER, file), "r") as f:
                metadata_files[file] = f.read()
    return metadata_files

# ==============================
# SELECT RELEVANT METADATA
# ==============================
def get_relevant_metadata(question, metadata_files):
    q = question.lower()
    selected = ""

    for file, content in metadata_files.items():
        if any(word in content.lower() for word in q.split()):
            selected += content + "\n\n"

    # fallback (if nothing matched)
    if not selected:
        selected = "\n\n".join(metadata_files.values())

    return selected

# ==============================
# SQL GENERATION (REPLACE WITH LLM)
# ==============================
def generate_sql(question, metadata):
    q = question.lower()

    # Basic rules (replace with LLM later)
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
    return "SELECT * FROM sales_data LIMIT 50"

# ==============================
# SQL VALIDATION
# ==============================
def validate_sql(sql):
    bad_words = ["drop", "delete", "truncate"]
    return not any(word in sql.lower() for word in bad_words)

# ==============================
# EXPLANATION (BASIC)
# ==============================
def explain_result(question, df):
    return f"Showing results for: '{question}'. Total rows: {len(df)}"

# ==============================
# STREAMLIT UI
# ==============================
st.set_page_config(page_title="AI Data Assistant", layout="wide")

st.title("💬 AI Data Assistant")
st.write("Ask questions about your Snowflake data")

# Load metadata
metadata_files = load_metadata_files()

# Sidebar
with st.sidebar:
    st.subheader("📄 Metadata Files")
    st.write(list(metadata_files.keys()))

# Chat memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input
user_input = st.chat_input("Ask your data...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get relevant metadata
    metadata = get_relevant_metadata(user_input, metadata_files)

    # Generate SQL
    sql = generate_sql(user_input, metadata)

    with st.chat_message("assistant"):
        st.subheader("🧾 Generated SQL")
        st.code(sql, language="sql")

        # Validate SQL
        if not validate_sql(sql):
            st.error("Unsafe query detected!")
        else:
            try:
                df = run_query(sql)

                st.subheader("📊 Result")
                st.dataframe(df)

                # Chart (auto)
                if len(df.columns) == 2:
                    st.subheader("📈 Chart")
                    st.bar_chart(df)

                # Explanation
                st.subheader("🧠 Insight")
                st.write(explain_result(user_input, df))

                # Save response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Query executed successfully. Rows: {len(df)}"
                })

            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error: {e}"
                })