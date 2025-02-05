import streamlit as st
import pandas as pd
import altair as alt
from collections import Counter
import re
import requests
from streamlit_autorefresh import st_autorefresh

# Auto refresh every 20 seconds
st_autorefresh(interval=20000, key="data_refresh")

# API endpoint URL
api_url = "http://127.0.0.1:5000/"

# Initialize df to handle case where API data is missing
df = None

# Fetch data from the API
try:
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        
        if not data:
            st.error("No data received from the API.")
            st.stop()  # Stop execution if no data
        
        # Create DataFrame from API data
        df = pd.DataFrame(data)
        
        # Check if 'date' column exists in the data
        if 'date' not in df.columns:
            st.error("The 'date' column is missing from the data.")
            st.stop()

        # Convert the 'date' column to datetime format
        df["date"] = pd.to_datetime(df["date"])
    else:
        st.error(f"Failed to fetch data from the API. Status code: {response.status_code}")
        st.stop()
except Exception as e:
    st.error(f"An error occurred while fetching the data: {str(e)}")
    st.stop()

# Proceed only if df is successfully defined
if df is not None:
    # Streamlit main page
    st.title("📊 Sentiment Analysis Report")

    # Sidebar filters
    st.sidebar.header("Filter Options")

    # Check if the column exists before creating filters
    if "source" in df.columns:
        source_filter = st.sidebar.multiselect(
            "Select Source(s):", options=df["source"].unique(), default=df["source"].unique()
        )
    else:
        st.error("The 'source' column is missing from the data.")
        st.stop()

    if "sentiment" in df.columns:
        sentiment_filter = st.sidebar.multiselect(
            "Select Sentiment(s):",
            options=df["sentiment"].unique(),
            default=df["sentiment"].unique(),
        )
    else:
        st.error("The 'sentiment' column is missing from the data.")
        st.stop()

    if "topic" in df.columns:
        topic_filter = st.sidebar.multiselect(
            "Select Topic(s):",
            options=df["topic"].unique(),
            default=df["topic"].unique(),
        )
    else:
        st.error("The 'topic' column is missing from the data.")
        st.stop()

    if "date" in df.columns:
        date_filter = st.sidebar.date_input(
            "Select Date Range:",
            value=[pd.to_datetime(df["date"].min()), pd.to_datetime(df["date"].max())],
        )
    else:
        st.error("The 'date' column is missing from the data.")
        st.stop()

    # Apply filters
    filtered_df = df[ 
        (df["topic"].isin(topic_filter)) 
        & (df["source"].isin(source_filter)) 
        & (df["sentiment"].isin(sentiment_filter)) 
        & (df["date"] >= pd.to_datetime(date_filter[0])) 
        & (df["date"] <= pd.to_datetime(date_filter[1])) 
    ]

    # Display summary cards
    st.header("Summary Statistics")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="📝 Number of Comments", value=len(filtered_df))

    with col2:
        st.metric(label="📌 Number of Topics", value=filtered_df["topic"].nunique())

    with col3:
        st.metric(label="🔗 Number of Sources", value=filtered_df["source"].nunique())

    # Display filtered data
    st.header("Filtered Data")
    st.dataframe(filtered_df)

    # Display sentiment distribution chart and source distribution chart side by side
    st.header("Sentiment and Source Distribution")
    col1, col2 = st.columns(2)

    with col1:
        sentiment_chart = (
            alt.Chart(filtered_df)
            .mark_bar()
            .encode(x="sentiment", y="count()", color="sentiment")
            .properties(width=400, height=300)
        )
        st.altair_chart(sentiment_chart)

    with col2:
        source_chart = (
            alt.Chart(filtered_df)
            .mark_bar()
            .encode(x="source", y="count()", color="source")
            .properties(width=400, height=300)
        )
        st.altair_chart(source_chart)

    # Line chart for sentiment change over time
    st.header("Sentiment Change Over Time")

    # Calculate percentage of sentiments for each source over time
    sentiment_counts = (
        filtered_df.groupby(["date", "source", "sentiment"]).size().unstack(fill_value=0)
    )
    sentiment_counts["total"] = sentiment_counts.sum(axis=1)
    sentiment_counts["positive_percentage"] = (
        sentiment_counts["POSITIVE"] / sentiment_counts["total"] * 100
    )

    sentiment_counts.reset_index(inplace=True)
    sentiment_counts_melted = pd.melt(
        sentiment_counts, id_vars=["date", "source"], value_vars=["positive_percentage"]
    )

    line_chart = (
        alt.Chart(sentiment_counts_melted)
        .mark_line()
        .encode(
            x="date:T",
            y="value:Q",
            color="source:N",
            tooltip=["date:T", "source:N", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(width=800, height=500)
    )

    st.altair_chart(line_chart)

    # Display most frequently used words in comments
    st.header("Most Frequently Used Words")

    def get_most_common_words(comments, num_words=10):
        all_comments = " ".join(comments)
        all_comments = re.sub(r"[^\w\s]", "", all_comments).lower()
        words = all_comments.split()
        most_common_words = Counter(words).most_common(num_words)
        return pd.DataFrame(most_common_words, columns=["word", "count"])

    # Top 5 words by topic
    st.header("Top 5 Words by Topic")
    topics = filtered_df['topic'].unique()
    for topic in topics:
        st.subheader(f"Topic: {topic}")
        topic_df = filtered_df[filtered_df['topic'] == topic]
        most_common_words_df = get_most_common_words(topic_df["cleaned_comment"], num_words=5)
        
        word_chart = (
            alt.Chart(most_common_words_df)
            .mark_bar()
            .encode(x="count", y=alt.Y("word", sort="-x"), color="count")
            .properties(width=600, height=400)
        )
        st.altair_chart(word_chart)

    # Add text input for searching comments
    st.header("Search Comments")
    search_term = st.text_input("Enter search term:")
    if search_term:
        search_results = filtered_df[
            filtered_df["comment"].str.contains(search_term, case=False)
        ]
        st.dataframe(search_results)
    else:
        st.write("Enter a search term to filter comments.")

    # Display raw data
    st.header("Raw Data")
    st.write(df)
