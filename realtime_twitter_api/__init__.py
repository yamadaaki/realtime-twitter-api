from __future__ import annotations

import json
import re
from typing import Any, Literal

import requests

BASE_URL = 'https://search.yahoo.co.jp/realtime'

# ==============================================================

def get_next_data(url: str) -> dict | list | Any:
    response_text = requests.get(url).text
    return json.loads(re.findall(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', response_text)[0])


def get_json(url: str) -> dict | list | Any:
    response_text = requests.get(url).text
    return json.loads(response_text)


def get_tweets_by_url(url: str) -> list[dict[str, Any]]:
    return get_json(url)['timeline']['entry']


def sort_tweets(tweet_list: list[Tweet]) -> list[Tweet]:
    return sorted(tweet_list, key=lambda x: x.created_at, reverse=True)


def search_tweet_by_id(id: str | int) -> Tweet:
    url = BASE_URL + f'/search/tweet/{id}'
    next_data = get_next_data(url)
    return Tweet(next_data['props']['pageProps']['pageData']['bestTweet'])


def make_trend_dict(trend_items = None, tweet_items = None, hotbuzz_items = None) -> dict[Literal['trend', 'tweet', 'word'], Any]:
    trend_dict = {}

    if trend_items:
        trend_dict['trend'] = [{
            'query': item['query'],
            'rank_up': item['rankUp'],
            'tweet_count': item['tweetCount'],
            'genre': item['genre'],
            'child_buzz': item['childBuzz']
        } for item in trend_items]

    if tweet_items:
        trend_dict['tweet'] = [{
            'id': re.findall(r'/realtime/search/tweet/(\d+)', item['url'])[0],
            'body': item['body'],
            'image_url': item['imageUrl'],
            'reply_count': item['reply'],
            'rt_count': item['rt'],
            'like_count': item['like'],
            'time': item['time']
        } for item in tweet_items]

    if hotbuzz_items:
        trend_dict['hotbuzz'] = [item['query'] for item in hotbuzz_items]

    return trend_dict

# ==============================================================


class Tweet:
    """
    Attributes:
        content (str): ツイート内容
        id (str): ツイートID
        verified (bool): 投稿者が認証されているかどうか
        urls (list[str]): 添付URLのリスト
        hashtags (list[str]): ツイート内のハッシュタグのリスト
        mentions (list[str]): ツイート内でメンションされたユーザーのIDのリスト
        created_at (int): ツイートの作成日時
        reply_count (int): ツイートへのリプライの数
        rt_count (int): ツイートのリツイート数
        likes_count (int): ツイートのいいね数
        user_id (str): ユーザーID
        user_name (str): ユーザー名
        user_screen_name (str): スクリーン名
        quoted_tweet (str | None): 引用されたツイートのURL
        media (list[dict]): ツイートに添付されたメディアのリスト
    """

    def __init__(self, tweet_data: dict[str, Any]) -> None:
        self.content = re.sub(r'\tSTART\t(.+)\tEND\t', r'\1', tweet_data['displayText'])
        self.id = tweet_data['id']
        self.verified = tweet_data['verified']
        self.urls = [url['expandedUrl'] for url in tweet_data['urls']]
        self.hashtags = [hashtag['text'] for hashtag in tweet_data['hashtags']]
        self.mentions = [mention['id'] for mention in tweet_data['mentions']]
        self.created_at = tweet_data['createdAt']
        self.reply_count = tweet_data['replyCount']
        self.rt_count = tweet_data['replyCount']
        self.likes_count = tweet_data['likesCount']
        self.user_id = tweet_data['userId']
        self.user_name = tweet_data['name']
        self.user_screen_name = tweet_data['screenName']
        self.quoted_tweet = tweet_data.get('quotedTweet') and tweet_data['quotedTweet']['url'].split('?')[0]

        self.media = [
            {
                'type': media['type'],
                'url': media['item']['url']
            } for media in tweet_data.get('media', [])
        ]

        self._reply_count = 0

    def get_replies(self, times: int = 1) -> list[Tweet]:
        """ツイートのリプライを取得する
        一回の実行で最大10件の返信を取得できる

        Args:
            times (int, optional): 返信を取得する回数。デフォルトは1回

        Returns:
            list[Tweet]: 取得した返信のリスト
        """

        results = []

        for _ in range(times):
            url = BASE_URL + f'/api/v1/pagination/tweet/{self.id}?start={self._reply_count}'
            replies = [Tweet(i) for i in get_tweets_by_url(url)]
            results += replies
            self._reply_count += len(replies)

        return results

    def __repr__(self) -> str:
        return f'<Tweet id="{self.id}">'


class Search:
    def __init__(self, query: str, search_media: bool = False, sort_by: Literal['t', 'h'] = 't') -> None:
        """
        Args:
            query (str): 検索クエリ
            search_media (bool, optional): メディア検索
            sort_by (Literal['t', 'h'], optional): 't'で新着順、'h'で人気順
        """

        url = BASE_URL + f'/search?p={query}&md={sort_by}'
        url += (search_media and '&mtype=image') or ''

        self.search_media = search_media
        self.query = query
        self.sort_by = sort_by

        next_data = get_next_data(url)
        tweet_list = next_data['props']['pageProps']['pageData']['timeline']['entry']

        results = [Tweet(i) for i in tweet_list]
        self.results = sort_tweets(results) if sort_by == 't' else results

        self._oldest_tweet_id = (results and results[-1].id) or ''
        self._latest_tweet_id = (results and results[0].id) or ''
        self._tweet_count = len(results)
        self.crumb = next_data['props']['pageProps']['pageData']['pagination']['params']['crumb']

        self.trend = make_trend_dict(
            next_data['props']['pageProps']['pageData']['buzzTrend']['items'],
            next_data['props']['pageProps']['pageData']['poptw']['items']
        )

    def get_more_tweets(self, times: int = 1) -> list[Tweet]:
        """さらにツイートを取得する
        一回の実行で最大10件のツイートを取得できる

        Args:
            times (int, optional): ツイートを取得する回数。デフォルトは1回。
        """

        results = []

        for _ in range(times):
            url = BASE_URL + f'/api/v1/pagination?crumb={self.crumb}&p={self.query}&md={self.sort_by}'
            url += (self.search_media and '&mtype=image') or ''

            if self.sort_by == 't':
                url += f'&oldestTweetId={self._oldest_tweet_id}'
            elif self.sort_by == 'h':
                url += f'&start={self._tweet_count}'

            tweets = [Tweet(i) for i in get_tweets_by_url(url)]
            if self.sort_by == 't':
                tweets = sort_tweets(tweets)

            if tweets:
                self._oldest_tweet_id = tweets[-1].id

            self._tweet_count += len(tweets)
            results += tweets

        return results

    def get_latest_tweets(self) -> list[Tweet]:
        """最新のツイートを取得する
        """

        url = BASE_URL + f'/api/v1/autoscroll?crumb={self.crumb}&p={self.query}&latestTweetId={self._latest_tweet_id}'
        url += (self.search_media and '&mtype=image') or ''

        tweets = sort_tweets([Tweet(i) for i in get_tweets_by_url(url)])

        if tweets:
            self._latest_tweet_id = tweets[0].id

        return tweets

    def __repr__(self) -> str:
        return f'<Search query="{self.query}" search_media={self.search_media}>'


def get_transition(query: str, search_media: bool = False, interval: int = 900, span: int = 21600) -> dict[Literal['total', 'transitions', 'positive', 'negative'], Any]:
    """ツイート数の推移を取得

    Args:
        query (str): 検索クエリ
        search_media (bool, optional): メディア検索
        interval (int, optional): データの間隔。デフォルトは900秒
        span (int, optional): データの期間。デフォルトは21600秒
    """

    url = BASE_URL + f'/api/v1/transition?p={query}&interval={interval}&span={span}'
    url += (search_media and '&mtype=image') or ''

    response_data = get_json(url)

    return {
        'total': response_data['tweetTransition']['head']['totalResultsAvailable'],
        'transitions': response_data['tweetTransition']['entry'],
        'positive': response_data['sentimentPieChart']['positive'],
        'negative': response_data['sentimentPieChart']['negative']
    }


def get_trend() -> dict[Literal['trend', 'tweet', 'word'], Any]:
    """トレンドを取得する

    trend: トレンドワード
    tweet: 人気ツイート
    word: 急上昇ワード
    """

    next_data = get_next_data(BASE_URL)

    return make_trend_dict(
        next_data['props']['pageProps']['pageData']['buzzTrend']['items'],
        next_data['props']['pageProps']['pageData']['poptw']['items'],
        next_data['props']['pageProps']['pageData']['hotBuzz']['items']
    )
