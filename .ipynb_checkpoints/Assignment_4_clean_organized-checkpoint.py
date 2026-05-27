from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = "notebook_connected"
pd.set_option("display.max_columns", None)

DATA_DIR = Path("data")

REVENUE_FILE = DATA_DIR / "Table_of_Gross_Cigarette_Tax_Revenue_Per_State_(Orzechowski_and_Walker_Tax_Burden_on_Tobacco)_20260417.csv"
CANCER_FILE = DATA_DIR / "Lung_Cancer_Deaths.csv"
SAM_FILE = DATA_DIR / "Smoking-Attributable_Mortality,_Morbidity,_and_Economic_Costs_(SAMMEC)_-_Smoking-Attributable_Mortality_(SAM)_20260417.csv"

required_files = [REVENUE_FILE, CANCER_FILE, SAM_FILE]
missing_files = [str(file) for file in required_files if not file.exists()]

if missing_files:
    print("Missing files. Make sure the data folder is in the same folder as this notebook:")
    for file in missing_files:
        print(" -", file)
else:
    print("All required data files were found.")

revenue_raw = pd.read_csv(REVENUE_FILE)
cancer_raw = pd.read_csv(CANCER_FILE)
sam_raw = pd.read_csv(SAM_FILE)

print("Revenue dataset shape:", revenue_raw.shape)
print("Cancer deaths dataset shape:", cancer_raw.shape)
print("SAM dataset shape:", sam_raw.shape)

print("Cigarette tax revenue preview")
st.dataframe(revenue_raw.head())

print("Lung/respiratory cancer deaths preview")
st.dataframe(cancer_raw.head())

print("Smoking-attributable mortality preview")
st.dataframe(sam_raw.head())

revenue = revenue_raw.copy()

# Remove metadata columns that are not needed for analysis.
revenue = revenue.drop(
    columns=["Datasource", "Source", "TopicTypeId", "TopicId", "MeasureId"],
    errors="ignore"
)

# Keep only the years used in this project.
revenue_2005_2009 = revenue[
    (revenue["Year"] >= 2005) &
    (revenue["Year"] <= 2009)
].copy()

# Convert revenue values from strings like "1,234" to numeric values.
revenue_2005_2009["Data_Value"] = pd.to_numeric(
    revenue_2005_2009["Data_Value"].astype(str).str.replace(",", "", regex=False),
    errors="coerce"
)

# Average revenue by state.
revenue_avg = (
    revenue_2005_2009
    .groupby(["LocationAbbr", "LocationDesc"], as_index=False)["Data_Value"]
    .mean()
    .rename(columns={"Data_Value": "Mean_State_Revenue"})
)

revenue_avg.head()

sam = sam_raw.copy()

