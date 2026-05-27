#!/usr/bin/env python
# coding: utf-8

# # Assignment 4: Smoking, Tax Revenue, and Mortality Dashboard
# 
# This notebook prepares and visualizes data about cigarette tax revenue, smoking-attributable mortality, and lung/respiratory cancer deaths across U.S. states.
# 
# The notebook is organized in this order:
# 
# 1. Imports and dashboard setup
# 2. Data loading
# 3. Cleaning each dataset
# 4. Merging the final dataset
# 5. Dashboard overview
# 6. Map visualization
# 7. Bar chart rankings
# 8. Scatter plot correlation analysis
# 9. Correlation heatmap
# 10. Data tables at the end for transparency
# 
# The tables are intentionally placed at the bottom so the dashboard starts with the main story and visualizations first.
# 

# ## 1. Imports and dashboard setup
# 
# Run this notebook normally in Jupyter for review, or convert it to a Streamlit app with:
# 
# ```bash
# python3 -m jupyter nbconvert --to script Assignment_4_reordered_clean.ipynb
# streamlit run Assignment_4_reordered_clean.py
# ```
# 
# Install missing packages from Terminal, not inside the notebook:
# 
# ```bash
# python3 -m pip install pandas plotly streamlit statsmodels jupyter
# ```
# 

# In[ ]:


from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Streamlit page settings must be the first Streamlit command.
st.set_page_config(
    page_title="Smoking & Tax Revenue Dashboard",
    page_icon="📊",
    layout="wide"
)


# In[ ]:


