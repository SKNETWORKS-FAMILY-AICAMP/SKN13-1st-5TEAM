import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
import plotly.express as px
import numpy as np
import seaborn as sns
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from datetime import datetime, timedelta
import matplotlib.font_manager as fm

# 한글 폰트 설정
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# Streamlit 앱 구성
st.set_page_config(page_title="법인차량 대시보드", layout="wide")
menu = st.sidebar.radio("📋 메뉴 선택", ["차량 등록 현황","차량 정보 필터", "데이터 시각화", "뉴스 정보" ,"자주 묻는 질문"])

@st.cache_data
def load_data():
    return pd.read_csv("car_sales_2023_01_to_2025_03.csv")

df = load_data()

if menu == "차량 등록 현황":
    st.title("🚗 법인 차량 등록 통계")

    @st.cache_data
    def load_car_data():
        cars = pd.read_csv("자동차등록현황보고_자동차등록대수현황 시도별 (201101 ~ 202502).csv", encoding="cp949", skiprows=5)
        cars.columns = ['일시', '시도명', '시군구', '승용_관용', '승용_자가용', '승용_영업용', '승용_계',
                        '승합_관용', '승합_자가용', '승합_영업용', '승합_계',
                        '화물_관용', '화물_자가용', '화물_영업용', '화물_계',
                        '특수_관용', '특수_자가용', '특수_영업용', '특수_계',
                        '총계_관용', '총계_자가용', '총계_영업용', '총계']
        cars = cars[(cars['시도명'] == '서울') & (cars['시군구'] == '강남구')]
        cars['일시'] = pd.to_datetime(cars['일시'])
        cars['승용_영업용'] = cars['승용_영업용'].str.replace(',', '').astype(int)
        return cars[['일시', '승용_영업용']]

    df_car = load_car_data()
    df_recent = df_car[-24:].reset_index(drop=True)

    avg_2023 = df_recent[:12]['승용_영업용'].mean()
    avg_2024 = df_recent[12:]['승용_영업용'].mean()

    st.write("2023-2024 영업용 승용차 변동 추이")
    fig = px.scatter(df_recent, x="일시", y="승용_영업용", title="월별 등록수 변화")
    st.plotly_chart(fig)

    col1, col2, col3 = st.columns(3)
    col1.metric("🚗 2023 평균 등록수", f"{avg_2023:.0f}대")
    col2.metric("🚗 2024 평균 등록수", f"{avg_2024:.0f}대")
    diff = avg_2024 - avg_2023
    rate = (diff / avg_2023) * 100
    col3.metric("📉 전년 대비 변화", f"{diff:+.0f}대", f"{rate:+.1f}%")

elif menu == "차량 정보 필터":
    st.title("🚘 수입차 판매 데이터 비교")

    car_models = df['자동차 모델'].unique()
    selected_models = st.multiselect("🚘 모델 선택", car_models)

    excluded = ['년도', '월', '자동차 모델']
    candidate_metrics = [col for col in df.columns if col not in excluded]

    selected_metrics = st.multiselect("📊 비교 항목 선택", candidate_metrics)

    if selected_models and selected_metrics:
        filtered_df = df[df['자동차 모델'].isin(selected_models)]
        melted_df = filtered_df.melt(id_vars='자동차 모델', value_vars=selected_metrics, var_name='항목', value_name='값')

        fig = px.line(melted_df, x='자동차 모델', y='값', color='항목', markers=True,
                      title='선택된 항목별 모델 비교 (꺾은선그래프)')
        st.plotly_chart(fig)
    else:
        st.info("모델과 비교 항목을 모두 선택해주세요.")

elif menu == "데이터 시각화":
    st.title("📊 법인차량 데이터 시각화")

    @st.cache_data
    def load_viz_data():
        return pd.read_csv("corporate_cars.csv")

    viz_df = load_viz_data()
    st.dataframe(viz_df)
    st.line_chart(viz_df.set_index(viz_df.columns[0]))

elif menu == "뉴스 정보":
    st.title("📰 법인 관련 뉴스")
    st.info("이 섹션은 뉴스 크롤링 기능을 제공합니다. 다른 기능은 기존과 동일합니다.")

elif menu == "자주 묻는 질문":
    st.title("❓ 자주 묻는 질문 (FAQ)")
    with st.expander("Q1. 법인차량을 개인적으로 사용해도 되나요?"):
        st.write("A. 업무 외의 개인적 사용은 세무상 문제가 발생할 수 있습니다. 규정을 반드시 확인하세요.")
    with st.expander("Q2. 법인차량 구매 시 세금 혜택이 있나요?"):
        st.write("A. 네, 부가가치세 환급 등 다양한 혜택이 존재합니다.")
    with st.expander("Q3. 전기차도 법인차로 등록 가능한가요?"):
        st.write("A. 네, 오히려 친환경 혜택으로 인해 많이 권장되고 있습니다.")
