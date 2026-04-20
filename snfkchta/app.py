import streamlit as st
from utils import load_all_metadata, generate_sql, run_query

st.set_page_config(page_title="AI Data Chatbot", layout="wide")

st.title("💬 AI Data Assistant")
st.write("Ask questions about your Snowflake data")

# Load metadata once
metadata = load_all_metadata()

# Sidebar (debug view)
with st.sidebar:
    st.subheader("📄 Metadata Preview")
    st.text_area("Loaded Metadata", metadata, height=300)

# Input
question = st.text_input("Enter your question:")

if st.button("Ask"):
    if question:
        # Generate SQL
        sql = generate_sql(question, metadata)

        st.subheader("🧾 Generated SQL")
        st.code(sql, language="sql")

        # Run query
        try:
            df = run_query(sql)

            st.subheader("📊 Result")
            st.dataframe(df)

        except Exception as e:
            st.error(f"Error running query: {e}")