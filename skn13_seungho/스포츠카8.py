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
menu = st.sidebar.radio("📋 메뉴 선택", ["차량 등록 현황","차량 정보 필터", "뉴스 정보" ,"자주 묻는 질문"])

@st.cache_data
def load_data():
    return pd.read_csv("car_sales_2023_01_to_2025_03.csv")

df = load_data()

if menu == "차량 등록 현황":
    st.title("🚗 수입차 등록 통계 (차종별)")

    @st.cache_data
    def load_car_data():
        df = pd.read_csv("car_reg.csv")
        df = df.set_index("차종별").T  # 전치: 날짜(열) → 인덱스
        df.index.name = "월"
        df.index = pd.to_datetime(df.index, format='%y%m')
        return df

    car_df = load_car_data()

    selected_models = st.multiselect("🚘 차종 선택", car_df.columns.tolist())
    if selected_models:
        df_selected = car_df[selected_models]

        # 👉 등록수 기준으로 10000대 이상/미만 분리
        high_volume = [model for model in selected_models if df_selected[model].max() >= 5000]
        low_volume = [model for model in selected_models if df_selected[model].max() < 5000]

        st.subheader("📈 등록대수 5,000대 이상 모델")
        if high_volume:
            st.line_chart(df_selected[high_volume])
        else:
            st.info("5,000대 이상 등록된 모델이 없습니다.")

        st.subheader("📉 등록대수 5,000대 미만 모델")
        if low_volume:
            st.line_chart(df_selected[low_volume])
        else:
            st.info("5,000대 미만 등록된 모델이 없습니다.")


        st.line_chart(df_selected)

        # 최근 12개월 평균
        df_recent = df_selected[-24:].copy()
        df_2023 = df_recent[df_recent.index.year == 2023].mean()
        df_2024 = df_recent[df_recent.index.year == 2024].mean()

        st.write("📊 평균 등록 수 (최근 12개월)")
        for model in selected_models:
            col1, col2, col3 = st.columns(3)
            col1.metric(f"🚘 {model} - 2023 평균", f"{df_2023[model]:.0f}대")
            col2.metric(f"🚘 {model} - 2024 평균", f"{df_2024[model]:.0f}대")
            diff = df_2024[model] - df_2023[model]
            rate = (diff / df_2023[model]) * 100 if df_2023[model] != 0 else 0
            col3.metric("📈 전년 대비 변화", f"{diff:+.0f}대", f"{rate:+.1f}%")
    else:
        st.info("비교할 차종을 선택해주세요.")


elif menu == "차량 정보 필터":
    st.title("🚘 수입차 판매 데이터 비교 (연도별/월별 시각화)")

    available_years = sorted(df["년도"].unique())
    selected_years = st.multiselect("📆 연도 선택", available_years, default=available_years)

    car_models = df['자동차 모델'].unique()
    selected_models = st.multiselect("🚘 모델 선택", car_models)

    excluded = ['년도', '월', '자동차 모델']
    candidate_metrics = [col for col in df.columns if col not in excluded]

    selected_metrics = st.multiselect("📊 비교 항목 선택", candidate_metrics)

    if selected_models and selected_metrics and selected_years:
        filtered_df = df[
            (df['자동차 모델'].isin(selected_models)) &
            (df['년도'].isin(selected_years))
        ].copy()

        if '전월대비_증감' in filtered_df.columns:
            filtered_df['전월대비_증감'] = filtered_df['전월대비_증감'].astype(str)
            filtered_df['전월대비_증감'] = filtered_df['전월대비_증감'].str.extract(r'([+-]?\d+)')[0]
            filtered_df['전월대비_증감'] = pd.to_numeric(filtered_df['전월대비_증감'], errors='coerce')

        for metric in selected_metrics:
            fig = px.line(
                filtered_df,
                x="월",
                y=metric,
                color="자동차 모델",
                line_dash="년도",
                markers=True,
                title=f"{metric} 월별 추이 (연도별 라인 구분)",
            )

            if metric == "전월대비_증감":
                fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='gray')
                fig.update_layout(yaxis_range=[
                    filtered_df[metric].min() - 10,
                    filtered_df[metric].max() + 10
                ])

            fig.update_layout(
                xaxis=dict(tickmode='linear', tick0=1, dtick=1),
                legend_title_text="자동차 모델",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig)
    else:
        st.info("연도, 모델, 비교 항목을 모두 선택해주세요.")

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