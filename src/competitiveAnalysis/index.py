import pandas as pd
import base64
from requests_toolbelt.multipart import decoder
import json


def competitveAnalysis(file1, file2):
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    df1_count = df1.groupby(df1["Date"].dt.date)["Tweet"].count()
    df2_count = df2.groupby(df2["Date"].dt.date)["Tweet"].count()

    # Convert date objects to strings
    df1_dates = [date.strftime('%Y-%m-%d') for date in df1_count.index]
    df2_dates = [date.strftime('%Y-%m-%d') for date in df2_count.index]

    # Create a dictionary to store the data
    chart_data = {
        "file1": {
            "x": df1_dates,
            "y": df1_count.values.tolist(),
            "name": "File 1",
            "color": "blue"
        },
        "file2": {
            "x": df2_dates,
            "y": df2_count.values.tolist(),
            "name": "File 2",
            "color": "purple"
        }
    }

    return chart_data


def number_of_tweets_comparison(file1, file2):
    # Count the number of tweets in each file
    num_tweets_file1 = len(file1)
    num_tweets_file2 = len(file2)

    # Create a dictionary with the data to be converted to JSON format
    data = {
        "labels": ["File 1", "File 2"],  # x-axis values
        "values": [num_tweets_file1, num_tweets_file2]  # y-axis values
    }
    # Convert the Pandas dataframe into JSON format
    return data


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

    file1 = multipart_data.parts[0]
    file2 = multipart_data.parts[1]

    num_tweets_comparison = number_of_tweets_comparison(
        file1.content, file2.content)

    competitive_analysis = competitveAnalysis(file1.content, file2.content)

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'tweets_comparison': num_tweets_comparison,
            'competitive_analysis': competitive_analysis
        }),
    }