sam = sam.drop(
    columns=[
        "DataSource",
        "Data_Value_Unit",
        "Data_Value_Footnote_Symbol",
        "Data_Value_Footnote",
        "Data_Value_Type",
        "TopicTypeID",
        "TopicID"
    ],
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

sam_avg.head()

cancer_deaths = cancer_raw.copy()

# The original notebook used the first 52 rows to keep state-level entries.
cancer_deaths = cancer_deaths.iloc[:52].copy()

cancer_deaths = cancer_deaths.rename(columns={"State": "LocationDesc"})

cancer_deaths["Deaths"] = pd.to_numeric(
    cancer_deaths["Deaths"].astype(str).str.replace(",", "", regex=False),
    errors="coerce"
)

cancer_deaths = cancer_deaths.rename(columns={"Deaths": "Average_Cancer_Deaths"})

cancer_deaths.head()

final = pd.merge(
    revenue_avg,
    sam_avg,
    on="LocationAbbr",
    how="inner"
)

final = pd.merge(
    final,
    cancer_deaths,
    on="LocationDesc",
    how="inner"
)

# Derived metrics used in visualizations.
final["Revenue_per_SAM"] = final["Mean_State_Revenue"] / final["Avg_Annual_SAM"]
final["SAM_per_Cancer_Death"] = final["Avg_Annual_SAM"] / final["Average_Cancer_Deaths"]
final["Revenue_per_Cancer_Death"] = final["Mean_State_Revenue"] / final["Average_Cancer_Deaths"]

# Sort alphabetically for easier reading.
final = final.sort_values("LocationDesc").reset_index(drop=True)

print("Final dataset shape:", final.shape)
final.head()

summary_cards = pd.DataFrame({
    "Metric": [
        "States analyzed",
        "Average tax revenue",
        "Average annual SAM deaths",
        "Average lung/respiratory cancer deaths"
    ],
    "Value": [
        f"{len(final):,}",
        f"${final['Mean_State_Revenue'].mean():,.0f}",
        f"{final['Avg_Annual_SAM'].mean():,.0f}",
        f"{final['Average_Cancer_Deaths'].mean():,.0f}"
    ]
})

summary_cards

METRIC_MAPPING = {
    "Tax Revenue": "Mean_State_Revenue",
    "Smoking Mortality (SAM)": "Avg_Annual_SAM",
    "Respiratory Cancer Deaths": "Average_Cancer_Deaths",
    "Revenue per SAM Death": "Revenue_per_SAM",
    "SAM per Respiratory Cancer Death": "SAM_per_Cancer_Death",
    "Revenue per Respiratory Cancer Death": "Revenue_per_Cancer_Death"
}

DISPLAY_LABELS = {
    "Mean_State_Revenue": "Tax Revenue",
    "Avg_Annual_SAM": "Smoking-Attributable Mortality",
    "Average_Cancer_Deaths": "Respiratory Cancer Deaths",
    "Revenue_per_SAM": "Revenue per SAM Death",
    "SAM_per_Cancer_Death": "SAM per Respiratory Cancer Death",
    "Revenue_per_Cancer_Death": "Revenue per Respiratory Cancer Death"
}

def make_choropleth(metric_name="Tax Revenue"):
    column = METRIC_MAPPING[metric_name]

    fig = go.Figure(
        data=go.Choropleth(
            locations=final["LocationAbbr"],
            z=final[column],
            text=final["LocationDesc"],
            locationmode="USA-states",
            colorscale="Blues",
            colorbar_title=metric_name,
            marker_line_color="white",
            marker_line_width=0.5
        )
    )

    fig.update_layout(
        title={"text": f"{metric_name} by State", "x": 0.5, "xanchor": "center"},
        geo_scope="usa",
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#111827"),
        margin=dict(l=0, r=0, t=60, b=0),
        height=550
    )

    return fig

fig_map = make_choropleth("Tax Revenue")
fig_map.show()

def make_top_states_bar(metric_name, top_n=10):
    column = METRIC_MAPPING[metric_name]

    top_states = (
        final
        .sort_values(column, ascending=False)
        .head(top_n)
        .sort_values(column, ascending=True)
    )

    fig = px.bar(
        top_states,
        x=column,
        y="LocationDesc",
        orientation="h",
        title=f"Top {top_n} States by {metric_name}",
        labels={column: metric_name, "LocationDesc": "State"},
        hover_data=["LocationAbbr", "Mean_State_Revenue", "Avg_Annual_SAM", "Average_Cancer_Deaths"]
    )

    fig.update_traces(marker_color="#3B82F6")
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#111827"),
        title_font_size=22,
        margin=dict(l=20, r=20, t=60, b=20),
        height=500
    )

    return fig

fig_bar_revenue = make_top_states_bar("Tax Revenue", top_n=10)
fig_bar_revenue.show()

fig_bar_sam = make_top_states_bar("Smoking Mortality (SAM)", top_n=10)
fig_bar_sam.show()

fig_bar_cancer = make_top_states_bar("Respiratory Cancer Deaths", top_n=10)
fig_bar_cancer.show()

comparison = final.copy()

index_columns = [
    "Mean_State_Revenue",
    "Avg_Annual_SAM",
    "Average_Cancer_Deaths"
]

for column in index_columns:
    comparison[f"{column}_Index"] = comparison[column] / comparison[column].max() * 100

top_comparison = (
    comparison
    .sort_values("Average_Cancer_Deaths", ascending=False)
    .head(10)
)

comparison_long = top_comparison.melt(
    id_vars=["LocationDesc"],
    value_vars=[
        "Mean_State_Revenue_Index",
        "Avg_Annual_SAM_Index",
        "Average_Cancer_Deaths_Index"
    ],
    var_name="Metric",
    value_name="Index Value"
)

comparison_long["Metric"] = comparison_long["Metric"].replace({
    "Mean_State_Revenue_Index": "Tax Revenue Index",
    "Avg_Annual_SAM_Index": "SAM Deaths Index",
    "Average_Cancer_Deaths_Index": "Cancer Deaths Index"
})

