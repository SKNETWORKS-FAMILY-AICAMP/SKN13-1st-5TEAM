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
import pymysql
from wordcloud import WordCloud
from sqlalchemy import create_engine
import mysql.connector

# 한글 폰트 설정
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# Streamlit 앱 구성
st.set_page_config(page_title="법인차량 대시보드", layout="wide")
# Streamlit 메뉴 구성
menu = st.sidebar.radio("📋 메뉴 선택", ["차량 등록 현황","차량 정보 필터", "뉴스 정보", "트위터 반응", "유튜브 반응" ,"자주 묻는 질문"])       

###############################################################################################################

if menu == "차량 등록 현황": # 차량 등록 현황 메뉴 구성
    st.title("🚗 수입 법인차량 등록 통계 (차종별)")

    # ✅ MySQL에서 데이터 불러오기 함수
    @st.cache_data
    def load_car_data_from_mysql():
        db_user = "user1"
        db_password = "1111"
        db_host = "localhost"
        db_port = "3306"
        db_name = "car_reg"
        table_name = "car_reg"

        engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
        query = f"SELECT * FROM {table_name}"
        car_reg_df = pd.read_sql(query, con=engine)

        # 전처리
        car_reg_df = car_reg_df.set_index("차종별").T
        car_reg_df.index.name = "월"
        car_reg_df.index = pd.to_datetime(car_reg_df.index, format="%y%m")
        return car_reg_df

    # ✅ 데이터 불러오기
    car_reg_df = load_car_data_from_mysql()

    # ✅ 차종 선택
    selected_models = st.multiselect("🚘 차종 선택", car_reg_df.columns.tolist())

    if selected_models:
        car_reg_df_selected = car_reg_df[selected_models]

        # ✅ 등록 수 기준 분류
        high_volume = [model for model in selected_models if car_reg_df_selected[model].max() >= 5000]
        low_volume = [model for model in selected_models if car_reg_df_selected[model].max() < 5000]

        st.subheader("📈 등록대수 5,000대 이상 모델")
        if high_volume:
            st.line_chart(car_reg_df_selected[high_volume])
        else:
            st.info("5,000대 이상 등록된 모델이 없습니다.")

        st.subheader("📉 등록대수 5,000대 미만 모델")
        if low_volume:
            st.line_chart(car_reg_df_selected[low_volume])
        else:
            st.info("5,000대 미만 등록된 모델이 없습니다.")

        # ✅ 최근 12개월 평균 비교
        car_reg_df_recent = car_reg_df_selected[-24:].copy()
        car_reg_df_2023 = car_reg_df_recent[car_reg_df_recent.index.year == 2023].mean()
        car_reg_df_2024 = car_reg_df_recent[car_reg_df_recent.index.year == 2024].mean()

        st.write("📊 평균 등록 수 (최근 12개월)")
        for model in selected_models:
            col1, col2, col3 = st.columns(3)
            col1.metric(f"🚘 {model} - 2023 평균", f"{car_reg_df_2023[model]:.0f}대")
            col2.metric(f"🚘 {model} - 2024 평균", f"{car_reg_df_2024[model]:.0f}대")
            diff = car_reg_df_2024[model] - car_reg_df_2023[model]
            rate = (diff / car_reg_df_2023[model]) * 100 if car_reg_df_2023[model] != 0 else 0
            col3.metric("📈 전년 대비 변화", f"{diff:+.0f}대", f"{rate:+.1f}%")
    else:
        st.info("비교할 차종을 선택해주세요.")


###############################################################################################################
    
