import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# 타이틀
st.set_page_config(layout="wide")
st.title("World Population Map")


# 국가별 인구(수) 데이터 로드
@st.cache_data
def load_population_data():
    df = pd.read_csv("./data/countries_by_population.csv")
    df = df.sort_values(by="population", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1  # 순위 추가
    return df


population_df = load_population_data()


# 국가별 영토(land+water) 데이터 추가
@st.cache_data
def load_area_data():
    df = pd.read_csv("./data/countries_by_area.csv")
    df = df.sort_values(by="area", ascending=False).reset_index(drop=True)
    return df


area_df = load_area_data()


# GeoPandas 세계 지도 데이터 로드
# https://www.naturalearthdata.com/downloads/110m-cultural-vectors
@st.cache_data
def load_world_data():
    world = gpd.read_file("./maps/110m_cultural/ne_110m_admin_0_countries.shp")
    return world


world = load_world_data()
print(world.columns)

# 데이터 병합 (인구 & 면적 추가)
world = world.merge(population_df, left_on="NAME", right_on="country", how="left")
world = world.merge(area_df, left_on="NAME", right_on="country", how="left")

# 결측값 처리
world["population"] = world["population"].fillna(0)
world["area"] = world["area"].fillna(0)

# 인구밀도 계산 (면적이 0이면 인구밀도도 0)
world["population_density"] = world.apply(
    lambda row: 0 if row["area"] == 0 else round(row["population"] / row["area"], 2),
    axis=1,
)

# 순위 데이터 추가
world["population_rank"] = (
    world["population"].rank(ascending=False, method="min").astype(int)
)
world["population_density_rank"] = (
    world["population_density"].rank(ascending=False, method="min").astype(int)
)

# 메뉴 추가
option = st.radio("Select Data Type", ["Population", "Population Density"])

# 슬라이더 추가 (사용자가 필터링)
if option == "Population":
    min_val, max_val = int(world["population"].min()), int(world["population"].max())
else:
    min_val, max_val = int(world["population_density"].min()), int(
        world["population_density"].max() + 1
    )

filter_min, filter_max = st.slider(
    f"Filter by {option}",
    min_value=min_val,
    max_value=max_val,
    value=(min_val, max_val),
)

# 선택한 범위에 맞게 데이터 필터링
if option == "Population":
    filtered_world = world[
        (world["population"] >= filter_min) & (world["population"] <= filter_max)
    ]
    color_column = "population"
else:
    filtered_world = world[
        (world["population_density"] >= filter_min)
        & (world["population_density"] <= filter_max)
    ]
    color_column = "population_density"


# 특정 국가 검색 기능 추가
search_country = st.text_input("Search for a country (case-sensitive)", "")
if search_country:
    filtered_world = filtered_world[
        filtered_world["NAME"].str.contains(search_country, case=True, na=False)
    ]

# 지도 시각화 (인구 0이면 흰색으로 설정)
fig = px.choropleth(
    filtered_world,
    geojson=filtered_world.geometry,
    locations=filtered_world.index,
    color=color_column,
    hover_name="NAME",
    hover_data=(
        ["population", "population_rank"]
        if option == "Population"
        else ["population", "population_density", "population_density_rank"]
    ),
    projection="natural earth",
    color_continuous_scale=[
        (0, "white"),
        (0.01, "lightyellow"),
        (0.5, "orange"),
        (1, "darkred"),
    ],
    title=f"World {option} Map",
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
st.subheader(f"Top {option} Rankings")

if option == "Population":
    top_df = population_df.sort_values(by="population", ascending=False).head(30)
    top_df = top_df[["rank", "country", "population"]]
else:
    top_df = world[["NAME", "population_density"]].copy()
    top_df = top_df.rename(columns={"NAME": "country"})
    top_df = top_df.sort_values(by="population_density", ascending=False).head(30)
    top_df.insert(0, "rank", range(1, len(top_df) + 1))  # 순위 추가

st.dataframe(top_df.set_index("rank"))
