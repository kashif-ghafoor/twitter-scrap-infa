import re
import json
import base64
import pandas as pd
import networkx as nx
from textblob import TextBlob
from collections import defaultdict
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from requests_toolbelt.multipart import decoder


def generate_hashtag_data(file_path):
    # Read the excel file
    df = pd.read_excel(file_path)

    # Define function to extract hashtags from each tweet
    def extract_hashtags(text):
        hashtags = re.findall(r'\#\w+', text)
        return hashtags

    # Create a list of all hashtags in the dataframe
    all_hashtags = []
    for tweet in df['Tweet']:
        hashtags = extract_hashtags(tweet)
        all_hashtags.extend(hashtags)

    # Create a dictionary to store the frequency of each hashtag
    frequency = {}
    for hashtag in all_hashtags:
        if hashtag in frequency:
            frequency[hashtag] += 1
        else:
            frequency[hashtag] = 1

    # Reshape and reorder the text
    reshaped_text = {}
    for k, v in frequency.items():
        reshaped_k = reshape(k)
        bidi_k = get_display(reshaped_k)
        reshaped_text[bidi_k] = v

    # Return the data
    return {
        "hashtag_frequency": frequency,
        "reshaped_text": reshaped_text
    }


def generate_sentiment_data(file_path):
    # Load the data from Excel file
    df = pd.read_excel(file_path)

    # Define function to calculate sentiment polarity
    def get_sentiment(text):
        blob = TextBlob(text)
        return blob.sentiment.polarity

    # Create a dictionary to store sentiment values for each user
    sentiments = defaultdict(list)

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Get the user and tweet
        user = row['User']
        tweet = row['Tweet']

        # Calculate sentiment polarity of the tweet
        sentiment = get_sentiment(tweet)

        # Append sentiment to the list of sentiments for the user
        sentiments[user].append(sentiment)

    # Create a list of sentiment data for each user
    sentiment_data = []
    for user in df['User'].unique():
        user_sentiments = sentiments[user]
        indices = list(range(1, len(user_sentiments) + 1))
        sentiment_data.append(
            {"user": user, "indices": indices, "sentiments": user_sentiments})

    return sentiment_data


def generate_user_tweet_counts(file_path):
    # Read the Excel file into a Pandas DataFrame
    df = pd.read_excel(file_path)

    # Group the data by user and count the number of tweets for each user
    user_counts = df.groupby('User').size().reset_index(name='count')

    # Convert the user_counts DataFrame into a list of dictionaries
    user_tweet_counts = user_counts.to_dict('records')

    return user_tweet_counts


def generate_user_mentions_graph_data(file_path):
    # Load the Excel file into a Pandas DataFrame
    df = pd.read_excel(file_path)

    # Extract the usernames from the tweet column using regular expressions
    df['username'] = df['Tweet'].str.extract(r'@(\w+)')

    # Create a list of unique usernames
    users = list(df['username'].dropna().unique())

    # Create an empty directed graph using NetworkX
    G = nx.DiGraph()

    # Add nodes to the graph for each user
    for user in users:
        G.add_node(user)

    # Add edges to the graph for each mention
    for tweet in df['Tweet']:
        # Find all mentions in the tweet using regular expressions
        mentions = re.findall(r'@(\w+)', tweet)
        # Create edges between the mentioned users
        for i in range(len(mentions)):
            for j in range(i+1, len(mentions)):
                G.add_edge(mentions[i], mentions[j])

    # Calculate the degree centrality of each node (user)
    centrality = nx.degree_centrality(G)

    # Sort the centrality dictionary by value in descending order
    sorted_centrality = sorted(
        centrality.items(), key=lambda x: x[1], reverse=True)

    # Get the top 10 most influential users
    top_users = [user[0] for user in sorted_centrality[:10]]

    # Create a subgraph of the top users
    H = G.subgraph(top_users)

    # Create a dictionary containing the necessary data for the frontend
    graph_data = {
        'nodes': [node for node in H.nodes()],
        'edges': [{'source': edge[0], 'target': edge[1]} for edge in H.edges()],
    }

    return graph_data


def generate_map_data(file_path):
    # Load the data from the Excel file
    data = pd.read_excel(file_path)

    # Filter out rows without coordinates
    data = data[data['coordinates'].notna()]

    # Extract coordinates and create a list of dictionaries with lat and lon
    coords_list = []
    for i, row in data.iterrows():
        coords_str = row['coordinates']
        lon = float(coords_str.split(',')[0].split('=')[1])
        lat = float(coords_str.split(',')[1].split('=')[1][:-1])
        coords_list.append({'lat': lat, 'lon': lon})

    # Return the coordinates data
    return coords_list


headers = {
    "Access-Control-Allow-Origin": "*",  # Adjust the value according to your needs
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,PATCH,DELETE",
    "Access-Control-Allow-Credentials": "true",
}


def handler(event, context):
    # decode the multipart form data
    decoded_str = base64.b64decode(event["body"])

    content_type_header = event["headers"]["content-type"]

    multipart_data = decoder.MultipartDecoder(
        decoded_str, content_type_header)

    # get the file data from the multipart data
    file = multipart_data.parts[0]

    # print the file name
    print(file.headers[b'Content-Disposition'].decode().split(';')[1])

    # generate hashtag data
    hashtag_data = generate_hashtag_data(file.content)

    # generate sentiment data
    sentiment_data = generate_sentiment_data(file.content)

    # generate user tweet counts
    user_tweet_counts = generate_user_tweet_counts(file.content)

    # generate user mentions graph data
    user_mentions_graph_data = generate_user_mentions_graph_data(file.content)

    # generate map data
    map_data = generate_map_data(file.content)

    # return the response
    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps({
            "hashtag_data": hashtag_data,
            "sentiment_data": sentiment_data,
            "user_tweet_counts": user_tweet_counts,
            "user_mentions_graph_data": user_mentions_graph_data,
            "map_data": map_data
        })
    }