elif menu == "차량 정보 필터": # 차량 정보 필터 메뉴 구성
    st.title("🚘 수입차 판매 데이터 비교 (연도별/월별 시각화)")

    # ✅ MySQL에서 데이터 불러오기 함수
    @st.cache_data
    def load_data():
        conn = pymysql.connect(
            host="localhost",
            user="user1",
            password="1111",
            database="car_sales",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM car_sales")
            result = cursor.fetchall()
        conn.close()

        df = pd.DataFrame(result)
        df = df.drop_duplicates(subset=["자동차 모델", "년도", "월"])
        return df

    # ✅ 데이터 불러오기
    df = load_data()

    # ✅ 필터 영역
    available_years = sorted(df["년도"].unique())
    selected_years = st.multiselect("📆 연도 선택", available_years, default=available_years)

    car_models = df['자동차 모델'].unique()
    selected_models = st.multiselect("🚘 모델 선택", car_models)

    excluded = ['년도', '월', '자동차 모델']
    candidate_metrics = [col for col in df.columns if col not in excluded]
    selected_metrics = st.multiselect("📊 비교 항목 선택", candidate_metrics)

    # ✅ 조건 충족 시 필터링 및 시각화
    if selected_models and selected_metrics and selected_years:
        # ✅ 필터링
        filtered_df = df[
            (df['자동차 모델'].isin(selected_models)) &
            (df['년도'].isin(selected_years))
        ].copy()
    
        # ✅ 전월대비_증감 전처리 (필요 시)
        if '전월대비_증감' in filtered_df.columns:
            filtered_df['전월대비_증감'] = filtered_df['전월대비_증감'].astype(str)
            filtered_df['전월대비_증감'] = filtered_df['전월대비_증감'].str.extract(r'([+-]?\d+)')[0]
            filtered_df['전월대비_증감'] = pd.to_numeric(filtered_df['전월대비_증감'], errors='coerce')
    
        for metric in selected_metrics:
            # ✅ 월별 요약
            month_summary = (
                filtered_df
                .groupby(['년도', '월', '자동차 모델'])[metric]
                .sum()
                .reset_index()
            )
            month_summary[metric] = pd.to_numeric(month_summary[metric], errors="coerce")
            month_summary['월'] = month_summary['월'].astype(str)
    
            # ✅ 1. 월별 판매량 비교 그래프
            fig_month = px.bar(
                month_summary,
                x="월",
                y=metric,
                color="년도",
                barmode="group",
                facet_col="자동차 모델",
                title=f"{metric} 월별 연도 비교 막대그래프"
            )
            fig_month.update_layout(
                xaxis_title="월",
                yaxis_title=metric,
                legend_title_text="년도",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                ),
                plot_bgcolor="#fafafa",
                font=dict(family="Arial", size=14)
            )
            st.plotly_chart(fig_month)
    
            # ✅ 2. 연도별 총합 계산
            total_summary = (
                month_summary
                .groupby(['년도'])[metric]
                .sum()
                .reset_index()
            )
            total_summary[metric] = pd.to_numeric(total_summary[metric], errors='coerce')
            total_summary['년도'] = total_summary['년도'].astype(str)
    
            # ✅ 연도별 색상 설정
            year_color_map = {
                '2023': '#4C78A8',
                '2024': '#9ECAE9',
            }
    
            # ✅ 총합 그래프
            fig_total = px.bar(
                total_summary,
                x="년도",
                y=metric,
                text=total_summary[metric].apply(lambda x: f"{int(x):,}대"),
                title=f"📊 {metric} 총합 비교 (선택된 모델 기준)",
                color="년도",
                color_discrete_map=year_color_map,
            )
            fig_total.update_traces(
                textposition='outside',
                cliponaxis=False,
                marker_line_width=1.5,
                marker_line_color='gray',
                width=0.5,
            )
            fig_total.update_layout(
                yaxis_title=f"{metric} (대)",
                xaxis_title="연도",
                title_font_size=20,
                font=dict(family="Arial", size=14),
                uniformtext_minsize=12,
                uniformtext_mode='hide',
                bargap=0.3,
                showlegend=False,
                height=400,
                margin=dict(t=60, b=40, l=60, r=40),
                plot_bgcolor="#fafafa"
            )
            st.plotly_chart(fig_total)
    
    else:
        st.info("연도, 모델, 비교 항목을 모두 선택해주세요.")


###############################################################################################################

