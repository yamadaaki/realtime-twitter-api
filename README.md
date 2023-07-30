# realtime-twitter-api

リアルタイム検索のAPIを使用してツイートやトレンドを検索できるライブラリです。
APIキーなどを使用せずに無料無制限で使用できます。


## インストール

pipを用いてインストールできます

```bash
  pip install realtime-twitter-api
```

## 使い方

**Tweetクラス**

| 変数名         | タイプ  | 説明         |
| ----------- | ---- | ---------- |
| content     | str  | ツイートの内容    |
| id          | str  | ツイートのID    |
| reply_count | int  | リプライ数      |
| like_count  | int  | いいね数       |
| rt_count    | int  | リツイート数     |
| created_at  | int  | ツイートの作成日時  |
| urls        | list | 添付URLのリスト  |
| hashtags    | list | ハッシュタグのリスト |
| mentions     | list | メンションされたユーザーのリスト |
| media        | list | 添付メディアのリスト       |
| quoted_tweet | str  | 引用されたツイートのURL    |
| user_id          | str  | 投稿者のID       |
| user_name        | str  | 投稿者の名前       |
| user_screen_name | str  | 投稿者のスクリーンネーム |
| verified         | bool | 投稿者が認証されているか |

```py
# リプライを取得
tweet.get_replies()
```

**ツイート検索**

```py
from realtime_twitter_api import Search

# search_media = True にすると画像・動画を検索
# sort_by = 'h' にすると話題順で検索（デフォルトは新着順）

search_obj = realtime_twitter_api.Search('検索ワード')

# 検索結果のリスト(最大40件)
search_obj.results

# さらにツイートを取得する
search_obj.get_more_tweets()

# 最新のツイートを取得する
# sort_by が 't' (新着順) の場合のみ使用可能
search_obj.get_latest_tweets()
```

**トレンド検索**

```py
from realtime_twitter_api import get_trend

trend = get_trend()

# トレンドワード
trend['trend']

# 人気ツイート
trend['tweet']

# 急上昇ワード
trend['word']
```

**ツイート数の推移**

```py
from realtime_twitter_api import get_transition

# search_media = True にすると画像・動画を検索
# interval 取得するデータの間隔。デフォルトは900秒
# span 検索する期間。デフォルトは21600秒

transition = get_transition('検索ワード')

# トータルのツイート数
transition['total']

# 時間毎のツイート数
transition['transitions']

# ポジティブなツイートの割合
transition['positive']

# ネガティブなツイートの割合
transition['negative']
```