st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    h1, h2, h3 {
        color: #0F172A !important;
        font-weight: 700;
    }

    p, li, label, .stMarkdown {
        color: #0F172A;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }

    div[data-testid="stMetric"] * {
        color: #0F172A !important;
    }

    /* Plotly chart containers */
    div[data-testid="stPlotlyChart"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 12px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        color: #475569 !important;
        font-weight: 600;
        background-color: transparent !important;
        border: none !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2563EB !important;
        border-bottom: 3px solid #2563EB !important;
    }

    /* Main page dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
    }

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: #0F172A !important;
    }

    div[data-baseweb="select"] svg {
        color: #0F172A !important;
        fill: #0F172A !important;
    }

    /* Main buttons */
    div[data-testid="stButton"] button {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }

    /* Multiselect selected tags */
    span[data-baseweb="tag"] {
        background-color: #EF4444 !important;
        color: #FFFFFF !important;
    }

    span[data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #1F2937 !important;
    }

    /* Sidebar text */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] * {
        color: #F8FAFC !important;
    }

    /* Sidebar dropdowns */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        color: #F8FAFC !important;
        border: 1px solid #4B5563 !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] span,
    section[data-testid="stSidebar"] div[data-baseweb="select"] input {
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
        color: #F8FAFC !important;
        fill: #F8FAFC !important;
    }

    /* Sidebar slider */
    section[data-testid="stSidebar"] div[data-testid="stSlider"] * {
        color: #F8FAFC !important;
    }

    /* Expander headers */
    div[data-testid="stExpander"] details summary {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }

    div[data-testid="stExpander"] details summary * {
        color: #0F172A !important;
    }


    </style>
    """,
    unsafe_allow_html=True
)


# ## 2. Data sources
# 
# This project uses three datasets:
# 
# - **Cigarette tax revenue dataset:** average cigarette tax revenue by U.S. state.
# - **Smoking-attributable mortality dataset:** estimated deaths attributable to smoking.
# - **Lung/respiratory cancer deaths dataset:** deaths from lung and respiratory system cancers.
# 
# All datasets are combined at the state level for the years 2005–2009.
# 

# In[ ]:


# File paths
# Works both in a notebook and after converting to a .py file.
try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()

DATA_DIR = BASE_DIR / "data"

REVENUE_FILE = "Table_of_Gross_Cigarette_Tax_Revenue_Per_State_(Orzechowski_and_Walker_Tax_Burden_on_Tobacco)_20260417.csv"
CANCER_FILE = "Lung_Cancer_Deaths.csv"
SAM_FILE = "Smoking-Attributable_Mortality,_Morbidity,_and_Economic_Costs_(SAMMEC)_-_Smoking-Attributable_Mortality_(SAM)_20260417.csv"

revenue_path = DATA_DIR / REVENUE_FILE
cancer_path = DATA_DIR / CANCER_FILE
sam_path = DATA_DIR / SAM_FILE

missing_files = [str(path) for path in [revenue_path, cancer_path, sam_path] if not path.exists()]

if missing_files:
    st.error("Some required CSV files are missing. Make sure the data folder is in the same folder as this notebook/script.")
    st.write(missing_files)
    st.stop()


# ## 3. Load the datasets
# 
# The datasets are loaded first, then cleaned separately so each transformation is easier to understand.
# 

# In[ ]:


revenue_raw = pd.read_csv(revenue_path)
cancer_raw = pd.read_csv(cancer_path)
sam_raw = pd.read_csv(sam_path)


# ## 4. Clean cigarette tax revenue data
# 
# This section keeps the years 2005–2009, converts revenue values to numeric format, and calculates the mean cigarette tax revenue for each state.
# 

# In[ ]:


revenue = revenue_raw.copy()

revenue.drop(
    ["Datasource", "Source", "TopicTypeId", "TopicId", "MeasureId"],
    axis=1,
    inplace=True,
    errors="ignore"
)

revenue_2005_2009 = revenue[
    (revenue["Year"] >= 2005) &
    (revenue["Year"] <= 2009)
].copy()

revenue_2005_2009["Data_Value"] = pd.to_numeric(
    revenue_2005_2009["Data_Value"].astype(str).str.replace(",", "", regex=False),
    errors="coerce"
)

revenue_avg = (
    revenue_2005_2009
    .groupby(["LocationAbbr", "LocationDesc"], as_index=False)["Data_Value"]
    .mean()
    .rename(columns={"Data_Value": "Mean_State_Revenue"})
)


# ## 5. Clean smoking-attributable mortality data
# 
# This section keeps the overall population estimate and the average annual smoking-attributable mortality measure.
# 

# In[ ]:


sam = sam_raw.copy()

sam.drop(
    [
        "DataSource",
        "Data_Value_Unit",
        "Data_Value_Footnote_Symbol",
        "Data_Value_Footnote",
        "Data_Value_Type",
        "TopicTypeID",
        "TopicID"
    ],
    axis=1,
    inplace=True,
    errors="ignore"
)

sam["Data_Value"] = pd.to_numeric(
    sam["Data_Value"].astype(str).str.replace(",", "", regex=False),
    errors="coerce"
)

sam_avg = sam[
    (sam["Sex"] == "Overall") &
    (sam["MeasureDesc"] == "Average Annual SAM")
].copy()

sam_avg = sam_avg[["LocationAbbr", "Data_Value"]].rename(
    columns={"Data_Value": "Avg_Annual_SAM"}
)


# ## 6. Clean lung/respiratory cancer deaths data
# 
# This section keeps the state-level cancer death counts and aligns the state column name with the other datasets.
# 

# In[ ]:


cancer = cancer_raw.copy()

# The source file may include extra summary rows at the bottom, so we keep the first 52 rows as in the original project.
cancer = cancer.iloc[:52].copy()

cancer = cancer.rename(columns={"State": "LocationDesc"})

cancer["Deaths"] = pd.to_numeric(
    cancer["Deaths"].astype(str).str.replace(",", "", regex=False),
    errors="coerce"
)

cancer = cancer.rename(columns={"Deaths": "Average_Cancer_Deaths"})


# ## 7. Merge final dataset and create derived metrics
# 
# The final dataset combines all three cleaned datasets by state. New derived metrics are added so the dashboard can compare revenue and mortality in multiple ways.
# 

# In[ ]:


final = pd.merge(
    revenue_avg,
    sam_avg,
    on="LocationAbbr",
    how="inner"
)

final = pd.merge(
    final,
    cancer,
    on="LocationDesc",
    how="inner"
)

final["Revenue_per_SAM"] = final["Mean_State_Revenue"] / final["Avg_Annual_SAM"]
final["SAM_per_Cancer_Death"] = final["Avg_Annual_SAM"] / final["Average_Cancer_Deaths"]
final["Revenue_per_Cancer_Death"] = final["Mean_State_Revenue"] / final["Average_Cancer_Deaths"]

# Keep only the columns needed for the dashboard first, while preserving extra cancer columns at the end if present.
priority_columns = [
    "LocationAbbr",
    "LocationDesc",
    "Mean_State_Revenue",
    "Avg_Annual_SAM",
    "Average_Cancer_Deaths",
    "Revenue_per_SAM",
    "SAM_per_Cancer_Death",
    "Revenue_per_Cancer_Death"
]

remaining_columns = [col for col in final.columns if col not in priority_columns]
final = final[priority_columns + remaining_columns]


# ## 8. Dashboard overview
# 
# The dashboard starts with a short explanation and summary cards before showing visualizations. This keeps the story clear before showing detailed tables.
# 

# In[ ]:


st.title("📊 Smoking, Tax Revenue, and Mortality Dashboard")

st.markdown(
    """
    This dashboard explores how **cigarette tax revenue**, **smoking-attributable mortality**,
    and **lung/respiratory cancer deaths** vary across U.S. states between **2005 and 2009**.
    """
)

st.header("Project Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("States Analyzed", f"{len(final):,}")
col2.metric("Average Tax Revenue", f"${final['Mean_State_Revenue'].mean():,.0f}")
col3.metric("Average Annual SAM Deaths", f"{final['Avg_Annual_SAM'].mean():,.0f}")
col4.metric("Average Cancer Deaths", f"{final['Average_Cancer_Deaths'].mean():,.0f}")

st.markdown(
    """
    **Metric definitions:**

    - **Tax Revenue:** average cigarette tax revenue by state.
    - **SAM Deaths:** estimated average annual deaths attributable to smoking.
    - **Cancer Deaths:** lung and respiratory cancer deaths by state.
    - **Ratio metrics:** calculated values used to compare revenue and mortality across states.
    """
)


# In[ ]:


METRIC_MAPPING = {
    "Tax Revenue": "Mean_State_Revenue",
    "Smoking Mortality (SAM)": "Avg_Annual_SAM",
    "Lung/Respiratory Cancer Deaths": "Average_Cancer_Deaths",
    "Revenue per SAM Death": "Revenue_per_SAM",
    "SAM per Cancer Death": "SAM_per_Cancer_Death",
    "Revenue per Cancer Death": "Revenue_per_Cancer_Death"
}
DISPLAY_LABELS = {
    "Mean_State_Revenue": "Tax Revenue",
    "Avg_Annual_SAM": "Smoking Mortality",
    "Average_Cancer_Deaths": "Cancer Deaths",
    "Revenue_per_SAM": "Revenue per SAM",
    "SAM_per_Cancer_Death": "SAM per Cancer Death",
    "Revenue_per_Cancer_Death": "Revenue per Cancer Death"
}

state_name_map = dict(zip(final["LocationAbbr"], final["LocationDesc"]))
state_options = sorted(final["LocationAbbr"].dropna().unique())

st.sidebar.header("Dashboard Controls")

map_metric_name = st.sidebar.selectbox(
    "Map metric:",
    options=list(METRIC_MAPPING.keys()),
    index=0
)

bar_metric_name = st.sidebar.selectbox(
    "Bar chart metric:",
    options=list(METRIC_MAPPING.keys()),
    index=0
)

number_of_states = st.sidebar.slider(
    "Number of states in bar chart:",
    min_value=5,
    max_value=20,
    value=10
)

if "selected_states" not in st.session_state:
    st.session_state["selected_states"] = (
        final.sort_values("Mean_State_Revenue", ascending=False)["LocationAbbr"]
        .head(6)
        .tolist()
    )

if "map_key" not in st.session_state:
    st.session_state["map_key"] = 0


def clear_selection():
    st.session_state["selected_states"] = []
    st.session_state["map_key"] += 1


# ## 9. Organized visualizations
# 
# The visualizations are placed in tabs so each section has a clear purpose.
# 

# In[ ]:


tab_map, tab_bar, tab_scatter, tab_heatmap, tab_data = st.tabs(
    [
        "🗺️ Map",
        "📊 Bar Chart",
        "🔍 Scatter Plot",
        "🌡️ Correlation Heatmap",
        "📄 Data Tables"
    ]
)


# In[1]:


with tab_map:
    st.header("National Overview Map")
    st.markdown(
        "This map shows how the selected metric varies geographically across U.S. states. "
        "Click a state on the map to add it to the scatter plot comparison."
    )

    selected_map_col = METRIC_MAPPING[map_metric_name]

    fig_map = go.Figure(
        data=go.Choropleth(
            locations=final["LocationAbbr"],
            z=final[selected_map_col],
            text=final["LocationDesc"],
            locationmode="USA-states",
            colorscale="Viridis",
            colorbar_title=map_metric_name,
            hovertemplate="<b>%{text}</b><br>Value: %{z:,.2f}<extra></extra>"
        )
    )

    fig_map.update_layout(
        title={
            "text": f"{map_metric_name} by State",
            "x": 0.5,
            "xanchor": "center",
            "font": {"color": "#000000", "size": 22}
        },
        geo_scope="usa",
        clickmode="event+select",
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#000000", size=14),
        margin=dict(l=0, r=0, t=60, b=0)
    )

    map_event = st.plotly_chart(
        fig_map,
        width="stretch",
        theme=None,
        on_select="rerun",
        key=f"map_{st.session_state['map_key']}"
    )

    state_added = False

    if map_event and "selection" in map_event and "points" in map_event["selection"]:
        for point in map_event["selection"]["points"]:
            state_clicked = point.get("location")

            if state_clicked and state_clicked not in st.session_state["selected_states"]:
                st.session_state["selected_states"].append(state_clicked)
                state_added = True

    if state_added:
        st.rerun()


# In[ ]:


with tab_bar:
    st.header("Top States Ranking")
    st.markdown(
        "This bar chart ranks states by the selected metric. "
        "Use the sidebar to choose the metric and number of states."
    )

    selected_bar_col = METRIC_MAPPING[bar_metric_name]

    top_states = (
        final
        .sort_values(selected_bar_col, ascending=False)
        .head(number_of_states)
        .sort_values(selected_bar_col)
    )

    fig_bar = px.bar(
        top_states,
        x=selected_bar_col,
        y="LocationDesc",
        orientation="h",
        title=f"Top {number_of_states} States by {bar_metric_name}",
        labels={
            selected_bar_col: bar_metric_name,
            "LocationDesc": "State"
        },
        hover_data=[
            "LocationAbbr",
            "Mean_State_Revenue",
            "Avg_Annual_SAM",
            "Average_Cancer_Deaths"
        ]
    )

    fig_bar.update_traces(marker_color="#2563EB")
    fig_bar.update_traces(marker_color="#440154")

    fig_bar.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#000000", size=14),
        title_font=dict(size=22, color="#000000"),
        xaxis=dict(
            tickfont=dict(color="#000000", size=13),
            title_font=dict(color="#000000", size=14)
        ),
        yaxis=dict(
            tickfont=dict(color="#000000", size=13),
            title_font=dict(color="#000000", size=14)
        ),
        margin=dict(l=140, r=40, t=70, b=50)
    )

    st.plotly_chart(fig_bar, width="stretch", theme=None)


# In[ ]:


with tab_scatter:
    st.header("State Comparison and Correlation")
    st.markdown(
        "This scatter plot compares two selected metrics for the chosen states. "
        "Choose at least two states and two different metrics."
    )

    col_select, col_clear = st.columns([4, 1])

    # Remove old invalid selections if the app was changed from full state names to abbreviations.
    st.session_state["selected_states"] = [
        state for state in st.session_state["selected_states"]
        if state in state_options
    ]

    with col_select:
        st.multiselect(
            "Select states to analyze:",
            options=state_options,
            key="selected_states",
            format_func=lambda abbr: f"{state_name_map.get(abbr, abbr)} ({abbr})"
        )

    with col_clear:
        st.write("")
        st.write("")
        st.button("Clear States", on_click=clear_selection)

    col_x, col_y = st.columns(2)

    with col_x:
        x_metric_name = st.selectbox(
            "Select X-axis metric:",
            options=list(METRIC_MAPPING.keys()),
            index=0
        )

    with col_y:
        y_metric_name = st.selectbox(
            "Select Y-axis metric:",
            options=list(METRIC_MAPPING.keys()),
            index=1
        )

    x_col = METRIC_MAPPING[x_metric_name]
    y_col = METRIC_MAPPING[y_metric_name]

    df_selected = final[final["LocationAbbr"].isin(st.session_state["selected_states"])].copy()

    if x_col == y_col:
        st.info("Please select two different metrics for the X-axis and Y-axis.")

    elif len(df_selected) < 2:
        st.info("Please select at least two states to view the scatter plot and regression line.")

    else:
        correlation = df_selected[x_col].corr(df_selected[y_col])
        st.write(f"**Pearson correlation for selected states:** {correlation:.3f}")

        try:
            fig_scatter = px.scatter(
                df_selected,
                x=x_col,
                y=y_col,
                text="LocationAbbr",
                hover_name="LocationDesc",
                trendline="ols",
                title=f"{y_metric_name} vs. {x_metric_name}",
                labels={
                    x_col: x_metric_name,
                    y_col: y_metric_name
                }
            )
        except Exception:
            fig_scatter = px.scatter(
                df_selected,
                x=x_col,
                y=y_col,
                text="LocationAbbr",
                hover_name="LocationDesc",
                title=f"{y_metric_name} vs. {x_metric_name}",
                labels={
                    x_col: x_metric_name,
                    y_col: y_metric_name
                }
            )
            st.info("Install statsmodels if you want the trendline: python3 -m pip install statsmodels")

            fig_scatter.update_traces(
                marker=dict(size=11, color="#2563EB", line=dict(width=1, color="white")),
                textposition="top center"
            )

            fig_scatter.update_layout(
                template="plotly_white",
                paper_bgcolor="white",
                plot_bgcolor="white",
                font=dict(color="#0F172A"),
                title_font=dict(size=22, color="#0F172A"),
                margin=dict(l=20, r=20, t=60, b=20)
            )

        st.plotly_chart(fig_scatter, width="stretch")


# In[ ]:


with tab_heatmap:
    st.header("Correlation Heatmap")
    st.markdown(
        "This heatmap summarizes how strongly the numeric variables are related. "
        "Values closer to 1 mean a stronger positive relationship, values closer to -1 mean a stronger negative relationship."
    )

    heatmap_columns = list(METRIC_MAPPING.values())
    corr = final[heatmap_columns].corr()

    corr = corr.rename(index=DISPLAY_LABELS, columns=DISPLAY_LABELS)

    fig_heatmap = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="Viridis",
        zmin=-1,
        zmax=1,
        aspect="auto",
        title="Correlation Between Dashboard Metrics"
    )

    fig_heatmap.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#000000", size=14),
        title_font=dict(size=24, color="#000000"),
        margin=dict(l=160, r=60, t=80, b=160),
        height=700,
        coloraxis_colorbar=dict(
            title=dict(text="Correlation", font=dict(color="#000000", size=14)),
            tickfont=dict(color="#000000", size=13)
        )
    )

    fig_heatmap.update_xaxes(
        tickangle=35,
        tickfont=dict(color="#000000", size=13),
        title_font=dict(color="#000000", size=14)
    )

    fig_heatmap.update_yaxes(
        tickfont=dict(color="#000000", size=13),
        title_font=dict(color="#000000", size=14)
    )

    fig_heatmap.update_traces(
        textfont=dict(size=14, color="white")
    )

    st.plotly_chart(fig_heatmap, width="stretch", theme=None)


# In[ ]:


with tab_data:
    st.header("Data Tables")
    st.markdown(
        "The tables are placed at the end so the dashboard starts with the main insights first. "
        "These tables document the cleaned data used in the visualizations."
    )

    with st.expander("Cleaned cigarette tax revenue data"):
        st.markdown("Average cigarette tax revenue by state for 2005–2009.")
        st.dataframe(revenue_avg, width="stretch")

    with st.expander("Cleaned smoking-attributable mortality data"):
        st.markdown("Average annual smoking-attributable mortality by state.")
        st.dataframe(sam_avg, width="stretch")

    with st.expander("Cleaned lung/respiratory cancer deaths data"):
        st.markdown("State-level lung and respiratory cancer death data.")
        st.dataframe(cancer, width="stretch")

    with st.expander("Final merged dataset"):
        st.markdown("Final merged dataset used to create the dashboard visualizations.")
        st.dataframe(final, width="stretch")