elif menu == "뉴스 정보": # 뉴스 정보 메뉴 구성
    st.title("📰 법인 관련 뉴스")
    st.info("이 섹션은 뉴스 크롤링 기능을 제공합니다. 다른 기능은 기존과 동일합니다.")

    QUERY = st.text_input("검색어를 입력하세요", value="법인차 제도") # 기본값 법인차 도도
    FILE_PATH = f"news_data/{QUERY}_news.csv"
    os.makedirs("news_data", exist_ok=True) # 폴더 저

    def parse_date(text): # 실제 날짜 객체로 변
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

    def crawl_news(query, pages=1): # 크롤링: 제목 / 링크 / 언론사 / 날짜 / 요약 / URL을 가져옴
        data = []
        for page in range(1, pages + 1): # 페이지당 10개
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

    def save_news(df_new, query): # 뉴스 저장 , query 어떤 검색어로 저장했는지
        # 1️⃣ 기존 CSV 병합
        file_path = f"news_data/{query}_news.csv"
        if os.path.exists(file_path):
            df_old = pd.read_csv(file_path)
            df_all = pd.concat([df_old, df_new]).drop_duplicates(subset=['url'])
        else:
            df_all = df_new
    
        # 2️⃣ 검색어 컬럼 추가
        df_all["query"] = query
    
        # 3️⃣ CSV 저장
        df_all.to_csv(file_path, index=False, encoding='utf-8-sig')
    
        # 4️⃣ MySQL 저장
        try:
            engine = create_engine("mysql+pymysql://runnnn:1111@localhost:3306/news_db")
            df_new["query"] = query  # ✅ 새로 수집된 뉴스에도 검색어 추가
            df_new.to_sql(name="news_data", con=engine, if_exists="append", index=False)
        except Exception as e:
            st.error(f"MySQL 저장 실패: {e}")
    
        return df_all

    def show_news_paginated(df): # 뉴스가 많을 떄 10개씩 1페이지 별로 나눠 출력
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
        df_all = save_news(df_today, QUERY)  # ✅ 두 번째 인자 추가
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
        
###############################################################################################################

elif menu == "트위터 반응":
    st.title("🚗 트위터 반응 수집 결과 보기")

    # ✅ MySQL에서 트위터 데이터 불러오기
    @st.cache_data
    def load_data_tw():
        db_user = "user1"
        db_password = "1111"
        db_host = "localhost"
        db_port = "3306"
        db_name = "tweet_contents"
        table_name = "tweet_contents"

        engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
        query = f"SELECT url, text FROM {table_name}"
        df = pd.read_sql(query, con=engine)
        return df

    df_tw = load_data_tw()

    if df_tw.empty:
        st.error("❌ MySQL에서 트위터 데이터를 불러오지 못했습니다.")
    else:
        st.success("✅ 트위터 데이터 로딩 완료!")

        search_keyword = st.text_input("🔍 키워드로 내용 검색 (예: 법인, 연두색)")

        if search_keyword:
            filtered = df_tw[df_tw["text"].str.contains(search_keyword, case=False, na=False)]

            if not filtered.empty:
                for _, row in filtered.iterrows():
                    st.markdown("**📝 트윗 내용**")
                    st.write(row["text"])
                    st.markdown("---")
            else:
                st.warning("❗ 검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
                
##############################################################################################################

elif menu == "유튜브 반응":
    st.title("🟢 연두색 번호판 관련 유튜브 댓글 분석")

    # ✅ MySQL에서 유튜브 댓글 불러오기
    @st.cache_data
    def load_data_youtube():
        db_user = "user1"
        db_password = "1111"
        db_host = "localhost"
        db_port = "3306"
        db_name = "youtube"
        table_name = "youtube"

        # SQLAlchemy 연결
        engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

        # ✅ 유튜브 댓글의 컬럼명이 숫자(0)이므로 역따옴표로 감싸고, 이름 변경 
        query = f"SELECT `0` AS comment FROM {table_name}"
        df = pd.read_sql(query, con=engine)
        return df

    # ✅ 댓글 데이터 불러오기
    df_youtube = load_data_youtube()
    comments = df_youtube["comment"].dropna().astype(str)

    # ✅ 총 댓글 수 표시
    st.write(f"총 댓글 수: {len(comments)}개")

    # 🔍 키워드 검색
    search_keyword = st.text_input("댓글 내 키워드 검색", "")
    if search_keyword:
        filtered = comments[comments.str.contains(search_keyword, case=False)]
        st.write(f"🔍 '{search_keyword}'가 포함된 댓글 수: {len(filtered)}개")
        st.dataframe(filtered)

    # 📊 워드클라우드 생성
    st.subheader("📊 주요 키워드 워드클라우드")

    all_text = " ".join(comments.tolist())

    # ✅ 폰트 경로 지정 (윈도우 한글 폰트)
    font_path = r"C:\Users\erety\sk_13_5_1st_sungil\1st_pj_g5\새 폴더\NanumGothicCoding.ttf"

    wc = WordCloud(
        font_path=font_path,
        width=800,
        height=400,
        background_color="white"
    ).generate(all_text)

    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)



###############################################################################################################

