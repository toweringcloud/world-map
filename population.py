import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# 타이틀
st.set_page_config(layout="wide")
st.title("World Population Map")


# CSV 데이터 로드
@st.cache_data
def load_population_data():
    df = pd.read_csv("data/population.csv")  # 인구 데이터 로드
    df = df.sort_values(by="population", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1  # 순위 추가
    return df


population_df = load_population_data()


# GeoPandas 세계 지도 데이터 로드
# https://www.naturalearthdata.com/downloads/110m-cultural-vectors
@st.cache_data
def load_world_data():
    world = gpd.read_file("maps/110m_cultural/ne_110m_admin_0_countries.shp")
    return world


world = load_world_data()
print(world.columns)

# 데이터 병합 (국가별 인구 추가)
world = world.merge(population_df, left_on="NAME", right_on="country", how="left")
world["population"] = world["population"].fillna(0)

# 슬라이더 추가 (사용자가 인구 필터링)
min_pop, max_pop = st.slider(
    "Filter by Population",
    min_value=int(world["population"].min()),
    max_value=int(world["population"].max()),
    value=(int(world["population"].min()), int(world["population"].max())),
)

# 선택한 범위에 맞게 데이터 필터링
filtered_world = world[
    (world["population"] >= min_pop) & (world["population"] <= max_pop)
]

# 특정 국가 검색 기능 추가
search_country = st.text_input("Search for a country (case-sensitive)", "")

if search_country:
    filtered_world = filtered_world[
        filtered_world["NAME"].str.contains(search_country, case=True, na=False)
    ]

# 국가별 인구 순위 표시
filtered_world = filtered_world.merge(
    population_df[["country", "rank"]], left_on="NAME", right_on="country", how="left"
)

# 지도 시각화 (인구 0이면 흰색으로 설정)
fig = px.choropleth(
    filtered_world,
    geojson=filtered_world.geometry,
    locations=filtered_world.index,
    color="population",
    hover_name="NAME",
    hover_data=["rank_y", "population"],
    projection="natural earth",
    color_continuous_scale=[
        (0, "white"),
        (0.01, "lightyellow"),
        (0.5, "orange"),
        (1, "darkred"),
    ],
    title="World Population Map",
)

# 레이아웃 조정 (화면 꽉 차게)
fig.update_layout(
    autosize=True,
    height=800,  # 높이 크게 설정
    margin=dict(l=0, r=0, t=0, b=0),  # 여백 제거
    geo=dict(showframe=False, showcoastlines=False),  # 지도 테두리 제거
)

# Streamlit에 지도 렌더링 (화면 가득 차게)
st.plotly_chart(fig, use_container_width=True)

# 인구 순위 테이블 표시 (Top 30)
st.subheader("Top Population Rankings")
st.dataframe(
    population_df[["rank", "country", "population"]].set_index("rank").head(30)
)
