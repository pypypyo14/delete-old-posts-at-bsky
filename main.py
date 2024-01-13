from datetime import datetime, timedelta, timezone
from typing import Generator

from atproto import Client, models


def get_all_feed(client: Client, actor: str) -> Generator[dict, None, None]:
    """
    # まだRepostと自分のPostとごっちゃ
    """
    cursor = None
    feed: list = []

    while True:
        fetched = fetch_feed(actor, cursor)
        if not fetched.cursor:
            break

        feed = feed + fetched.feed
        cursor = fetched.cursor

    for post in feed:
        yield {
            "uri": post.post.uri,
            "created_at": post.post.record.created_at,
            "text": post.post.record.text,
        }


# ref: https://github.com/MarshalX/atproto/blob/main/examples/advanced_usage/handle_cursor_pagination.py
def fetch_feed(
    actor: str, cursor: str | None
) -> models.AppBskyFeedGetAuthorFeed.Response:
    params = models.AppBskyFeedGetAuthorFeed.Params(actor=actor, limit=100)
    if cursor:
        params.cursor = cursor
    return client.app.bsky.feed.get_author_feed(params)


def delete_old_posts(client: Client, actor: str, days: int) -> None:
    posts = get_all_feed(client, actor)
    today = datetime.now(timezone.utc)
    specify_date = today - timedelta(days=days)

    for post in posts:
        posted_date = datetime.fromisoformat(post["created_at"])
        if posted_date < specify_date:
            try:
                client.delete_post(post_uri=post["uri"])
            except Exception as e:
                print(f"削除失敗: {post}")
                print(e)


def create_client_from_session_string(session_string: str) -> Client:
    client = Client()
    client.login(session_string=session_string)
    return client


if __name__ == "__main__":
    domain = str(input("domain: "))
    password = str(input("Password: "))
    days = int(input("Days: "))

    client = Client()
    client.login(domain, password)
    session_string = client.export_session_string()
    client2 = create_client_from_session_string(session_string)

    delete_old_posts(client2, domain, days)