elif menu == "자주 묻는 질문":

    st.title("'연두색 번호판' 자주 묻는 질문")
    st.markdown("고가 법인차량 대상 연두색 번호판 도입 정책 관련 주요 문의와 답변을 정리했습니다.")
    
    with st.expander("💬 Q1: 적용 차량"):
        st.markdown("""
        <div style='font-size:22px; font-weight:700; margin-bottom:10px; color:#222;'>💬 Q1. 연두색 번호판은 어떤 차량에 부착되나요?</div>
    
        **A.** 연두색 번호판은 **출고가 8,000만 원 이상의 법인 명의 승용차량**에 부착됩니다.  
        이는 법인차량의 업무용·사적용도를 구분하고, **세금 혜택 오남용을 방지하기 위한 제도적 장치**입니다.
    
        ---
    
        **📌 부착 대상 요약**
        - 법인 또는 단체 명의로 등록된 차량
        - 차량 출고가 기준 **8,000만 원 이상**
        - **2024년 1월 1일 이후** 신규 등록 차량
    
        **🔸 예외 차량**
        - **1년 미만 단기 렌트 차량**
        - **2023년 12월 31일 이전 등록된 기존 차량**
        - 공공기관용 관용차량, 일부 의전 차량
        """, unsafe_allow_html=True)
    
    
    with st.expander("💬 Q2: 정책 도입 목적"):
      st.markdown("""
        <div style='font-size:22px; font-weight:700; margin-bottom:10px; color:#222;'>💬 Q2. 법인차량에 연두색 번호판을 도입한 목적은 무엇인가요?</div>
                  
        ✅ **A:** 연두색 번호판 제도는 **법인차량의 사적 사용을 방지하고, 과세 형평성을 회복하기 위해** 도입되었습니다.  
        이 제도는 단순한 ‘색상 구분’이 아니라, **세금 정의 실현을 위한 제도적 장치**입니다.
    
        ---
        🔹 **배경 요약**
        - 억대 고가 수입차를 법인 명의로 등록한 후  
          **가족이나 대표자 개인 용도로 사용하는 사례**가 지속적으로 증가
        - 차량 구매 비용과 유지비를 **업무 비용으로 처리**하여  
          **세금 부담을 부당하게 줄이는 '편법 소비'**가 사회적 이슈로 대두됨
    
        ---
        🔸 **도입 목적**
        - 업무용 차량과 사적 사용 차량의 **구분 명확화**
        - 법인차량의 **세제 혜택 오남용 방지**
        - **과세 형평성 제고** 및 고소득층에 대한 탈세 억제
        """, unsafe_allow_html=True)
    
    
    with st.expander("💬 Q3: 허위 신고 시 처벌"):
      st.markdown("""
        <div style='font-size:22px; font-weight:700; margin-bottom:10px; color:#222;'>💬 Q3. 법인차로 등록할 때 취득가를 낮춰서 신고하면 어떻게 되나요?</div>
        
        ✅ **A:** **의도적으로 차량 취득가를 낮춰 신고하는 행위는 '다운계약'에 해당하며**,  
        조세포탈로 간주되어 **세무조사 및 가산세 부과** 대상이 됩니다.
    
        ---
        🔹 **다운계약이란?**
        - 실제 거래 가격보다 **낮은 가격으로 계약서를 작성**하여  
          취득세, 등록세, 부가세 등 **세금 부담을 줄이는 행위**
    
        ---
        ❌ **이렇게 되면?**
        - 세무당국에 적발 시:
            - **세금 추징** (부족분 + 연체 이자)
            - **가산세 부과** (최대 40%까지)
            - **법인 회계·지출 항목 전수조사 가능성**
    
        ---
        📌 **주의사항**
        - 연두색 번호판 제도 시행 이후,  
          **출고가를 의도적으로 낮춰 신고하는 사례가 집중 단속 대상**입니다.
        - **실제 거래가격과 취득가가 상이할 경우**, 국세청이 제조사 출고가 기준으로 과세를 재산정할 수 있습니다.
        """, unsafe_allow_html=True)
    
    
    with st.expander("💬 Q4: 사적 사용 시 처벌"):
      st.markdown("""
        <div style='font-size:22px; font-weight:700; margin-bottom:10px; color:#222;'>💬 Q4. 연두색 번호판을 단 법인차량을 사적으로 사용할 경우 어떻게 되나요?</div>
      
        ✅ **A:** 연두색 번호판이 부착된 **법인차량을 사적으로 사용하는 것은 명백한 세법 위반**에 해당하며,  
        **법인세법·소득세법상 세금 추징 및 가산세, 과태료 등의 처벌 대상이 됩니다.**
    
        ---
        🔹 **사적 사용으로 간주되는 경우**
        - 주말/야간에 가족이나 지인이 차량을 이용한 흔적
        - 골프장, 리조트, 휴양지 등 **비업무 목적지 방문 내역**
        - 운행기록부 미작성 또는 조작
    
        ---
        ❗ **적발 시 불이익**
        - **업무용 차량 비용 인정 배제** → 법인세 추가 납부
        - **부가가치세 환급 취소**
        - **가산세 및 연체 이자 부과**
        - 반복 적발 시 **세무조사 대상**
    
        ---
        📌 **정부 단속 방식**
        - **운행기록부 점검**, 유류비·보험 내역 크로스체크
        - 연두색 번호판 차량은 **민원 신고 접수 시 바로 조사 가능**
        """, unsafe_allow_html=True)
    
    with st.expander("💬 Q5: 정책 시행 후 변화"):
      st.markdown("""
        <div style='font-size:22px; font-weight:700; margin-bottom:10px; color:#222;'>💬 Q5. 정책 시행 이후 어떤 변화가 있었나요?</div>
      
        ✅ **A:** 2024년 정책 시행 이후 고가 법인차의 등록률이 크게 감소했습니다.  
        일부 브랜드는 전년 대비 40~90% 가까운 등록 감소를 기록했습니다.
    
        ---
        📉 **시장 전체 영향**
        - 수입차 전체 등록량 약 **-11.5% 감소**  
        - 고급 외제차의 **법인 구매 위축 → 개인 명의 전환 증가**
        - 일부 소비자는 **국산 고급차(G90 등)로 대체**
        """, unsafe_allow_html=True)
    
    with st.expander("💬 Q6: 업무 외 용도 신고 시 포상금 "):
      st.markdown("""
        <div style='font-size:22px; font-weight:700; margin-bottom:10px; color:#222;'>💬 Q6. 연두색 번호판 차량의 용도 외 사용을 신고하면 포상금이 있나요?</div>
      
        ✅ **A:** 네, 있습니다.  
        「국가공무원법 제84조 제2항」 및 **각 지방자치단체의 신고 포상 조례**에 따라  
        **불법 사용된 법인차량을 신고할 경우 포상금이 지급될 수 있습니다.**
    
        ---
        🔹 **포상금 지급 조건**
        - 연두색 번호판 부착 대상 차량이 **일반 번호판을 부착한 채 운행하거나**,  
        - **사적으로 운행되는 정황**을 영상 또는 사진 등으로 신고한 경우
        - **실제 세금 추징**으로 이어질 경우에 한해 지급
    
        ---
        💰 **포상금 금액**
        - **일정 비율(최대 수백만 원 한도)**로 보상  
        - 금액 및 지급 방식은 **지자체마다 상이**  
        - 일반적으로 **공익제보 보상금 또는 탈루세액 비율 기준**
    
        ---
        📌 **주의사항**
        - 익명 신고는 접수되나, **증거자료가 명확해야 인정**됨  
        - 포상금은 **사전 확정이 아닌, 사후 심사 후 지급** 방식
        """, unsafe_allow_html=True)
    
    
    with st.expander("💬 Q7: 연두색 번호판 미부착시 처벌 "):
      st.markdown("""
        <div style='font-size:22px; font-weight:700; margin-bottom:10px; color:#222;'>💬 Q7. 법인차량 연두색 번호판을 달지 않으면 과태료가 부과되나요?</div>
      
        ✅ **A:** 네, 부과됩니다.
    
        2024년 1월부터 시행된 **연두색 번호판 제도**는  
        출고가 **8천만 원 이상의 법인 승용차량**에 **연두색 번호판 부착을 의무화**하고 있습니다.
    
        ---
        🔹 **관련 법령**  
        - 「자동차관리법 시행규칙 제11조」  
        - 「자동차관리법 제48조 제1항」
    
        ---
        ❗ **위반 시 제재**  
        - 연두색 번호판을 부착하지 않으면 → **등록번호 미부착 간주**  
        - ▶️ **100만 원 이하 과태료 부과**
    
        ---
        📌 **추가 유의사항**  
        - 부착 대상 차량이 일반 번호판을 부착하고 운행할 경우,  
          **사적 이용 신고 시 국세청 세무조사 가능성** 있음  
        - 국토교통부는 **연두색 번호판 대상 차량 정보를 국세청과 공유** 중
        """, unsafe_allow_html=True)

    # 마무리 문구
    st.divider()
    st.info("📬 추가적인 문의사항은 개인적으로 요청해주시면 답변드리겠습니다. 감사합니다.")

