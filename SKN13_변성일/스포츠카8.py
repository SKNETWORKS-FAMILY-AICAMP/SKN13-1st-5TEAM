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



# 한글 폰트 설정
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# Streamlit 앱 구성
st.set_page_config(page_title="법인차량 대시보드", layout="wide")
menu = st.sidebar.radio("📋 메뉴 선택", ["차량 등록 현황","차량 정보 필터", "뉴스 정보", "트위터 반응", "유튜브 반응" ,"자주 묻는 질문"])

@st.cache_data
def load_data():
    return pd.read_csv("car_sales_2023_01_to_2025_03.csv")

df = load_data()

###############################################################################################################

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

if menu == "차량 등록 현황":
    st.title("🚗 수입 법인차량 등록 통계 (차종별)")

    # ✅ MySQL에서 데이터 불러오기 함수
    @st.cache_data
    def load_car_data_from_mysql():
        db_user = "runnnn"
        db_password = "1111"
        db_host = "localhost"
        db_port = "3306"
        db_name = "car_reg"
        table_name = "car_reg"

        engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, con=engine)
        df = df.set_index("차종별").T
        df.index.name = "월"
        df.index = pd.to_datetime(df.index, format="%y%m")
        return df

    car_df = load_car_data_from_mysql()

    selected_models = st.multiselect("🚘 차종 선택", car_df.columns.tolist())
    if selected_models:
        df_selected = car_df[selected_models]

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

        # 전체 차트
        st.line_chart(df_selected)

        # 최근 12개월 평균 비교
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


###############################################################################################################

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

###############################################################################################################

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
        
###############################################################################################################

elif menu == "트위터 반응":
    st.title("🚗 트위터 반응 수집 결과 보기")
    
    csv_file = "tweet_contents.csv"

    # CSV 로드
    @st.cache_data
    def load_data_tw():
        if os.path.exists(csv_file):
            return pd.read_csv(csv_file)
        else:
            return pd.DataFrame(columns=["url", "text"])  # 빈 데이터프레임 반환
    
    df = load_data_tw()
    
    if df.empty:
        st.error("❌ tweet_contents.csv 파일을 찾을 수 없습니다.")
    else:
        st.success("✅ CSV 파일 로딩 완료!")
    
        search_keyword = st.text_input("🔍 키워드로 내용 검색 (예: 법인, 연두색)")
    
        if search_keyword:
            filtered = df[df["text"].str.contains(search_keyword, case=False, na=False)]
    
            if not filtered.empty:
                for _, row in filtered.iterrows():
                    st.markdown(f"**📝 트윗 내용**")
                    st.write(row["text"])
                    st.markdown("---")
            else:
                st.warning("❗ 검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
                
##############################################################################################################

elif menu == "유튜브 반응":
    # CSV 파일 불러오기 (파일명에 괄호가 있으면 오류 가능 → 파일명 변경 권장)
    comments_df = pd.read_csv("comments.csv", header=None)
    comments = comments_df[0].dropna().astype(str)
    
    st.title("🟢 연두색 번호판 관련 유튜브 댓글 분석")
    
    # 총 댓글 수 표시
    st.write(f"총 댓글 수: {len(comments)}개")
    
    # 🔎 키워드 검색
    search_keyword = st.text_input("댓글 내 키워드 검색", "")
    if search_keyword:
        filtered = comments[comments.str.contains(search_keyword, case=False)]
        st.write(f"🔍 '{search_keyword}'가 포함된 댓글 수: {len(filtered)}개")
        st.dataframe(filtered)
    
    # 📊 워드클라우드 생성
    st.subheader("주요 키워드 워드클라우드")
    
    all_text = " ".join(comments.tolist())
    
    # ✅ font_path 제거 → 시스템 기본 폰트 사용
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    
    text = " ".join(comments.tolist())
    wc = WordCloud(font_path=r"C:\Users\erety\sk_13_5_1st_sungil\1st_pj_g5\새 폴더\NanumGothicCoding.ttf", width=800, height=400).generate(text)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    plt.show()
    
    
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)


###############################################################################################################

elif menu == "자주 묻는 질문":
    st.title("❓ 자주 묻는 질문 (FAQ)")

    # MySQL에서 FAQ 데이터 불러오기
    def load_data_from_mysql(host, user, password, database, table_name="faq"):
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT question, answer FROM {table_name}")
            result = cursor.fetchall()
        conn.close()
        return pd.DataFrame(result)

    # Streamlit FAQ 페이지 실행 함수
    def render_faq():
        st.write("아래 질문을 클릭하면 답변을 확인할 수 있어요.")
    
        host = "127.0.0.1"
        user = "runnnn"
        password = "1111"
        database = "FAQ"
        table_name = "faq"
    
        try:
            df = load_data_from_mysql(host, user, password, database, table_name)
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류 발생: {e}")
            return
    
        query = st.text_input("🔍 질문 검색", "")
        if query:
            df = df[df["question"].str.contains(query, case=False, na=False)]
    
        if df.empty:
            st.warning("검색 결과가 없습니다.")
            return
    
        for idx, row in enumerate(df.itertuples(index=False), start=1):
            question = str(row.question).strip()
            
            # ✅ 숫자 앞에 이모지 추가로 강조 + 굵게 처리
            expander_title = f"🔸 **{idx}. {question}**"
            
            with st.expander(expander_title):
                st.write(row.answer)


    # ✅ 여기가 핵심! 메뉴에 진입했을 때 바로 실행
    render_faq()

