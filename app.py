import re  # 문자열 패턴 정리(정규표현식)를 위한 모듈
import pandas as pd  # 표 데이터를 다루기 위한 라이브러리
import requests  # 웹페이지 HTML을 가져오기 위한 라이브러리
import streamlit as st  # 웹 앱 화면을 만들기 위한 라이브러리
from bs4 import BeautifulSoup  # HTML 태그를 파싱하기 위한 라이브러리


WIKIPEDIA_URL = "https://ko.wikipedia.org/wiki/대한민국의_영화_흥행_기록"
HEADERS = {
    # 위키백과 요청 시 수업 실습용임을 밝히는 User-Agent 설정
    "User-Agent": "PythonClassPracticeBot/1.0 (Freshman Non-CS Course Exercise)"
}


def fetch_wikipedia_html(url: str, headers: dict, timeout: int = 10) -> str:
    """위키백과 문서의 HTML 문자열을 가져온다."""
    try:
        # 연결 시간 초과와 읽기 시간 초과를 함께 지정해 요청
        response = requests.get(url, headers=headers, timeout=(timeout, timeout))
        # 4xx, 5xx 같은 HTTP 오류 상태 코드면 예외 발생
        response.raise_for_status()
        # 한글 깨짐 방지를 위해 인코딩 지정
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("요청 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("인터넷 또는 위키백과 서버에 연결할 수 없습니다.") from exc
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "알 수 없음"
        raise RuntimeError(f"HTTP 오류가 발생했습니다. (상태 코드: {status_code})") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"웹페이지를 불러오는 중 오류가 발생했습니다: {exc}") from exc


def find_target_table(html: str):
    """wikitable 중 첫 줄에 '관객수'와 '감독'이 모두 있는 첫 번째 표를 찾는다."""
    soup = BeautifulSoup(html, "html.parser")
    # class 속성에 'wikitable'이 포함된 모든 table 태그 탐색
    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        # 첫 줄의 제목 칸(th)과 일반 칸(td) 텍스트를 합쳐 확인
        first_row_cells = rows[0].find_all(["th", "td"])
        first_row_text = " ".join(cell.get_text(" ", strip=True) for cell in first_row_cells)

        if "관객수" in first_row_text and "감독" in first_row_text:
            return table

    # 조건에 맞는 표가 없는 경우 명시적으로 오류 발생
    raise ValueError("첫 줄에 '관객수'와 '감독'이 모두 포함된 wikitable 표를 찾지 못했습니다.")


def parse_table_to_dataframe(table) -> pd.DataFrame:
    """각주(sup)를 제거하고 표의 각 행을 읽어 DataFrame으로 변환한다."""
    # 원본 HTML 구조를 건드리지 않기 위해 복사본 생성
    table_copy = BeautifulSoup(str(table), "html.parser")

    # 각주 번호가 들어가는 sup 태그 모두 제거
    for sup_tag in table_copy.find_all("sup"):
        sup_tag.decompose()

    rows = table_copy.find_all("tr")
    if len(rows) < 2:
        raise ValueError("표에 데이터 행이 충분하지 않습니다.")

    # 첫 줄(th)을 열 이름으로 추출
    headers = [th.get_text(" ", strip=True) for th in rows[0].find_all("th")]
    if not headers:
        # 예외적으로 첫 줄이 td로만 구성된 경우 대비
        headers = [td.get_text(" ", strip=True) for td in rows[0].find_all("td")]

    records = []
    # 두 번째 줄부터 각 영화 행(tr)을 순회
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        values = [cell.get_text(" ", strip=True) for cell in cells]

        # 열 개수가 헤더와 다를 경우 길이를 맞춰 안전하게 처리
        if len(values) < len(headers):
            values.extend([""] * (len(headers) - len(values)))
        elif len(values) > len(headers):
            values = values[: len(headers)]

        records.append(dict(zip(headers, values)))

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("표에서 영화 데이터를 추출하지 못했습니다.")

    return df


def find_column_by_keyword(df: pd.DataFrame, keyword: str):
    """열 이름에 특정 키워드가 포함된 첫 번째 열 이름을 찾는다."""
    for col in df.columns:
        if keyword in str(col):
            return col
    return None


