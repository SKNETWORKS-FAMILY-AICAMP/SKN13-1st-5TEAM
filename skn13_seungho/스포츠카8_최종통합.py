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
menu = st.sidebar.radio("📋 메뉴 선택", ["차량 등록 현황", "차량 정보 필터", "뉴스 정보", "자주 묻는 질문"])

@st.cache_data
def load_data():
    df = pd.read_csv("car_sales_2023_01_to_2025_03.csv")
    df = df.drop_duplicates(subset=["자동차 모델", "년도", "월"])  # ✅ 중복 제거 적용
    return df

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

        # 👉 등록수 기준으로 5000대 이상/미만 분리
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

    QUERY = st.text_input("검색어를 입력하세요", value="법인차 제도")
    FILE_PATH = f"news_data/{QUERY}_news.csv"
    os.makedirs("news_data", exist_ok=True)

    def parse_date(text):
        if '일 전' in text:
            return datetime.now() - timedelta(days=int(text.replace('일 전', '').strip()))
        elif '시간 전' in text:
            return datetime.now()
        elif '.' in text:
            try:
                return datetime.strptime(text.strip(), "%Y.%m.%d.")
            except:
                return None
        return None

    def crawl_news(query, pages=1):
        data = []
        for page in range(1, pages + 1):
            start = (page - 1) * 10 + 1
            url = f'https://search.naver.com/search.naver?where=news&query={query}&start={start}'
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            articles = soup.select('div.news_wrap.api_ani_send')

            for article in articles:
                title_tag = article.select_one('a.news_tit')
                if not title_tag:
                    continue
                title = title_tag['title']
                link = title_tag['href']
                press_tag = article.select_one('a.info.press')
                press = press_tag.text.strip() if press_tag else 'Unknown'
                date_tag = article.select('span.info')[-1]
                raw_date = date_tag.text.strip() if date_tag else ''
                parsed = parse_date(raw_date)
                date = parsed.strftime('%Y-%m-%d') if parsed else datetime.today().strftime('%Y-%m-%d')
                summary_tag = article.select_one('div.dsc_wrap')
                summary = summary_tag.text.strip() if summary_tag else ''
                data.append({'title': title, 'press': press, 'date': date, 'summary': summary, 'url': link})
        return pd.DataFrame(data)

    def save_news(df_new):
        if os.path.exists(FILE_PATH):
            df_old = pd.read_csv(FILE_PATH)
            df_all = pd.concat([df_old, df_new]).drop_duplicates(subset=['url'])
        else:
            df_all = df_new
        df_all.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')
        return df_all

    def show_news_paginated(df):
        st.subheader("📰 뉴스 제목 및 요약 보기 (페이지별)")
        def truncate(text, limit=100):
            return text if len(text) <= limit else text[:limit] + "..."

        page_size = 10
        total_pages = (len(df) - 1) // page_size + 1
        page = st.number_input("페이지 선택", min_value=1, max_value=total_pages, step=1)
        start = (page - 1) * page_size
        end = start + page_size

        for i, row in df.iloc[start:end].iterrows():
            st.markdown(f"### 🔗 [{row['title']}]({row['url']})")
            st.write(f"📝 요약: {truncate(row['summary'], 100)}")
            st.markdown("---")

    pages = st.number_input("크롤링할 뉴스 페이지 수 입력 (10개 단위)", min_value=1, max_value=10, step=1)

    if st.button("최신 뉴스 크롤링하기"):
        df_today = crawl_news(QUERY, pages)
        df_all = save_news(df_today)
        st.success(f"{len(df_today)}건 수집 완료! 전체 {len(df_all)}건 저장됨.")
    elif os.path.exists(FILE_PATH):
        df_all = pd.read_csv(FILE_PATH)
    else:
        st.warning("저장된 뉴스 데이터가 없습니다. 먼저 크롤링을 실행하세요.")
        df_all = pd.DataFrame()

    if not df_all.empty:
        st.subheader("최근 수집된 뉴스 미리보기")
        st.dataframe(df_all[['date', 'title', 'press', 'summary']])

        show_news_paginated(df_all)
    else:
        st.warning("뉴스 데이터가 존재하지 않습니다.")

elif menu == "자주 묻는 질문":
    st.title("'연두색 번호판' 정책 관련 자주 묻는 질문")
    st.markdown("""
                고가 법인차량 대상 연두색 번호판 도입 정책관련, 문의 내용을 정리했습니다.
                """)
    
    # FAQ 섹션
    with st.expander("Q1. 연두색 번호판은 어떤 차량에 부착되나요??"):
        st.markdown("""
                    **A:** 8000만원 이상의 법인 차량이 주요 대상이며, 
                    1년 미만의 단기렌트 차량은 제외 됩니다.
                    """)
    
    with st.expander("Q2. 법인차량에 연두색 번호판을 도입한 목적은 무엇인가요?"):
        st.markdown("""
                    **A:** 고가의 수입차를 법인 명의로 등록 후 가족이나 개인 용도로 사용하는 편법이 많아지면서,  
                    업무 비용처리에 의한 탈세 및 과세 형평성 문제를 막기 위해 제도를 도입하였습니다.  
                    """)
    
    with st.expander("Q3. 법인차로 등록할 때 취득가를 낮춰서 신고하면 어떻게 되나요?"):
        st.markdown("""
                    **A:** 의도적으로 취득가를 낮춰 신고하면 세무조사 대상이 되며,  
                    실제보다 낮은 가격으로 신고했을 경우 가산세 등 불이익을 받을 수 있습니다.  
                    """)
    
    with st.expander("Q4. 연두색 번호판을 단 법인차량을 사적으로 사용할 경우 어떻게 되나요?"):
        st.markdown("""
                    **A:** 사적 사용이 적발되면 법인세 관련 불이익과 더불어 세금 추징 및 과태료가 부과될 수 있습니다.  
                    정부는 운행기록부 점검을 통해 단속할 계획입니다.  
                    """)
    
    with st.expander("Q5. 정책 시행 이후 어떤 변화가 있었나요?"):
        st.markdown("""
                    **A:** 2024년 정책 시행 이후 고가 법인차의 등록률이 감소했으며,  
                    일부 브랜드는 전년 대비 30~40% 등록 감소를 보였습니다.
                    """)
    
    with st.expander("Q6. 연두색 번호판을 신고하면 포상금이 있나요?"):
        st.markdown("""
                    **A:** 네. 국기법 제84조 제2항에 따라 사적 이용 적발 시 일정 기준에 따라 **포상금**이 지급될 수 있습니다.  
                    다만, 금액은 관할 지자체 및 신고 상황에 따라 다를 수 있습니다.
                    """)

# 마무리 문구
    st.divider()
    st.info("추가적인 문의사항은 개인적으로 요청하시면 추후에 답변드리도록 하겠습니다. 감사합니다.")