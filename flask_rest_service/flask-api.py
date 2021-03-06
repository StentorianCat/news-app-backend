import requests
import json
import os

from flask import Flask
from flask_restful import Resource, Api, reqparse
from requests_oauthlib import OAuth1
from datetime import datetime, timedelta

APP = Flask(__name__)
API = Api(APP)

news_sources = 'ABC OR CNN OR FoxNews OR WSJ OR MSNBC OR NPR'
local_sources = 'KSNTNews OR wibw OR 1350kman'

def maptweet(tweet):
    if len(tweet['entities']['urls']) > 0 and tweet['entities']['urls'][0].get('url'):
        source_url = tweet['entities']['urls'][0].get('url')
    else:
        source_url = ''

    if tweet['entities'].get('media') and len(tweet['entities']['media']) > 0 and tweet['entities']['media'][0].get('media_url'):
        media_url = tweet['entities']['media'][0].get('media_url')
    else:
        media_url = ''

    reduced_tweet = {
        'id': tweet['id_str'],
        'title': tweet['user']['name'],
        'text': tweet['text'],
        'source_url': source_url,
        'media_url': media_url,
    }
    return reduced_tweet

class TwitterNewsData(Resource):
    def get(self):

        args = self.getarguments()
        search_text = self.getsearchtext(args['news_type'])

        tweets = self.gettweets(search_text, args['news_type'])
        
        top_tweets = self.filtertoptweets(tweets)
        reduced_tweets = self.reducetweetobjects(top_tweets)
        return json.dumps(list(reduced_tweets))

    def getsearchtext(self, news_type):
        request_params_table = {
            'world_news' : 'global OR world',
            'us_news' : "us OR united states",
            'local_news' : 'news OR KSNTNews OR wibw OR 1350kman OR kansas' 
        }

        return request_params_table[news_type]

    def filtertoptweets(self, tweets):
        for i, tweets_day in enumerate(tweets):
            tweets[i].sort(key=lambda x: x["retweet_count"], reverse=True)
            tweets[i] = tweets[i][:5]

        return tweets

    def reducetweetobjects(self, tweets):
        return map(lambda tweets_day: list(map(maptweet, tweets_day)), tweets)

    def getarguments(self): 
        parser = reqparse.RequestParser()
        parser.add_argument('news_type', type=str, help='global, national, or local')

        return parser.parse_args()

    def gettweets(self, search_text, news_type):
        tweets = []

        if news_type == 'local_news':
            news_from = local_sources
            time_intervals = 1
        else:
            news_from = news_sources
            time_intervals = 5

        for x in range(0, time_intervals):
            end_date = datetime.today() - timedelta(days=x)
            end_formatted = end_date.strftime('%Y-%m-%d')
            begin_date = datetime.today() - timedelta(days=(x + 1))
            begin_formatted = begin_date.strftime('%Y-%m-%d')

            if news_type == 'local_news':
                begin_formatted = ''
                end_formatted = ''

            params = {
                'q': search_text, 
                'lang': 'en', 
                'result_type': 'popular',
                'since': begin_formatted,
                'until': end_formatted,
                'filter': 'links',
                '-filter': 'nativeretweets',
                'from': news_from
            }

            url = 'https://api.twitter.com/1.1/search/tweets.json'
            auth = OAuth1(
                // authentication data goes here
            )

            req_object = requests.get(url, params=params, auth=auth)
            json_data = req_object.json()

            tweets.append(json_data["statuses"])
        
        return tweets

API.add_resource(TwitterNewsData, '/news_data')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    APP.run(host='0.0.0.0', port=port)
