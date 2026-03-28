from unittest import case

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

#Load Dataset
movie_df = pd.read_csv("movie_database.csv")
user_df = pd.read_csv("users.csv")
stream_activity_df = pd.read_csv("WatchHistory&Rating.csv")

#allow user login
credentials = dict(zip(user_df['user_id'], zip(user_df['password'], user_df['name'], user_df['role'])))


#Sidebar and User
st.sidebar.title("🎥🍿 Netflix")
st.sidebar.markdown("---")

#---------------------------------------------------------
# Function to Recommend Top 3 Movie based on Watch History
#---------------------------------------------------------

def recommend_movie(user, movie_df, stream_activity_df):
    user_movie_history = stream_activity_df[(stream_activity_df['user_id'] == user) & (stream_activity_df['watched'] == 1)] # get movies with "1" indicating watched

    if user_movie_history.empty:
        return pd.DataFrame()

    watched_titles = user_movie_history['title'].tolist()
    watched_movies = movie_df[movie_df['Title'].isin(watched_titles)] #get movies from the movie database
    genres = set()   #get genres of the movies watched by users
    for g in watched_movies['Genre']:
        for item in g.split(";"):
            genres.add(item.strip())
    suggest_candidates = movie_df[~movie_df['Title'].isin(watched_titles)]

    def match_genre(genre_str):
        movie_genres = [x.strip() for x in genre_str.split(";")]
        return any(g in genres for g in movie_genres)
    recommendation = suggest_candidates[suggest_candidates['Genre'].apply(match_genre)]

    recommendation = recommendation.sort_values(by='Rating', ascending=False)
    return recommendation.head(3)

#-------------------------------------
# Update Movies Average Rating
#-------------------------------------
def update_rating(user, title, rating, movie_df, stream_activity_df):
    existing = (
    (stream_activity_df['user_id'] == user) & (stream_activity_df['title'] == title)
    )
    if existing.any():
        stream_activity_df.loc[existing, 'rating'] = rating
        stream_activity_df.loc[existing, 'watched'] = 1
    else:
        new_entry = pd.DataFrame({
            "user_id": [user_login],
            "title": [title],
            "rating": [rating],
            "watched": [1]
        })
        stream_activity_df = pd.concat([stream_activity_df, new_entry], ignore_index=True)

        base_rating = movie_df.loc[movie_df['Title'] == title, 'rating'].values[0]
        movie_rating = stream_activity_df.loc[(stream_activity_df['title'] == title) & (stream_activity_df['watched'] == 1)]['rating']
        all_ratings = list(movie_rating) + [base_rating]
        final_avg_rating = sum(all_ratings)/len(all_ratings)
        movie_df.loc[movie_df['Title'] == title, 'Rating'] = round(final_avg_rating, 2)

        return movie_df, stream_activity_df

#-------------------------------
# Dashboard for Registered Users
#-------------------------------

def top_reco_by_ratings(user, movie_df, stream_activity_df, top_n=3):
    watched_titles = stream_activity_df.loc[(stream_activity_df['user_id'] == user) & (stream_activity_df['watched'] == 1), 'title'].tolist()
    rate_candidates = movie_df[~movie_df['Title'].isin(watched_titles)]
    top_movies = rate_candidates.sort_values(by='Rating', ascending=False)
    return top_movies.head(top_n)

def history_and_rating_table(user, movie_df, stream_activity_df):
    watch_history = stream_activity_df[(stream_activity_df['user_id'] == user) & (stream_activity_df['watched'] == 1)]
    user_log = watch_history.merge(
        movie_df[['Title', 'Genre']],
        left_on='title',
        right_on='Title',
        how='left'
    )
    user_log = user_log[['Title', 'Genre', 'rating']]
    user_log = user_log.sort_values(by='rating', ascending=False).reset_index(drop=True)
    return user_log

def bar_chart_topratedmovie(movie_df, top_n=5):
    top_movies = movie_df.sort_values(by='Rating', ascending=False).head(top_n)
    fig, ax = plt.subplots()
    ax.barh(top_movies['Title'], top_movies['Rating'], align='center', color='red')
    ax.set_xlabel("Rating")
    ax.set_ylabel("Movie Title")
    ax.set_title(f"Top {top_n} Rated Movies")
    ax.invert_yaxis()
    plt.tight_layout()
    return fig

#---------------------------------------
# Admin Actions
#---------------------------------------
def save_changes(movie_df):
    movie_df.to_csv("movie_database.csv", index=False)
    st.success("Changes Updated to Database.")