fig_indexed = px.bar(
    comparison_long,
    x="Index Value",
    y="LocationDesc",
    color="Metric",
    orientation="h",
    barmode="group",
    title="Indexed Comparison of Revenue, SAM Deaths, and Cancer Deaths",
    labels={"LocationDesc": "State", "Index Value": "Index Value (highest state = 100)"}
)

fig_indexed.update_layout(
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color="#111827"),
    title_font_size=22,
    margin=dict(l=20, r=20, t=60, b=20),
    height=600
)

fig_indexed.show()

def make_scatter(x_metric_name="Tax Revenue", y_metric_name="Smoking Mortality (SAM)"):
    x_col = METRIC_MAPPING[x_metric_name]
    y_col = METRIC_MAPPING[y_metric_name]

    if x_col == y_col:
        print("Please choose two different metrics for the X-axis and Y-axis.")
        return None

    correlation = final[x_col].corr(final[y_col])
    print(f"Pearson correlation between {x_metric_name} and {y_metric_name}: {correlation:.3f}")

    try:
        fig = px.scatter(
            final,
            x=x_col,
            y=y_col,
            text="LocationAbbr",
            hover_name="LocationDesc",
            trendline="ols",
            title=f"{y_metric_name} vs. {x_metric_name}",
            labels={x_col: x_metric_name, y_col: y_metric_name}
        )
    except Exception:
        fig = px.scatter(
            final,
            x=x_col,
            y=y_col,
            text="LocationAbbr",
            hover_name="LocationDesc",
            title=f"{y_metric_name} vs. {x_metric_name}",
            labels={x_col: x_metric_name, y_col: y_metric_name}
        )
        print("Trendline was skipped. Install statsmodels to enable it: python3 -m pip install statsmodels")

    fig.update_traces(textposition="top center")
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#111827"),
        title_font_size=22,
        margin=dict(l=20, r=20, t=60, b=20),
        height=550
    )

    return fig

fig_scatter = make_scatter("Tax Revenue", "Smoking Mortality (SAM)")
fig_scatter.show()

corr_columns = list(METRIC_MAPPING.values())
corr_matrix = final[corr_columns].corr()

corr_matrix_display = corr_matrix.rename(index=DISPLAY_LABELS, columns=DISPLAY_LABELS)

fig_heatmap = px.imshow(
    corr_matrix_display,
    text_auto=".2f",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    title="Correlation Heatmap of Project Metrics"
)

fig_heatmap.update_layout(
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color="#111827"),
    title_font_size=22,
    margin=dict(l=20, r=20, t=60, b=20),
    height=650
)

fig_heatmap.show()

revenue_avg.head(10)

sam_avg.head(10)

cancer_deaths.head(10)

final.head(15)

from pathlib import Path

