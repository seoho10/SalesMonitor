import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="StyleCode Analytics")

# 2. 제목
st.title("📊 StyleCode Data Lab v2.9")

# 3. 상단 필터 (가장 단순한 형태)
st.write("### Filters")
col1, col2, col3 = st.columns(3)
with col1:
    st.selectbox("Brand", ["MLB", "DISCOVERY", "DUVETICA"])
with col2:
    st.multiselect("Category", ["FOOTWEAR", "TOPS"], default="FOOTWEAR")
with col3:
    st.date_input("Period")

st.divider()

# 4. KPI 카드 (HTML 스타일 대신 스트림릿 기본 사용)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("총 주문금액", "₩ 1,240,500,000", "+12%")
kpi2.metric("총 주문수량", "15,420 EA", "-3%")
kpi3.metric("평균 판매단가", "₩ 80,450", "+5%")
kpi4.metric("반품률", "4.2%", "-0.5%")

# 5. 차트 영역 (Plotly 대신 스트림릿 내장 차트 사용)
st.subheader("Total Trend Analysis")
chart_data = pd.DataFrame(
    np.random.randint(100, 500, size=(20, 2)),
    columns=['Online', 'Offline']
)
st.line_chart(chart_data) # 이 함수는 별도 설치 없이 무조건 작동합니다.

# 6. 테이블 영역
st.subheader("Detailed Style Data")
dummy_df = pd.DataFrame(
    np.random.randn(5, 5),
    columns=['Style Code', 'Color', 'Size', 'Stock', 'Sales']
)
st.table(dummy_df) # dataframe 대신 정적 table로 표시