def add_movie(movie_df):
    movie_id = str(st.text_input("Enter Movie ID:"))
    title = st.text_input("Enter Movie Title:")
    genre = st.text_input("Enter Movie Genre:")
    year = st.text_input("Enter Movie Year:")
    if st.button("Add Movie"):
        if not movie_id or not title or not genre:
            st.warning("Please fill in all details.")
            return movie_df
        try:
            year = int(year)
        except ValueError:
            st.error("Year must be a valid integer.")
            return movie_df

        new_row = pd.DataFrame({'ID':[movie_id], 'Title':[title], 'Genre':[genre],'Year':[year]})
        movie_df = pd.concat([movie_df,new_row], ignore_index=True)
        save_changes(movie_df)
        st.success("Movie added successfully.")
    return movie_df

def remove_movie(movie_df):
    st.dataframe(movie_df[['ID', 'Title']])
    movie_id = st.text_input("Enter Movie ID to remove:")
    if st.button("Remove Movie"):
        if movie_id in movie_df['ID'].values:
            df = movie_df[movie_df['ID'] != movie_id].reset_index(drop=True)
            save_changes(movie_df)
            st.success("Movie removed successfully.")
        else:
            st.warning("Movie ID not found.")
    return movie_df

def edit_movie(movie_df):
    st.dataframe(movie_df[['ID', 'Title']])
    movie_id = st.text_input("Enter Movie ID to edit:")
    if st.button("Edit Movie"):
        if not movie_id:
            st.warning("Please enter Movie ID to edit.")
            return movie_df
        if movie_id in movie_df['ID'].values:
            row_idx = movie_df.index[movie_df['ID'] == movie_id][0]
            edit_title = st.text_input(f"Enter new title:", value=movie_df.at[row_idx, 'Title'])
            edit_genre = st.text_input(f"Enter new genre:", value=movie_df.at[row_idx, 'Genre'])
            edit_year = st.text_input(f"Enter new release year:", value=str(movie_df.at[row_idx, 'Year']))
            try:
                edit_year = int(edit_year)
            except ValueError:
                st.error("Year must be a valid integer.")
                return movie_df

            movie_df.at[row_idx, 'Title'] = edit_title
            movie_df.at[row_idx, 'Genre'] = edit_genre
            movie_df.at[row_idx, 'Year'] = edit_year
            save_changes(movie_df)
            st.success(f"Movie ID {movie_id} updated successfully!")
        else:
            st.warning("Movie ID not found.")
    return movie_df

def most_watched_movie(movie_df, stream_activity_df, top_n=5):
    movie_view_count = stream_activity_df['title'].value_counts().reset_index()
    movie_view_count.columns = ['Title', 'Views']
    most_watched = movie_view_count.merge(movie_df[['Title']], on='Title', how='inner')
    most_watched = most_watched.sort_values(by='Views', ascending=False).head(top_n)
    return most_watched

def display_most_watched(most_watched, top_n=5):
    fig, ax = plt.subplots()
    ax.barh(most_watched['Title'], most_watched['Views'], align='center', color='skyblue')
    ax.set_xlabel("Views")
    ax.set_ylabel("Movie Title")
    ax.set_title(f"Top {top_n} Watched Movies")
    ax.invert_yaxis()
    plt.tight_layout()
    return fig

def top_active_users(stream_activity_df, top_n=5):
    user_watch_count = stream_activity_df.groupby('user_id')['watched'].sum().reset_index()
    user_watch_count = user_watch_count.rename(columns={'watched': 'Movies Watched'})
    top_users = user_watch_count.sort_values(by='Movies Watched', ascending=False).head(top_n)
    fig, ax = plt.subplots()
    ax.barh(top_users['user_id'], top_users['Movies Watched'], align='center', color='skyblue')
    ax.set_xlabel("Watch Count")
    ax.set_ylabel("User")
    ax.set_title(f"Top {top_n} Active Users")
    ax.invert_yaxis()
    plt.tight_layout()
    return fig