APP_CODE = '\nfrom pathlib import Path\n\nimport pandas as pd\nimport plotly.express as px\nimport plotly.graph_objects as go\nimport streamlit as st\n\nst.set_page_config(\n    page_title="Smoking & Tax Revenue Dashboard",\n    page_icon="📊",\n    layout="wide"\n)\n\nst.markdown(\n    """\n    <style>\n    .stApp {\n        background-color: #F5F7FA;\n        color: #111827;\n    }\n    .block-container {\n        padding-top: 2rem;\n        padding-bottom: 2rem;\n    }\n    h1, h2, h3 {\n        color: #111827 !important;\n        font-family: Arial, sans-serif;\n    }\n    div[data-testid="stMetric"] {\n        background-color: #FFFFFF;\n        padding: 20px;\n        border-radius: 16px;\n        border: 1px solid #E5E7EB;\n        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.06);\n    }\n    div[data-testid="stMetric"] * {\n        color: #111827 !important;\n    }\n    div[data-testid="stPlotlyChart"] {\n        background-color: #FFFFFF;\n        border-radius: 16px;\n        padding: 12px;\n        border: 1px solid #E5E7EB;\n        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);\n    }\n    label {\n        color: #111827 !important;\n        font-weight: 600;\n    }\n    </style>\n    """,\n    unsafe_allow_html=True\n)\n\nDATA_DIR = Path(__file__).parent / "data"\n\nREVENUE_FILE = DATA_DIR / "Table_of_Gross_Cigarette_Tax_Revenue_Per_State_(Orzechowski_and_Walker_Tax_Burden_on_Tobacco)_20260417.csv"\nCANCER_FILE = DATA_DIR / "Lung_Cancer_Deaths.csv"\nSAM_FILE = DATA_DIR / "Smoking-Attributable_Mortality,_Morbidity,_and_Economic_Costs_(SAMMEC)_-_Smoking-Attributable_Mortality_(SAM)_20260417.csv"\n\n@st.cache_data\ndef load_data():\n    required_files = [REVENUE_FILE, CANCER_FILE, SAM_FILE]\n    missing_files = [str(file) for file in required_files if not file.exists()]\n\n    if missing_files:\n        st.error("Missing data files. Make sure the data folder is in the same folder as app.py.")\n        st.write(missing_files)\n        st.stop()\n\n    revenue_raw = pd.read_csv(REVENUE_FILE)\n    cancer_raw = pd.read_csv(CANCER_FILE)\n    sam_raw = pd.read_csv(SAM_FILE)\n\n    revenue = revenue_raw.drop(\n        columns=["Datasource", "Source", "TopicTypeId", "TopicId", "MeasureId"],\n        errors="ignore"\n    )\n\n    revenue_2005_2009 = revenue[\n        (revenue["Year"] >= 2005) &\n        (revenue["Year"] <= 2009)\n    ].copy()\n\n    revenue_2005_2009["Data_Value"] = pd.to_numeric(\n        revenue_2005_2009["Data_Value"].astype(str).str.replace(",", "", regex=False),\n        errors="coerce"\n    )\n\n    revenue_avg = (\n        revenue_2005_2009\n        .groupby(["LocationAbbr", "LocationDesc"], as_index=False)["Data_Value"]\n        .mean()\n        .rename(columns={"Data_Value": "Mean_State_Revenue"})\n    )\n\n    sam = sam_raw.drop(\n        columns=[\n            "DataSource",\n            "Data_Value_Unit",\n            "Data_Value_Footnote_Symbol",\n            "Data_Value_Footnote",\n            "Data_Value_Type",\n            "TopicTypeID",\n            "TopicID"\n        ],\n        errors="ignore"\n    )\n\n    sam["Data_Value"] = pd.to_numeric(\n        sam["Data_Value"].astype(str).str.replace(",", "", regex=False),\n        errors="coerce"\n    )\n\n    sam_avg = sam[\n        (sam["Sex"] == "Overall") &\n        (sam["MeasureDesc"] == "Average Annual SAM")\n    ].copy()\n\n    sam_avg = sam_avg[["LocationAbbr", "Data_Value"]].rename(\n        columns={"Data_Value": "Avg_Annual_SAM"}\n    )\n\n    cancer_deaths = cancer_raw.iloc[:52].copy()\n    cancer_deaths = cancer_deaths.rename(columns={"State": "LocationDesc"})\n    cancer_deaths["Deaths"] = pd.to_numeric(\n        cancer_deaths["Deaths"].astype(str).str.replace(",", "", regex=False),\n        errors="coerce"\n    )\n    cancer_deaths = cancer_deaths.rename(columns={"Deaths": "Average_Cancer_Deaths"})\n\n    final = pd.merge(revenue_avg, sam_avg, on="LocationAbbr", how="inner")\n    final = pd.merge(final, cancer_deaths, on="LocationDesc", how="inner")\n\n    final["Revenue_per_SAM"] = final["Mean_State_Revenue"] / final["Avg_Annual_SAM"]\n    final["SAM_per_Cancer_Death"] = final["Avg_Annual_SAM"] / final["Average_Cancer_Deaths"]\n    final["Revenue_per_Cancer_Death"] = final["Mean_State_Revenue"] / final["Average_Cancer_Deaths"]\n\n    final = final.sort_values("LocationDesc").reset_index(drop=True)\n\n    return final, revenue_avg, sam_avg, cancer_deaths\n\nfinal, revenue_avg, sam_avg, cancer_deaths = load_data()\n\nMETRIC_MAPPING = {\n    "Tax Revenue": "Mean_State_Revenue",\n    "Smoking Mortality (SAM)": "Avg_Annual_SAM",\n    "Respiratory Cancer Deaths": "Average_Cancer_Deaths",\n    "Revenue per SAM Death": "Revenue_per_SAM",\n    "SAM per Respiratory Cancer Death": "SAM_per_Cancer_Death",\n    "Revenue per Respiratory Cancer Death": "Revenue_per_Cancer_Death"\n}\n\nDISPLAY_LABELS = {\n    "Mean_State_Revenue": "Tax Revenue",\n    "Avg_Annual_SAM": "Smoking Mortality",\n    "Average_Cancer_Deaths": "Respiratory Cancer Deaths",\n    "Revenue_per_SAM": "Revenue per SAM Death",\n    "SAM_per_Cancer_Death": "SAM per Cancer Death",\n    "Revenue_per_Cancer_Death": "Revenue per Cancer Death"\n}\n\nst.title("📊 Smoking, Tax Revenue, and Mortality Dashboard")\nst.markdown(\n    """\n    This dashboard explores how **cigarette tax revenue**, **smoking-attributable mortality**,\n    and **lung/respiratory cancer deaths** vary across U.S. states from 2005 to 2009.\n    """\n)\n\nst.header("Project Overview")\ncol1, col2, col3, col4 = st.columns(4)\ncol1.metric("States Analyzed", f"{len(final):,}")\ncol2.metric("Average Tax Revenue", f"${final[\'Mean_State_Revenue\'].mean():,.0f}")\ncol3.metric("Average SAM Deaths", f"{final[\'Avg_Annual_SAM\'].mean():,.0f}")\ncol4.metric("Average Cancer Deaths", f"{final[\'Average_Cancer_Deaths\'].mean():,.0f}")\n\nst.markdown(\n    """\n    **Tax Revenue** is the average cigarette tax revenue by state.  \n    **SAM Deaths** are estimated annual deaths attributable to smoking.  \n    **Respiratory Cancer Deaths** are deaths from lung and respiratory system cancers.\n    """\n)\n\nst.divider()\n\ntab_map, tab_bar, tab_scatter, tab_heatmap, tab_data = st.tabs([\n    "🗺️ Map",\n    "📊 Bar Chart",\n    "🔍 Scatter Plot",\n    "🧮 Correlation Heatmap",\n    "📄 Data Tables"\n])\n\nwith tab_map:\n    st.header("National Overview Map")\n    st.markdown("This map shows how the selected metric varies across U.S. states.")\n\n    map_metric = st.selectbox("Select a metric to map:", list(METRIC_MAPPING.keys()))\n    map_col = METRIC_MAPPING[map_metric]\n\n    fig_map = go.Figure(\n        data=go.Choropleth(\n            locations=final["LocationAbbr"],\n            z=final[map_col],\n            text=final["LocationDesc"],\n            locationmode="USA-states",\n            colorscale="Blues",\n            colorbar_title=map_metric,\n            marker_line_color="white",\n            marker_line_width=0.5\n        )\n    )\n\n    fig_map.update_layout(\n        title={"text": f"{map_metric} by State", "x": 0.5, "xanchor": "center"},\n        geo_scope="usa",\n        template="plotly_white",\n        paper_bgcolor="white",\n        plot_bgcolor="white",\n        font=dict(color="#111827"),\n        margin=dict(l=0, r=0, t=60, b=0),\n        height=550\n    )\n\n    st.plotly_chart(fig_map, width="stretch")\n\nwith tab_bar:\n    st.header("Top States Ranking")\n    st.markdown("This chart ranks states by the selected metric.")\n\n    bar_metric = st.selectbox("Select a metric for the bar chart:", list(METRIC_MAPPING.keys()))\n    top_n = st.slider("Number of states to show:", min_value=5, max_value=20, value=10)\n    bar_col = METRIC_MAPPING[bar_metric]\n\n    top_states = (\n        final\n        .sort_values(bar_col, ascending=False)\n        .head(top_n)\n        .sort_values(bar_col, ascending=True)\n    )\n\n    fig_bar = px.bar(\n        top_states,\n        x=bar_col,\n        y="LocationDesc",\n        orientation="h",\n        title=f"Top {top_n} States by {bar_metric}",\n        labels={bar_col: bar_metric, "LocationDesc": "State"},\n        hover_data=["LocationAbbr", "Mean_State_Revenue", "Avg_Annual_SAM", "Average_Cancer_Deaths"]\n    )\n\n    fig_bar.update_traces(marker_color="#3B82F6")\n    fig_bar.update_layout(\n        template="plotly_white",\n        paper_bgcolor="white",\n        plot_bgcolor="white",\n        font=dict(color="#111827"),\n        title_font_size=22,\n        margin=dict(l=20, r=20, t=60, b=20),\n        height=550\n    )\n\n    st.plotly_chart(fig_bar, width="stretch")\n\nwith tab_scatter:\n    st.header("State Comparison and Correlation")\n    st.markdown("This scatter plot compares two selected metrics across states.")\n\n    col_x, col_y = st.columns(2)\n    with col_x:\n        x_metric = st.selectbox("Select X-axis metric:", list(METRIC_MAPPING.keys()), index=0)\n    with col_y:\n        y_metric = st.selectbox("Select Y-axis metric:", list(METRIC_MAPPING.keys()), index=1)\n\n    x_col = METRIC_MAPPING[x_metric]\n    y_col = METRIC_MAPPING[y_metric]\n\n    if x_col == y_col:\n        st.info("Please select two different metrics for the X-axis and Y-axis to create a meaningful scatter plot.")\n    else:\n        correlation = final[x_col].corr(final[y_col])\n        st.write(f"**Pearson correlation:** {correlation:.3f}")\n\n        try:\n            fig_scatter = px.scatter(\n                final,\n                x=x_col,\n                y=y_col,\n                text="LocationAbbr",\n                hover_name="LocationDesc",\n                trendline="ols",\n                title=f"{y_metric} vs. {x_metric}",\n                labels={x_col: x_metric, y_col: y_metric}\n            )\n        except Exception:\n            fig_scatter = px.scatter(\n                final,\n                x=x_col,\n                y=y_col,\n                text="LocationAbbr",\n                hover_name="LocationDesc",\n                title=f"{y_metric} vs. {x_metric}",\n                labels={x_col: x_metric, y_col: y_metric}\n            )\n            st.info("Install statsmodels to show the trendline: python3 -m pip install statsmodels")\n\n        fig_scatter.update_traces(textposition="top center")\n        fig_scatter.update_layout(\n            template="plotly_white",\n            paper_bgcolor="white",\n            plot_bgcolor="white",\n            font=dict(color="#111827"),\n            title_font_size=22,\n            margin=dict(l=20, r=20, t=60, b=20),\n            height=550\n        )\n\n        st.plotly_chart(fig_scatter, width="stretch")\n\nwith tab_heatmap:\n    st.header("Correlation Heatmap")\n    st.markdown("This heatmap shows how strongly the project metrics are related to each other.")\n\n    corr_cols = list(METRIC_MAPPING.values())\n    corr_matrix = final[corr_cols].corr().rename(index=DISPLAY_LABELS, columns=DISPLAY_LABELS)\n\n    fig_heatmap = px.imshow(\n        corr_matrix,\n        text_auto=".2f",\n        color_continuous_scale="RdBu_r",\n        zmin=-1,\n        zmax=1,\n        title="Correlation Heatmap of Project Metrics"\n    )\n\n    fig_heatmap.update_layout(\n        template="plotly_white",\n        paper_bgcolor="white",\n        plot_bgcolor="white",\n        font=dict(color="#111827"),\n        title_font_size=22,\n        margin=dict(l=20, r=20, t=60, b=20),\n        height=650\n    )\n\n    st.plotly_chart(fig_heatmap, width="stretch")\n\nwith tab_data:\n    st.header("Data Tables")\n    st.markdown("These tables show the cleaned datasets used to build the dashboard.")\n\n    with st.expander("Cigarette Tax Revenue Data"):\n        st.markdown("Average cigarette tax revenue by state from 2005 to 2009.")\n        st.dataframe(revenue_avg, width="stretch")\n\n    with st.expander("Smoking-Attributable Mortality Data"):\n        st.markdown("Estimated average annual smoking-attributable deaths by state.")\n        st.dataframe(sam_avg, width="stretch")\n\n    with st.expander("Respiratory Cancer Deaths Data"):\n        st.markdown("Lung and respiratory cancer deaths by state.")\n        st.dataframe(cancer_deaths, width="stretch")\n\n    with st.expander("Final Merged Dataset"):\n        st.markdown("The final merged dataset used for all maps, charts, and calculations.")\n        st.dataframe(final, width="stretch")\n'

Path("app.py").write_text(APP_CODE, encoding="utf-8")
print("Created app.py. Run it from Terminal with: streamlit run app.py")
