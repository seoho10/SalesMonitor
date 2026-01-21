import streamlit as st
import snowflake.connector
import pandas as pd

st.title("Sales Monitor Dashboard")

# Snowflake 연결 함수
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"]
    )

try:
    conn = init_connection()
    st.success("Snowflake 연결 성공!")

    # 테스트 쿼리 (실제 테이블명으로 변경 필요)
    query = "SELECT CURRENT_VERSION()"
    df = pd.read_sql(query, conn)
    st.write(df)
except Exception as e:
    st.error(f"연결 오류: {e}")