#------------------------------------------
# User/ Admin Login + Navigations + UI Display
#------------------------------------------
choice = st.sidebar.radio("👤", ["Registered User", "New User"])
if choice == "Registered User":
    user_login = st.sidebar.text_input("Enter ID:")
    user_password = st.sidebar.text_input("Enter Password:", type="password")

    if user_login and user_password:
        if user_login in credentials:
            stored_password, stored_username, stored_role = credentials[user_login]
            if user_password == stored_password:
                st.success(f"Welcome {stored_username}!")
                if stored_role.lower() == "admin":
                    page = st.sidebar.radio("🛠️ Admin Actions", [
                        "💻 Manage Movie Database",
                        "📶 View Engagement Trends"
                    ])

                    if page == "💻 Manage Movie Database":
                        st.title("💻 Manage Movie Database")
                        action = st.radio("Actions", ["Add Movie", "Edit Movie", "Remove Movie"])
                        if action == "Add Movie":
                            movie_df = add_movie(movie_df)
                        elif action == "Edit Movie":
                            movie_df = edit_movie(movie_df)
                        elif action == "Remove Movie":
                            movie_df = remove_movie(movie_df)
                    if page == "📶 View Engagement Trends":
                        st.title("📶 Engagement Trends")
                        st.header("Most Watched Movies 📺")
                        watch_count = most_watched_movie(movie_df, stream_activity_df, top_n=5)
                        barchart1 = display_most_watched(watch_count, top_n=5)
                        st.pyplot(barchart1)
                        st.divider()
                        st.header("Top Active User 🤸")
                        active_user_chart = top_active_users(stream_activity_df, top_n=5)
                        st.pyplot(active_user_chart)
                        st.divider()
                        st.header("Trending Movie Based On Rating 💫️")
                        plot = bar_chart_topratedmovie(movie_df, top_n=5)
                        st.pyplot(plot)

                else:
                    page = st.sidebar.radio("👤 User Navigations", [
                        "🏠 Home Page",
                        "📱 Dashboard"
                    ])

                    if page == "🏠 Home Page":
                        st.title("Home Page")
                        st.divider()
                        st.subheader(" 🔎 Search Movie")
                        movie_name = st.text_input("Search by Movie Title")
                        all_genres = set()
                        for g in movie_df['Genre']:
                            for item in g.split(";"):
                                all_genres.add(item.strip())
                        genre_list = ["All"] + sorted(all_genres)
                        genre = st.selectbox("Select Genre", genre_list)

                        if movie_name or genre != "All":
                            filtered_df = movie_df.copy()
                            if movie_name:
                                filtered_df = filtered_df[filtered_df['Title'].str.contains(movie_name, case=False)]
                            if genre != "All":
                                filtered_df = filtered_df[filtered_df['Genre'].str.contains(genre, case=False)]

                            st.write("Search Results")
                            for i, row in filtered_df.iterrows():
                                st.write(f"**{row['Title']}** Genre:[{row['Genre']}] Year:[{row['Year']}] Rating: ⭐{row['Rating']}")

                                rating = st.slider(
                                  f"Rate {row['Title']}",
                                  1, 5, 3,
                                  key=f"rating_{i}"
                                )

                                if st.button("Submit rating", key=f"btn_{i}"):
                                    new_entry = pd.DataFrame({
                                        "user_id": [user_login],
                                        "title": [row['Title']],
                                        "rating": [rating]
                                    })

                                    stream_activity_df = pd.concat([stream_activity_df, new_entry], ignore_index=True)
                                    stream_activity_df.to_csv("WatchHistory&Rating.csv", index=False)
                                    st.success(f"Thanks for rating {row['title']}!")
                                    update_rating(user_login, row['title'], rating, movie_df, stream_activity_df)
                        st.header("Your Top 3 Movie Recommendations Based on Your Watch History")
                        recos = recommend_movie(user_login, movie_df, stream_activity_df)
                        if recos.empty:
                            st.info("No Recommendations available based on Watch History. Do watch more movies!!")
                        else:
                            for _, row in recos.iterrows():
                                st.write(f"🎥**{row['Title']}** 🔖Genre:[{row['Genre']}] Rating: ⭐[{row['Rating']}]")
                    if page == "📱 Dashboard":
                        st.title("User Dashboard")
                        st.header("Top 3 Movie Recommendations by Ratings ⭐🎉")
                        top_rec_rate = top_reco_by_ratings(user_login, movie_df, stream_activity_df, top_n=3)
                        if top_rec_rate.empty:
                            st.info("Oops! No recommendations so far, how about rating some songs instead?")
                        else:
                            for _, row in top_rec_rate.iterrows():
                                st.write(f"🎥**{row['Title']}** 🔖Genre:[{row['Genre']}] Rating: ⭐[{row['Rating']}]")
                        st.header("Watch History & Log Ratings 🕰️")
                        table = history_and_rating_table(user_login, movie_df, stream_activity_df)
                        st.dataframe(table)
                        st.header("Top Rated MOVIES 🤩🤩")
                        plot = bar_chart_topratedmovie(movie_df, top_n=5)
                        st.pyplot(plot)


            else:
                st.error("Incorrect Password! Try Again!")
        else:
            st.warning("User not found.")
elif choice == "New User":
    st.sidebar.subheader("Register New User")
    new_user_name = st.sidebar.text_input("Enter Name:")
    new_user_id = st.sidebar.text_input("Create User ID:")
    new_password = st.sidebar.text_input("Create User Password:")
    if st.sidebar.button("Create Account"):
        if not new_user_name or not new_user_id or not new_password:
            st.sidebar.error("Please complete all details to proceed.")
        else:
            new_role = "user"
            new_user = pd.DataFrame({
                "user_id": [new_user_id],
                "name": [new_user_name],
                "password": [new_password],
                "role": [new_role]

            })

            user_df = pd.concat([user_df, new_user], ignore_index=True)
            user_df.to_csv("users.csv", index=False)

            st.success("Account Created! Refresh Page and Login with your ID and Password to Continue.")

