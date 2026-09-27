import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import base64


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SCC Beneficiary Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# API CONFIGURATION
# ============================================================

API_URL = (
    "https://somcc.redrosecps.com/"
    "externalapi/customQuery/queryToJson"
    "?queryName=BeneficiaryDetailsV2"
)


# ============================================================
# LOAD DATA FROM API
# ============================================================

@st.cache_data(
    ttl=3600,
    show_spinner="Loading beneficiary data from RedRose API..."
)
def load_data():

    # --------------------------------------------------------
    # Read credentials from Streamlit secrets
    # --------------------------------------------------------

    username = st.secrets["API_USERNAME"]
    password = st.secrets["API_PASSWORD"]

    # --------------------------------------------------------
    # Create Basic Authentication
    # This follows the same approach as your R code
    # --------------------------------------------------------

    credentials = f"{username}:{password}"

    encoded_credentials = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Accept": "application/json"
    }

    # --------------------------------------------------------
    # API Request
    # --------------------------------------------------------

    response = requests.get(
        API_URL,
        headers=headers,
        timeout=300
    )

    # --------------------------------------------------------
    # Check response
    # --------------------------------------------------------

    if response.status_code != 200:

        raise Exception(
            f"API request failed with HTTP "
            f"{response.status_code}"
        )

    # --------------------------------------------------------
    # Convert response to JSON
    # --------------------------------------------------------

    data = response.json()

    # --------------------------------------------------------
    # Convert JSON to DataFrame
    # --------------------------------------------------------

    df = pd.json_normalize(data)

    # --------------------------------------------------------
    # Clean column names
    # --------------------------------------------------------

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Registration Date
    # --------------------------------------------------------

    if "Registration Date" in df.columns:

        df["Registration Date"] = pd.to_datetime(
            df["Registration Date"],
            format="%d-%m-%Y %H:%M:%S",
            errors="coerce"
        )

    # --------------------------------------------------------
    # Age
    # --------------------------------------------------------

    if "Age" in df.columns:

        df["Age"] = pd.to_numeric(
            df["Age"],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Latitude
    # --------------------------------------------------------

    if "Latitude" in df.columns:

        df["Latitude"] = pd.to_numeric(
            df["Latitude"],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Longitude
    # --------------------------------------------------------

    if "Longitude" in df.columns:

        df["Longitude"] = pd.to_numeric(
            df["Longitude"],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Remove Archived records
    #
    # Your API column is "Archived"
    # --------------------------------------------------------

    if "Archived" in df.columns:

        archived_clean = (
            df["Archived"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        df = df[
            ~archived_clean.isin(
                [
                    "yes",
                    "true",
                    "1"
                ]
            )
        ]

    return df


# ============================================================
# LOAD DATA
# ============================================================

try:

    df = load_data()

except Exception as e:

    st.error(
        "Unable to load data from the API."
    )

    st.error(str(e))

    st.info(
        "Please check the API username/password "
        "in .streamlit/secrets.toml."
    )

    st.stop()


# ============================================================
# HEADER
# ============================================================

st.title("📊 SCC Beneficiary Dashboard")

st.caption(
    "Somali Cash Consortium — Beneficiary Registration Overview"
)

st.divider()


# ============================================================
# DATA INFORMATION
# ============================================================

total_api_records = len(df)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🔎 Dashboard Filters")


# ============================================================
# HELPER FUNCTION
# ============================================================

def get_options(column):

    if column not in df.columns:

        return []

    return sorted(
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )


# ============================================================
# FEDERAL STATE FILTER
# ============================================================

states = get_options(
    "ADM L1"
)

selected_states = st.sidebar.multiselect(
    "ADM L1",
    states
)


# ============================================================
# REGION FILTER
# ============================================================

regions = get_options(
    "ADM L2"
)

selected_regions = st.sidebar.multiselect(
    "ADM L2",
    regions
)


# ============================================================
# DISTRICT FILTER
# ============================================================

districts = get_options(
    "ADM L3"
)

selected_districts = st.sidebar.multiselect(
    "ADM L3",
    districts
)


# ============================================================
# AGENCY FILTER
# ============================================================

agencies = get_options(
    "Agency"
)

selected_agencies = st.sidebar.multiselect(
    "Agency",
    agencies
)


# ============================================================
# GENDER FILTER
# ============================================================

genders = get_options(
    "Gender"
)

selected_gender = st.sidebar.multiselect(
    "Gender",
    genders
)


# ============================================================
# STATUS FILTER
# ============================================================

statuses = get_options(
    "Status"
)

selected_status = st.sidebar.multiselect(
    "Status",
    statuses
)


# ============================================================
# TYPE FILTER
# ============================================================

types = get_options(
    "Type"
)

selected_types = st.sidebar.multiselect(
    "Type",
    types
)


# ============================================================
# CASeload FILTER
# ============================================================

caseloads = get_options(
    "Caseload"
)

selected_caseloads = st.sidebar.multiselect(
    "Caseload",
    caseloads
)


# ============================================================
# DATE FILTER
# ============================================================

date_range = None

if "Registration Date" in df.columns:

    valid_dates = (
        df["Registration Date"]
        .dropna()
    )

    if len(valid_dates) > 0:

        min_date = valid_dates.min().date()

        max_date = valid_dates.max().date()

        date_range = st.sidebar.date_input(
            "Registration Date",
            value=(
                min_date,
                max_date
            ),
            min_value=min_date,
            max_value=max_date
        )


# ============================================================
# RESET FILTER BUTTON
# ============================================================

st.sidebar.divider()

if st.sidebar.button(
    "🔄 Clear Filters"
):

    st.rerun()


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()


# ------------------------------------------------------------
# Federal State
# ------------------------------------------------------------

if selected_states:

    filtered_df = filtered_df[
        filtered_df[
            "ADM L1"
        ]
        .astype(str)
        .isin(selected_states)
    ]


# ------------------------------------------------------------
# Region
# ------------------------------------------------------------

if selected_regions:

    filtered_df = filtered_df[
        filtered_df["ADM L2"]
        .astype(str)
        .isin(selected_regions)
    ]


# ------------------------------------------------------------
# District
# ------------------------------------------------------------

if selected_districts:

    filtered_df = filtered_df[
        filtered_df["ADM L3"]
        .astype(str)
        .isin(selected_districts)
    ]


# ------------------------------------------------------------
# Agency
# ------------------------------------------------------------

if selected_agencies:

    filtered_df = filtered_df[
        filtered_df["Agency"]
        .astype(str)
        .isin(selected_agencies)
    ]


# ------------------------------------------------------------
# Gender
# ------------------------------------------------------------

if selected_gender:

    filtered_df = filtered_df[
        filtered_df["Gender"]
        .astype(str)
        .isin(selected_gender)
    ]


# ------------------------------------------------------------
# Status
# ------------------------------------------------------------

if selected_status:

    filtered_df = filtered_df[
        filtered_df["Status"]
        .astype(str)
        .isin(selected_status)
    ]


# ------------------------------------------------------------
# Type
# ------------------------------------------------------------

if selected_types:

    filtered_df = filtered_df[
        filtered_df["Type"]
        .astype(str)
        .isin(selected_types)
    ]


# ------------------------------------------------------------
# Caseload
# ------------------------------------------------------------

if selected_caseloads:

    filtered_df = filtered_df[
        filtered_df["Caseload"]
        .astype(str)
        .isin(selected_caseloads)
    ]


# ------------------------------------------------------------
# Registration Date
# ------------------------------------------------------------

if (
    date_range
    and len(date_range) == 2
    and "Registration Date" in filtered_df.columns
):

    start_date = pd.Timestamp(
        date_range[0]
    )

    end_date = (
        pd.Timestamp(date_range[1])
        + pd.Timedelta(days=1)
    )

    filtered_df = filtered_df[
        (
            filtered_df["Registration Date"]
            >= start_date
        )
        &
        (
            filtered_df["Registration Date"]
            < end_date
        )
    ]


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_beneficiaries = len(
    filtered_df
)


total_agencies = (
    filtered_df["Agency"].nunique()
    if "Agency" in filtered_df.columns
    else 0
)


total_districts = (
    filtered_df["ADM L3"].nunique()
    if "ADM L3" in filtered_df.columns
    else 0
)


total_caseloads = (
    filtered_df["Caseload"].nunique()
    if "Caseload" in filtered_df.columns
    else 0
)


# ============================================================
# KPI SECTION
# ============================================================

st.subheader("📌 Key Indicators")


k1, k2, k3, k4 = st.columns(4)


with k1:

    st.metric(
        "Beneficiaries",
        f"{total_beneficiaries:,}"
    )


with k2:

    st.metric(
        "Agencies",
        f"{total_agencies:,}"
    )


with k3:

    st.metric(
        "ADM L3",
        f"{total_districts:,}"
    )


with k4:

    st.metric(
        "Caseloads",
        f"{total_caseloads:,}"
    )


# ============================================================
# SECOND KPI ROW
# ============================================================

st.markdown("### Demographic Overview")


d1, d2, d3, d4 = st.columns(4)


# ------------------------------------------------------------
# Female
# ------------------------------------------------------------

if "Gender" in filtered_df.columns:

    gender_clean = (
        filtered_df["Gender"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    female_count = (
        gender_clean == "female"
    ).sum()

    male_count = (
        gender_clean == "male"
    ).sum()

else:

    female_count = 0

    male_count = 0


with d1:

    st.metric(
        "Female",
        f"{female_count:,}"
    )


with d2:

    st.metric(
        "Male",
        f"{male_count:,}"
    )


# ------------------------------------------------------------
# Average Age
# ------------------------------------------------------------

if "Age" in filtered_df.columns:

    average_age = (
        filtered_df["Age"]
        .mean()
    )

else:

    average_age = 0


with d3:

    st.metric(
        "Average Age",
        f"{average_age:.1f}"
    )


# ------------------------------------------------------------
# Records shown
# ------------------------------------------------------------

with d4:

    st.metric(
        "Filtered Records",
        f"{len(filtered_df):,}"
    )


# ============================================================
# GENDER AND AGE
# ============================================================

st.divider()

col1, col2 = st.columns(2)


# ============================================================
# GENDER CHART
# ============================================================

if "Gender" in filtered_df.columns:

    gender_data = (
        filtered_df
        .assign(
            Gender=
            filtered_df["Gender"]
            .astype(str)
            .str.strip()
            .str.title()
        )
        .groupby("Gender")
        .size()
        .reset_index(
            name="Beneficiaries"
        )
    )

    with col1:

        st.subheader(
            "Gender Distribution"
        )

        fig = px.pie(
            gender_data,
            names="Gender",
            values="Beneficiaries",
            hole=0.45
        )

        fig.update_layout(
            height=420
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# AGE GROUP
# ============================================================

if "Age" in filtered_df.columns:

    age_df = filtered_df.copy()

    age_df["Age Group"] = pd.cut(
        age_df["Age"],
        bins=[
            -1,
            4,
            17,
            59,
            200
        ],
        labels=[
            "Under 5",
            "5–17",
            "18–59",
            "60+"
        ]
    )

    age_data = (
        age_df
        .groupby(
            "Age Group",
            observed=False
        )
        .size()
        .reset_index(
            name="Beneficiaries"
        )
    )

    with col2:

        st.subheader(
            "Age Group Distribution"
        )

        fig = px.bar(
            age_data,
            x="Age Group",
            y="Beneficiaries",
            text="Beneficiaries"
        )

        fig.update_layout(
            height=420
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# BENEFICIARIES BY FEDERAL STATE
# ============================================================

if "Federal State Member" in filtered_df.columns:

    state_data = (
        filtered_df
        .groupby(
            "ADM L1"
        )
        .size()
        .reset_index(
            name="Beneficiaries"
        )
        .sort_values(
            "Beneficiaries",
            ascending=False
        )
    )

    st.subheader(
        "Beneficiaries by Federal State Member"
    )

    fig = px.bar(
        state_data,
        x="ADM L1",
        y="Beneficiaries",
        text="Beneficiaries"
    )

    fig.update_layout(
        height=450,
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# BENEFICIARIES BY DISTRICT
# ============================================================

if "District" in filtered_df.columns:

    district_data = (
        filtered_df
        .groupby("ADM L3")
        .size()
        .reset_index(
            name="Beneficiaries"
        )
        .sort_values(
            "Beneficiaries",
            ascending=False
        )
    )

    st.subheader(
        "Beneficiaries by District"
    )

    fig = px.bar(
        district_data,
        x="Beneficiaries",
        y="ADM L3",
        orientation="h",
        text="Beneficiaries"
    )

    fig.update_layout(
        height=700,
        yaxis={
            "categoryorder":
            "total ascending"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# FCS AND LCSI
# ============================================================

st.divider()

col1, col2 = st.columns(2)


# ============================================================
# FCS
# ============================================================

if "FCS_category" in filtered_df.columns:

    fcs_data = (
        filtered_df
        .groupby(
            "FCS_category"
        )
        .size()
        .reset_index(
            name="Beneficiaries"
        )
        .sort_values(
            "Beneficiaries",
            ascending=False
        )
    )

    with col1:

        st.subheader(
            "🍽️ Food Consumption Score"
        )

        fig = px.bar(
            fcs_data,
            x="FCS_category",
            y="Beneficiaries",
            text="Beneficiaries"
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# LCSI
# ============================================================

if "LCSI_category" in filtered_df.columns:

    lcsi_data = (
        filtered_df
        .groupby(
            "LCSI_category"
        )
        .size()
        .reset_index(
            name="Beneficiaries"
        )
        .sort_values(
            "Beneficiaries",
            ascending=False
        )
    )

    with col2:

        st.subheader(
            "🏠 Livelihood Coping Strategy"
        )

        fig = px.bar(
            lcsi_data,
            x="LCSI_category",
            y="Beneficiaries",
            text="Beneficiaries"
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# STATUS
# ============================================================

if "Status" in filtered_df.columns:

    status_data = (
        filtered_df
        .groupby(
            "Status"
        )
        .size()
        .reset_index(
            name="Beneficiaries"
        )
        .sort_values(
            "Beneficiaries",
            ascending=False
        )
    )

    st.subheader(
        "Beneficiaries by Status"
    )

    fig = px.bar(
        status_data,
        x="Status",
        y="Beneficiaries",
        text="Beneficiaries"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# REGISTRATION TREND
# ============================================================

if "Registration Date" in filtered_df.columns:

    trend_df = (
        filtered_df
        .dropna(
            subset=[
                "Registration Date"
            ]
        )
        .copy()
    )

    if len(trend_df) > 0:

        trend_df["Month"] = (
            trend_df[
                "Registration Date"
            ]
            .dt.to_period("M")
            .astype(str)
        )

        trend_data = (
            trend_df
            .groupby("Month")
            .size()
            .reset_index(
                name="Beneficiaries"
            )
        )

        st.subheader(
            "📅 Monthly Registration Trend"
        )

        fig = px.line(
            trend_data,
            x="Month",
            y="Beneficiaries",
            markers=True
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# MAP
# ============================================================

if (
    "Latitude" in filtered_df.columns
    and "Longitude" in filtered_df.columns
):

    map_df = filtered_df.copy()

    map_df = map_df.dropna(
        subset=[
            "Latitude",
            "Longitude"
        ]
    )

    st.divider()

    st.subheader(
        "🗺️ Beneficiary Registration Locations"
    )

    if len(map_df) > 0:

        # ----------------------------------------------------
        # Important:
        # Don't send 400,000 points to the browser.
        # Maximum 5,000 points are displayed.
        # ----------------------------------------------------

        map_display = map_df.sample(
            n=min(
                5000,
                len(map_df)
            ),
            random_state=42
        )

        hover_columns = []

        for column in [
            "Region",
            "District",
            "Gender",
            "Age",
            "FCS_category",
            "LCSI_category"
        ]:

            if column in map_display.columns:

                hover_columns.append(
                    column
                )

        fig = px.scatter_mapbox(
            map_display,
            lat="Latitude",
            lon="Longitude",
            hover_name="District"
            if "District"
            in map_display.columns
            else None,
            hover_data=hover_columns,
            zoom=5,
            height=650
        )

        fig.update_layout(
            mapbox_style="open-street-map",
            margin=dict(
                r=0,
                t=0,
                l=0,
                b=0
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.caption(
            f"Displaying a maximum of 5,000 "
            f"locations from {len(map_df):,} "
            f"records with valid coordinates."
        )

    else:

        st.info(
            "No valid latitude/longitude "
            "coordinates are available "
            "for the selected filters."
        )


# ============================================================
# DATA TABLE
# ============================================================

st.divider()

st.subheader(
    "📋 Beneficiary Data"
)

st.caption(
    f"{len(filtered_df):,} records match "
    "the selected filters."
)


# ------------------------------------------------------------
# Public-safe columns
#
# Beneficiary ID and exact location coordinates
# are intentionally excluded from the public table.
# ------------------------------------------------------------

public_columns = [
    "Type",
    "FCS_category",
    "LCSI_category",
    "Agency",
    "ADM L1",
    "ADM L2",
    "ADM L3",
    "Registration Date",
    "Age",
    "Gender",
    "Caseload",
    "Status"
]


display_columns = [
    column
    for column in public_columns
    if column in filtered_df.columns
]


display_df = filtered_df[
    display_columns
].copy()


# ------------------------------------------------------------
# Display first 5,000 records
# ------------------------------------------------------------

st.dataframe(
    display_df.head(5000),
    use_container_width=True,
    height=550
)


# ============================================================
# DOWNLOAD FILTERED DATA
# ============================================================

csv = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Filtered Data",
    data=csv,
    file_name="filtered_beneficiaries.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "SCC Beneficiary Dashboard | "
    "Powered by RedRose API"
)