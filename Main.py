import streamlit as st 
import pandas as pd
import ast
import plotly.express as px

# import data frame
female_df = pd.read_csv("data/cleaned_female_data.csv")
neutral_df = pd.read_csv("data/cleaned_neutral_data.csv")

# ---------- PAGE SET-UP ---------- #

st.set_page_config(layout='wide')
st.title("PubMed Publication Analysis")

st.write("Application by: Lauren Latimer | [Github](https://github.com/llatimer031/Data-Feminism-App#) ")

st.header("**Goal:** Understand who is conducting research in women's health.")

st.markdown("""Using PubMed's advanced search, articles containing the following MeSH terms were filtered:
- Dysmenorrhea/Diagnosis
- Endometriosis/Diagnosis
- Polycystic Ovary Syndrome/Diagnosis
- Postpartum Hemorrhage/Diagnosis \n
The metadata for studies conducted on human subjects and published between 2000-2025 were further filtered and can be found [here](https://github.com/llatimer031/Data-Feminism-App/blob/main/data/pubmed-dysmenorrh-set.nbib).
The following analysis will be performed on a cleaned, filtered [CSV](https://github.com/llatimer031/Data-Feminism-App/blob/main/data/cleaned_female_data.csv).
""")

st.divider()

# ---------- SIDEBAR ---------- #
st.sidebar.title("DATA OPTIONS")
st.sidebar.write("Use this sidebar to choose a topic to explore in women's health and add additional filters.")

st.sidebar.divider()

st.sidebar.header("Subset the Data:")

mesh = st.sidebar.selectbox("Select a keyword to filter the publications by:", ("Endometriosis", "Dysmenorrhea", "Polycystic Ovary Syndrome", "Postpartum Hemorrhage"))

# convert string-formatted lists to actual lists
female_df["MeSH_List"] = female_df["MeSH_Clean"].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])

# filter rows where mesh is in the MeSH list
filtered_df = female_df[female_df["MeSH_List"].apply(lambda x: mesh in x if isinstance(x, list) else False)]
st.sidebar.write(f"Number of matching articles: {len(filtered_df)}")

# ----- optional filters ----- #

st.sidebar.divider()
st.sidebar.header("Additional Filter Options:")

# extract min and max dates
min_year = female_df["Year"].min()
max_year = female_df["Year"].max()

if st.sidebar.toggle("Date of Publication"):
    date_range = st.sidebar.slider("Select a year range:", min_value=min_year, max_value=max_year, value=(min_year, max_year), step=1)
    filtered_df = filtered_df[(filtered_df["Year"] >= date_range[0]) & (filtered_df["Year"] <= date_range[1])]
    st.sidebar.write(f"Number of matching articles: {len(filtered_df)}")
    
    # filter neutral dataset for date as well
    neutral_df = neutral_df[(neutral_df["Year"] >= date_range[0]) & (neutral_df["Year"] <= date_range[1])]
    
if st.sidebar.toggle("Country of Publication"):
    # create unique list of country values
    country_options = sorted(filtered_df["Country"].dropna().unique())
    # set default option to United States
    if "United States" in country_options:
        default_index = country_options.index("United States")
    else:
        default_index = 0  # fallback
    # allow user to select country of choice
    country = st.sidebar.selectbox("Select a country:", country_options, index=default_index)

    # filter df according to chosen country
    filtered_df = filtered_df[filtered_df["Country"] == country]
    st.sidebar.write(f"Number of matching articles: {len(filtered_df)}")
    
    # filter neutral dataset by country
    if country in neutral_df["Country"].unique():
        neutral_df = neutral_df[neutral_df["Country"] == country]
    else:
        neutral_df = None

    
# ---------- MAIN DISPLAY ---------- #

st.header("Part 1: Explore Publications in a Women's Health Topic")
st.write(f"**Current topic:** {mesh}")

st.subheader("Preview of the filtered dataset:")
st.dataframe(filtered_df.head(5))

# ----- publications per year ----- #

# Count number of publications per year
year_counts =filtered_df["Year"].value_counts().sort_index()
# Display the bar chart
st.subheader("Number of publications per year:")
st.bar_chart(year_counts)

# ----- publications by author gender ----- #
st.subheader("Gender Distribution Among Authors:")

# simplify predicted genders to three categories
def simplify_gender(gender):
    if gender in ['male', 'mostly_male']:
        return 'male'
    elif gender in ['female', 'mostly_female']:
        return 'female'
    elif gender == 'andy':
        return 'andy'
    else:
        return 'unknown'

filtered_df["Predicted_First_Gender"] = filtered_df["Predicted_First_Gender"].apply(simplify_gender)
filtered_df["Predicted_Last_Gender"] = filtered_df["Predicted_Last_Gender"].apply(simplify_gender)

# create pie charts to display gender distribution of first and last authors
st.markdown(f"""
##### Gender distribution in articles regarding the diagnosis of {mesh}.
""")

# create two Streamlit columns
col1, col2 = st.columns(2)

# define color mapping
gender_colors = {
    "male": "#0068c9",      # blue
    "female": "#f5918b",    # pink
    "andy": "#d2ccc5",      # gray
    "unknown": "#f4f1ee"    # light gray
}