def clean_movie_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """제목 정제, 관객수 숫자 변환, 개봉연도 및 개봉월 생성을 수행한다."""
    cleaned = df.copy()

    title_col = find_column_by_keyword(cleaned, "제목") or find_column_by_keyword(cleaned, "영화")
    audience_col = find_column_by_keyword(cleaned, "관객수")
    release_col = find_column_by_keyword(cleaned, "개봉")

    if audience_col is None:
        raise ValueError("표에서 '관객수' 열을 찾을 수 없습니다.")

    # 1. 제목에서 《 와 》 기호 제거
    if title_col is not None:
        cleaned[title_col] = (
            cleaned[title_col]
            .astype(str)
            .str.replace("《", "", regex=False)
            .str.replace("》", "", regex=False)
            .str.strip()
        )

    # 2. 관객수에서 쉼표 및 숫자가 아닌 문자를 제거한 뒤 숫자로 변환
    cleaned["관객수_숫자"] = (
        cleaned[audience_col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.extract(r"(\d+)", expand=False)
    )
    cleaned["관객수_숫자"] = pd.to_numeric(cleaned["관객수_숫자"], errors="coerce")
    cleaned = cleaned.dropna(subset=["관객수_숫자"]).copy()
    cleaned["관객수_숫자"] = cleaned["관객수_숫자"].astype(int)
    cleaned[audience_col] = cleaned["관객수_숫자"]

    # 3. 개봉일 문자열에서 개봉연도와 개봉월 추출
    if release_col is not None:
        release_str = cleaned[release_col].astype(str)
        # 'YYYY년 M월 D일' 또는 'YYYY-MM-DD' 등에서 연도와 월 추출
        year_series = release_str.str.extract(r"(\d{4})\s*(?:년|-|\.|/)", expand=False)
        month_series = release_str.str.extract(
            r"(?:\d{4}\s*(?:년|-|\.|/)\s*|^\s*)(\d{1,2})\s*(?:월|-|\.|/)",
            expand=False,
        )

        # 날짜 파싱이 일부 행에서 실패할 경우 pandas datetime 변환으로 보완
        parsed_dates = pd.to_datetime(release_str, errors="coerce")
        year_series = year_series.fillna(parsed_dates.dt.year.astype("Int64").astype(str))
        month_series = month_series.fillna(parsed_dates.dt.month.astype("Int64").astype(str))

        cleaned["개봉연도"] = pd.to_numeric(year_series, errors="coerce").astype("Int64")
        cleaned["개봉월"] = pd.to_numeric(month_series, errors="coerce").astype("Int64")
    else:
        cleaned["개봉연도"] = pd.Series([pd.NA] * len(cleaned), dtype="Int64")
        cleaned["개봉월"] = pd.Series([pd.NA] * len(cleaned), dtype="Int64")

    # 보조 계산 열 제거 후 깔끔한 열 순서 유지
    cleaned = cleaned.drop(columns=["관객수_숫자"])
    return cleaned


def render_metrics(df: pd.DataFrame):
    """천만 영화 수, 역대 1위 영화, 1위 관객수 지표를 화면에 표시한다."""
    title_col = find_column_by_keyword(df, "제목") or find_column_by_keyword(df, "영화") or df.columns[0]
    audience_col = find_column_by_keyword(df, "관객수")

    # 관객수 기준 내림차순 정렬하여 1위 영화 확인
    sorted_df = df.sort_values(by=audience_col, ascending=False).reset_index(drop=True)
    top_movie_title = str(sorted_df.loc[0, title_col])
    top_audience_count = int(sorted_df.loc[0, audience_col])
    ten_million_count = int((df[audience_col] >= 10_000_000).sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("천만 영화 수", f"{ten_million_count}편")
    col2.metric("역대 1위", top_movie_title)
    col3.metric("1위 관객수", f"{top_audience_count:,}명")


def render_charts(df: pd.DataFrame):
    """관객수 상위 10편 가로 막대 차트와 개봉 연도별 편수 막대 차트를 그린다."""
    title_col = find_column_by_keyword(df, "제목") or find_column_by_keyword(df, "영화") or df.columns[0]
    audience_col = find_column_by_keyword(df, "관객수")

    st.subheader("관객수 상위 10편 (가로 막대 차트)")
    # 상위 10편 추출 후 가로 막대 차트에서 위에서부터 1위가 보이도록 순서 조정
    top10_df = (
        df.sort_values(by=audience_col, ascending=False)
        .head(10)
        .sort_values(by=audience_col, ascending=True)
        .set_index(title_col)
    )
    st.bar_chart(top10_df[audience_col], horizontal=True)

    st.subheader("개봉 연도별 편수 (막대 차트)")
    year_valid = df.dropna(subset=["개봉연도"])
    if not year_valid.empty:
        year_counts = (
            year_valid.groupby("개봉연도")
            .size()
            .sort_index()
        )
        # 연도 축이 소수점(예: 2,014.0)으로 보이지 않도록 문자열 인덱스로 변환
        year_counts.index = year_counts.index.astype(str)
        st.bar_chart(year_counts)
    else:
        st.info("개봉 연도 정보를 집계할 수 없습니다.")


def main():
    """Streamlit 앱 전체 실행 흐름을 관리한다."""
    st.title("대한민국 천만 관객 한국 영화 흥행 기록 분석")
    st.write("위키백과 '대한민국의 영화 흥행 기록' 문서에서 표 데이터를 가져와 분석합니다.")

    # 버튼 클릭 시 데이터를 수집하고 세션 상태에 저장
    if st.button("데이터 가져오기 및 분석"):
        try:
            with st.spinner("위키백과에서 표 데이터를 가져오는 중..."):
                html = fetch_wikipedia_html(WIKIPEDIA_URL, HEADERS, timeout=10)
                target_table = find_target_table(html)
                raw_df = parse_table_to_dataframe(target_table)
                cleaned_df = clean_movie_dataframe(raw_df)

            st.session_state["movie_df"] = cleaned_df
        except RuntimeError as exc:
            st.error(str(exc))
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"예상치 못한 오류가 발생했습니다: {exc}")

    # 이미 수집된 데이터가 있으면 지표, 표, 차트를 출력
    if "movie_df" in st.session_state:
        result_df = st.session_state["movie_df"]

        st.divider()
        render_metrics(result_df)

        st.subheader("정제된 영화 목록")
        # DataFrame의 기본 인덱스가 화면에 보이지 않도록 hide_index=True 설정
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        st.divider()
        render_charts(result_df)


if __name__ == "__main__":
    main()