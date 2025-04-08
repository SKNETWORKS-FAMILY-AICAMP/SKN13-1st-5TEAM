
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os

# 한글 폰트 설정
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 기본 설정
st.set_page_config(page_title="법인차량 대시보드", layout="wide")

# 사이드바 메뉴 구성
menu = st.sidebar.radio("📋 메뉴 선택", ["차량 정보 필터", "데이터 시각화", "자주 묻는 질문"])

# 데이터 불러오기
@st.cache_data
def load_data():
    return pd.read_csv("corporate_cars.csv")



# 가격을 '1억 5431만원' 형태로 포맷하는 함수
def format_price(value):
    value = int(value)
    if value >= 10000:
        return f"{value // 10000}억 {value % 10000}만원"
    else:
        return f"{value}만원"

df = load_data()

# 단위 조정
df['배기량'] = df['배기량'].str.replace("L", "").str.replace("이하", "000cc 이하").str.replace("이상", "000cc 이상").str.replace("~", "000cc~").str.replace(" ", "")
df['배기량'] = df['배기량'].str.replace("1.6", "1600").str.replace("2.0", "2000").str.replace("1.6", "1600").str.replace("2.0", "2000")
df['배기량'] = df['배기량'].str.replace("000cc", "cc")

if menu == "차량 정보 필터":
    st.title("🚘 법인차량 조건별 정보 확인")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_prices = st.multiselect("💰 가격대", df['가격대'].unique())

    with col2:
        selected_engines = st.multiselect("🔧 배기량", df['배기량'].unique())

    with col3:
        selected_brands = st.multiselect("🏢 제조사", df['제조사'].unique())

    col4, col5 = st.columns(2)

    with col4:
        selected_fuels = st.multiselect("⛽ 연료", df['연료'].unique())

    with col5:
        selected_types = st.multiselect("🚗 차량 유형", df['유형'].unique())

    filtered_df = df.copy()
    if selected_prices:
        filtered_df = filtered_df[filtered_df['가격대'].isin(selected_prices)]
    if selected_engines:
        filtered_df = filtered_df[filtered_df['배기량'].isin(selected_engines)]
    if selected_brands:
        filtered_df = filtered_df[filtered_df['제조사'].isin(selected_brands)]
    if selected_fuels:
        filtered_df = filtered_df[filtered_df['연료'].isin(selected_fuels)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['유형'].isin(selected_types)]

    # 가격 단위 붙이기
    df_display = filtered_df.copy()
    df_display['2024년_가격'] = df_display['2024년_가격'].apply(format_price)
    df_display['2025년_가격'] = df_display['2025년_가격'].apply(format_price)

    st.subheader("🔍 필터링된 차량 목록")
    st.dataframe(df_display)

elif menu == "데이터 시각화":
    st.title("📊 법인차량 데이터 시각화")

    chart_brands = st.multiselect("📌 제조사 선택", df['제조사'].unique())

    if chart_brands:
        chart_df = df[df['제조사'].isin(chart_brands)]

        group_df = chart_df.groupby('제조사').agg({
            '2024년_판매량': 'sum',
            '2025년_판매량': 'sum',
            '2024년_가격': 'mean',
            '2025년_가격': 'mean'
        })

        fig, ax1 = plt.subplots(figsize=(10, 6))

        x = range(len(group_df.index))
        bar1 = ax1.bar(x, group_df['2024년_판매량'], width=0.35, label='2024년 판매량', color='#4e79a7aa', zorder=3)
        bar2 = ax1.bar([p + 0.35 for p in x], group_df['2025년_판매량'], width=0.35, label='2025년 판매량', color='#f28e2b88', zorder=3)
        ax1.set_ylabel("판\n매\n량", rotation=0, labelpad=30, fontsize=12)
        ax1.set_xlabel("제조사", fontsize=12)
        ax1.set_xticks([p + 0.175 for p in x])
        ax1.set_xticklabels(group_df.index)
        ax1.grid(False)
        ax1.set_axisbelow(True)

        ax2 = ax1.twinx()
        ax2.plot([p + 0.175 for p in x], group_df['2024년_가격'], marker='o', color='#59a14f', label='2024년 가격 (단위 : 만원)', zorder=4)
        ax2.plot([p + 0.175 for p in x], group_df['2025년_가격'], marker='o', color='#e15759', label='2025년 가격 (단위 : 만원)', zorder=4)
        ax2.set_ylabel("평\n균\n가\n격", rotation=0, labelpad=50, fontsize=12)
        ax2.grid(False)

        plt.title("제조사별 판매량 및 평균 가격 비교", fontsize=14)
        ax1.legend(loc='lower left', bbox_to_anchor=(-0.02, -0.25), fontsize=9, frameon=True)
        ax2.legend(loc='lower right', bbox_to_anchor=(1.02, -0.25), fontsize=9, frameon=True)

        st.pyplot(fig)
    else:
        st.info("비교할 제조사를 선택해주세요.")

elif menu == "자주 묻는 질문":
    st.title("❓ 자주 묻는 질문 (FAQ)")
    with st.expander("Q1. 법인차량을 개인적으로 사용해도 되나요?"):
        st.write("A. 업무 외의 개인적 사용은 세무상 문제가 발생할 수 있습니다. 규정을 반드시 확인하세요.")
    with st.expander("Q2. 법인차량 구매 시 세금 혜택이 있나요?"):
        st.write("A. 네, 부가가치세 환급 등 다양한 혜택이 존재합니다.")
    with st.expander("Q3. 전기차도 법인차로 등록 가능한가요?"):
        st.write("A. 네, 오히려 친환경 혜택으로 인해 많이 권장되고 있습니다.")