# First Author Pie Chart
with col1:
    first_gender_counts = filtered_df["Predicted_First_Gender"].value_counts().reset_index()
    first_gender_counts.columns = ["Gender", "Count"]
    
    fig1 = px.pie(
        first_gender_counts,
        names="Gender",
        values="Count",
        title="First Author Gender",
        color="Gender", 
        color_discrete_map=gender_colors,
        category_orders={"Gender": ["female", "male", "andy", "unknown"]}
    )
    st.plotly_chart(fig1)

# Last Author Pie Chart
with col2:
    last_gender_counts = filtered_df["Predicted_Last_Gender"].value_counts().reset_index()
    last_gender_counts.columns = ["Gender", "Count"]

    fig2 = px.pie(
        last_gender_counts,
        names="Gender",
        values="Count",
        title="Last Author Gender",
        color="Gender",  
        color_discrete_map=gender_colors,
        category_orders={"Gender": ["female", "male", "andy", "unknown"]}
    )
    st.plotly_chart(fig2)

# allow user to click toggle for more information on the gender guesser
if st.toggle("Click here for more information on the gender predictor."):
    st.write("**Python Package:** [gender_guesser.detector](https://pypi.org/project/gender-guesser/)")
    st.markdown("""
    **Information:** This package uses a database of gender-labeled names to predict the likelihood that a first name is male or female. \n
    **Key:**

    - **Female**: contains observations predicted as `female` or `mostly_female`
    - **Male**: contains observations predicted as `male` or `mostly_male`
    - **Andy (androgynous)**: contains observations that were equally male and female in the training database
    - **Unknown**: contains observations that were not found in the training database
    """)

    
st.markdown("""
<small><i>Note: The gender displayed in these graphs are predictions based on a training dataset. 
Predictions of this sort can portray their own biases according to the training data, especially if the data does not equally represent different countries or cultures. 
**As such, these predictions should *not* be used as concrete evidence, but rather as a means of exploratory analysis that may influence the direction of further research.**</i></small>
""", unsafe_allow_html=True)

st.divider()

# ----- NEUTRAL CROSS REFERENCE ----- #
st.header("Part 2: Comparison to Gender-Neutral Topic:")
st.markdown("""
To provide a baseline for gender distribution in medical research, articles with the following main MeSH term were downloaded from PubMed:
- Cardiac Arrest/Diagnosis

While the previous MeSH terms were conditions specific to the female sex, heart disease is the leading cause of death for both **men and women**.

<small><i>Note: As with the previous dataset, data was filtered to human subjects and publications between 2000–2025. Find the original and cleaned datasets [here](https://github.com/llatimer031/Data-Feminism-App/tree/main/data).</i></small>
""", unsafe_allow_html=True)

# plot pie charts of gender distribution
st.subheader("Gender Distribution Among Authors:")
st.markdown(f"""
##### Gender distribution in articles regarding the diagnosis of cardiac arrest.
""")

if neutral_df is not None:
    # simplify predicted genders in cardiac data set
    neutral_df["Predicted_First_Gender"] = neutral_df["Predicted_First_Gender"].apply(simplify_gender)
    neutral_df["Predicted_Last_Gender"] = neutral_df["Predicted_Last_Gender"].apply(simplify_gender)

    # create two Streamlit columns
    col3, col4 = st.columns(2)

    # First Author Pie Chart
    with col3:
        first_gender_counts_n = neutral_df["Predicted_First_Gender"].value_counts().reset_index()
        first_gender_counts_n.columns = ["Gender", "Count"]
        
        fig1 = px.pie(
            first_gender_counts_n,
            names="Gender",
            values="Count",
            title="First Author Gender",
            color="Gender", 
            color_discrete_map=gender_colors,
            category_orders={"Gender": ["female", "male", "andy", "unknown"]}
        )
        st.plotly_chart(fig1)

    # Last Author Pie Chart
    with col4:
        last_gender_counts_n = neutral_df["Predicted_Last_Gender"].value_counts().reset_index()
        last_gender_counts_n.columns = ["Gender", "Count"]

        fig2 = px.pie(
            last_gender_counts_n,
            names="Gender",
            values="Count",
            title="Last Author Gender",
            color="Gender",  
            color_discrete_map=gender_colors,
            category_orders={"Gender": ["female", "male", "andy", "unknown"]}
        )
        st.plotly_chart(fig2)
    
else:
    st.error("No publications for this country and/or time range.")
    
st.divider()

# ----- ANALYSIS ----- #
st.header("Part 3: Analysis Questions")

st.write("**How has women's health research changed over the years?**")
st.write("For the topics explored in this project, there appears to be a gradual increase in research being published from the start of the 21st century to now.")

st.write("**Who is performing this research?**")
st.markdown("""
While there is still a degree of uncertainty due to a probability-based gender guesser,
the distribution of author gender in women's health fields appears to lean heavily female,
especially when compared to a more neutral condition such as heart disease. 
This is especially true of articles published in the United States.
""")

st.write("**Where do we go from here?**")
st.markdown("""
Though there are obvious limitations to these findings, 
they suggest that in regards to making the healthcare industry more equitable,
there may be benefits to investigating questions such as
whether women-led teams (who appear to lead female-based research) receive equal funding,
how to increase male involvement in women's health fields, etc. 
""")