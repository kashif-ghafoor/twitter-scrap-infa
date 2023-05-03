import snscrape.modules.twitter as sntwitter
import pandas as pd
import boto3
from datetime import datetime
from io import BytesIO
import os

# AWS S3 configuration
s3 = boto3.client('s3')
bucket_name = os.environ['BUCKET_NAME']


headers = {
    "Access-Control-Allow-Origin": "*",  # Adjust the value according to your needs
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,PATCH,DELETE",
    "Access-Control-Allow-Credentials": "true",
}


def handler(event, context):
    # Get request parameters
    file_name = event['queryStringParameters']['file_name']
    limit = int(event['queryStringParameters']['limit'])
    query = event['queryStringParameters']['query']

    tweets = []

    # for tweet in sntwitter.TwitterHashtagScraper(query).get_items():
    #     if len(tweets) == limit:
    #         break
    #     else:
    #         tweets.append([tweet.id, tweet.date, tweet.user.username, tweet.rawContent, tweet.likeCount, tweet.replyCount,
    #                        tweet.retweetCount, tweet.lang, tweet.url, tweet.hashtags, tweet.coordinates, tweet.place,
    #                        tweet.retweetedTweet, tweet.source, tweet.mentionedUsers, tweet.followersCount, tweet.viewCount])

    # df = pd.DataFrame(tweets, columns=['ID', 'Date', 'User', 'Tweet', 'Likes', 'Replies', 'Retweet', 'Language', 'URL', 'Hashtags',
    #                                    'coordinates', 'place', 'retweetedTweet', 'source', 'mentions'])

    # df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    # df['Date'] = df['Date'].apply(
    #     lambda a: datetime.strftime(a, "%Y-%m-%d %H:%M:%S"))
    # df['Date'] = pd.to_datetime(df['Date'])

    # Sample DataFrame
    data = {'ID': list(range(1, limit + 1)),
            'Date': [datetime(2023, 5, 1)] * limit}
    df = pd.DataFrame(data)

    # Save DataFrame to Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)

    # Save Excel file to S3
    s3.put_object(Body=output, Bucket=bucket_name,
                  Key=file_name)

    # Lambda function response with the public link
    link = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': file_name},
        ExpiresIn=3600
    )
    return {
        'statusCode': 200,
        'body': link,
        'headers': headers,
    }
