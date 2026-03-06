"""
Social Media MCP Server — 20+ platforms, no Postiz dependency.
Direct API calls to Twitter/X, LinkedIn, Facebook, Instagram, TikTok,
YouTube, Reddit, Pinterest, Discord, Slack, Telegram, Threads, Bluesky,
Mastodon, Medium, Dev.to, Hashnode, WordPress, Google My Business, Dribbble.
"""
import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

app = Server("social-media")

# ─── Config from env ──────────────────────────────────────────
ENV = {k: os.getenv(k, "") for k in [
    # Twitter/X
    "TWITTER_API_KEY", "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET", "TWITTER_BEARER_TOKEN",
    # LinkedIn
    "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID", "LINKEDIN_PAGE_ID",
    # Facebook
    "FB_PAGE_ACCESS_TOKEN", "FB_PAGE_ID",
    # Instagram
    "IG_ACCESS_TOKEN", "IG_USER_ID",
    # Threads (uses IG token)
    "THREADS_USER_ID",
    # TikTok
    "TIKTOK_ACCESS_TOKEN",
    # YouTube
    "YOUTUBE_ACCESS_TOKEN",
    # Reddit
    "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
    "REDDIT_USERNAME", "REDDIT_PASSWORD",
    # Pinterest
    "PINTEREST_ACCESS_TOKEN",
    # Discord
    "DISCORD_WEBHOOK_URL",
    # Slack
    "SLACK_WEBHOOK_URL",
    # Telegram
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    # Bluesky
    "BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD",
    # Mastodon
    "MASTODON_ACCESS_TOKEN", "MASTODON_INSTANCE",
    # Medium
    "MEDIUM_ACCESS_TOKEN", "MEDIUM_AUTHOR_ID",
    # Dev.to
    "DEVTO_API_KEY",
    # Hashnode
    "HASHNODE_TOKEN", "HASHNODE_PUBLICATION_ID",
    # WordPress
    "WORDPRESS_URL", "WORDPRESS_USERNAME", "WORDPRESS_APP_PASSWORD",
    # Google My Business
    "GMB_ACCESS_TOKEN", "GMB_LOCATION_ID",
    # Dribbble
    "DRIBBBLE_ACCESS_TOKEN",
]}


def e(key: str) -> str:
    return ENV.get(key, "")


def _ok(data: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2))]


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": msg}))]


async def _http(method: str, url: str, headers: dict = None, **kwargs) -> httpx.Response:
    async with httpx.AsyncClient(timeout=30) as c:
        return await getattr(c, method)(url, headers=headers or {}, **kwargs)


# ─── Twitter/X ────────────────────────────────────────────────

async def _post_tweet(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    if not e("TWITTER_ACCESS_TOKEN"):
        return _err("Set TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET, TWITTER_API_KEY, TWITTER_API_SECRET")
    from requests_oauthlib import OAuth1
    import requests
    auth = OAuth1(e("TWITTER_API_KEY"), e("TWITTER_API_SECRET"),
                  e("TWITTER_ACCESS_TOKEN"), e("TWITTER_ACCESS_SECRET"))
    r = requests.post("https://api.x.com/2/tweets", json={"text": text}, auth=auth)
    if r.status_code in (200, 201):
        return _ok({"status": "posted", "platform": "twitter", "response": r.json()})
    return _err(f"Twitter {r.status_code}: {r.text}")


async def _get_twitter_me(args: dict) -> list[TextContent]:
    if not e("TWITTER_BEARER_TOKEN"):
        return _err("TWITTER_BEARER_TOKEN not set")
    r = await _http("get", "https://api.x.com/2/users/me",
                     headers={"Authorization": f"Bearer {e('TWITTER_BEARER_TOKEN')}"})
    return _ok(r.json())


# ─── LinkedIn ─────────────────────────────────────────────────

async def _post_linkedin(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    if not e("LINKEDIN_ACCESS_TOKEN") or not e("LINKEDIN_PERSON_ID"):
        return _err("Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_ID")
    payload = {
        "author": f"urn:li:person:{e('LINKEDIN_PERSON_ID')}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": {
            "shareCommentary": {"text": text}, "shareMediaCategory": "NONE"}},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = await _http("post", "https://api.linkedin.com/v2/ugcPosts", json=payload,
                     headers={"Authorization": f"Bearer {e('LINKEDIN_ACCESS_TOKEN')}",
                              "X-Restli-Protocol-Version": "2.0.0"})
    if r.status_code in (200, 201):
        return _ok({"status": "posted", "platform": "linkedin", "response": r.json()})
    return _err(f"LinkedIn {r.status_code}: {r.text}")


async def _post_linkedin_page(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    if not e("LINKEDIN_ACCESS_TOKEN") or not e("LINKEDIN_PAGE_ID"):
        return _err("Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_PAGE_ID")
    payload = {
        "author": f"urn:li:organization:{e('LINKEDIN_PAGE_ID')}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": {
            "shareCommentary": {"text": text}, "shareMediaCategory": "NONE"}},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = await _http("post", "https://api.linkedin.com/v2/ugcPosts", json=payload,
                     headers={"Authorization": f"Bearer {e('LINKEDIN_ACCESS_TOKEN')}",
                              "X-Restli-Protocol-Version": "2.0.0"})
    if r.status_code in (200, 201):
        return _ok({"status": "posted", "platform": "linkedin-page", "response": r.json()})
    return _err(f"LinkedIn Page {r.status_code}: {r.text}")


# ─── Facebook ─────────────────────────────────────────────────

async def _post_facebook(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    link = args.get("link", "")
    if not text:
        return _err("text is required")
    if not e("FB_PAGE_ACCESS_TOKEN") or not e("FB_PAGE_ID"):
        return _err("Set FB_PAGE_ACCESS_TOKEN and FB_PAGE_ID")
    data = {"message": text, "access_token": e("FB_PAGE_ACCESS_TOKEN")}
    if link:
        data["link"] = link
    r = await _http("post", f"https://graph.facebook.com/v19.0/{e('FB_PAGE_ID')}/feed", data=data)
    if r.status_code == 200:
        return _ok({"status": "posted", "platform": "facebook", "response": r.json()})
    return _err(f"Facebook {r.status_code}: {r.text}")


# ─── Instagram ────────────────────────────────────────────────

async def _post_instagram(args: dict) -> list[TextContent]:
    caption = args.get("text", "")
    image_url = args.get("image_url", "")
    if not caption or not image_url:
        return _err("text and image_url are required")
    if not e("IG_ACCESS_TOKEN") or not e("IG_USER_ID"):
        return _err("Set IG_ACCESS_TOKEN and IG_USER_ID")
    r1 = await _http("post", f"https://graph.facebook.com/v19.0/{e('IG_USER_ID')}/media",
                      data={"image_url": image_url, "caption": caption, "access_token": e("IG_ACCESS_TOKEN")})
    if r1.status_code != 200:
        return _err(f"IG container {r1.status_code}: {r1.text}")
    cid = r1.json().get("id")
    r2 = await _http("post", f"https://graph.facebook.com/v19.0/{e('IG_USER_ID')}/media_publish",
                      data={"creation_id": cid, "access_token": e("IG_ACCESS_TOKEN")})
    if r2.status_code == 200:
        return _ok({"status": "posted", "platform": "instagram", "response": r2.json()})
    return _err(f"IG publish {r2.status_code}: {r2.text}")


# ─── Threads ──────────────────────────────────────────────────

async def _post_threads(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    uid = e("THREADS_USER_ID") or e("IG_USER_ID")
    token = e("IG_ACCESS_TOKEN")
    if not token or not uid:
        return _err("Set IG_ACCESS_TOKEN and THREADS_USER_ID (or IG_USER_ID)")
    r1 = await _http("post", f"https://graph.threads.net/v1.0/{uid}/threads",
                      data={"media_type": "TEXT", "text": text, "access_token": token})
    if r1.status_code != 200:
        return _err(f"Threads container {r1.status_code}: {r1.text}")
    cid = r1.json().get("id")
    r2 = await _http("post", f"https://graph.threads.net/v1.0/{uid}/threads_publish",
                      data={"creation_id": cid, "access_token": token})
    if r2.status_code == 200:
        return _ok({"status": "posted", "platform": "threads", "response": r2.json()})
    return _err(f"Threads publish {r2.status_code}: {r2.text}")


# ─── TikTok ───────────────────────────────────────────────────

async def _post_tiktok(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    video_url = args.get("video_url", "")
    if not text or not video_url:
        return _err("text and video_url are required")
    if not e("TIKTOK_ACCESS_TOKEN"):
        return _err("Set TIKTOK_ACCESS_TOKEN")
    # TikTok Content Posting API - init upload
    r = await _http("post", "https://open.tiktokapis.com/v2/post/publish/content/init/",
                     json={"post_info": {"title": text, "privacy_level": "PUBLIC_TO_EVERYONE"},
                           "source_info": {"source": "PULL_FROM_URL", "video_url": video_url}},
                     headers={"Authorization": f"Bearer {e('TIKTOK_ACCESS_TOKEN')}",
                              "Content-Type": "application/json"})
    if r.status_code == 200:
        return _ok({"status": "initiated", "platform": "tiktok", "response": r.json()})
    return _err(f"TikTok {r.status_code}: {r.text}")


# ─── YouTube ──────────────────────────────────────────────────

async def _post_youtube(args: dict) -> list[TextContent]:
    title = args.get("title", args.get("text", ""))
    description = args.get("description", "")
    if not title:
        return _err("title is required")
    if not e("YOUTUBE_ACCESS_TOKEN"):
        return _err("Set YOUTUBE_ACCESS_TOKEN")
    # Community post (text-only)
    r = await _http("post", "https://www.googleapis.com/youtube/v3/activities",
                     json={"snippet": {"title": title, "description": description}},
                     headers={"Authorization": f"Bearer {e('YOUTUBE_ACCESS_TOKEN')}"})
    return _ok({"status": "posted", "platform": "youtube", "response": r.json()})


# ─── Reddit ───────────────────────────────────────────────────

async def _post_reddit(args: dict) -> list[TextContent]:
    title = args.get("title", args.get("text", ""))
    text = args.get("text", "")
    subreddit = args.get("subreddit", "")
    if not title or not subreddit:
        return _err("title and subreddit are required")
    if not e("REDDIT_CLIENT_ID"):
        return _err("Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD")
    # Get token
    auth_r = await _http("post", "https://www.reddit.com/api/v1/access_token",
                          data={"grant_type": "password", "username": e("REDDIT_USERNAME"),
                                "password": e("REDDIT_PASSWORD")},
                          headers={"User-Agent": "AIRealtor/1.0"},
                          auth=(e("REDDIT_CLIENT_ID"), e("REDDIT_CLIENT_SECRET")))
    token = auth_r.json().get("access_token", "")
    r = await _http("post", "https://oauth.reddit.com/api/submit",
                     data={"kind": "self", "sr": subreddit, "title": title, "text": text},
                     headers={"Authorization": f"Bearer {token}", "User-Agent": "AIRealtor/1.0"})
    return _ok({"status": "posted", "platform": "reddit", "response": r.json()})


# ─── Pinterest ────────────────────────────────────────────────

async def _post_pinterest(args: dict) -> list[TextContent]:
    title = args.get("title", args.get("text", ""))
    description = args.get("text", "")
    image_url = args.get("image_url", "")
    board_id = args.get("board_id", "")
    link = args.get("link", "")
    if not title or not image_url or not board_id:
        return _err("title, image_url, and board_id are required")
    if not e("PINTEREST_ACCESS_TOKEN"):
        return _err("Set PINTEREST_ACCESS_TOKEN")
    payload = {"title": title, "description": description, "board_id": board_id,
               "media_source": {"source_type": "image_url", "url": image_url}}
    if link:
        payload["link"] = link
    r = await _http("post", "https://api.pinterest.com/v5/pins", json=payload,
                     headers={"Authorization": f"Bearer {e('PINTEREST_ACCESS_TOKEN')}"})
    if r.status_code in (200, 201):
        return _ok({"status": "posted", "platform": "pinterest", "response": r.json()})
    return _err(f"Pinterest {r.status_code}: {r.text}")


# ─── Discord ──────────────────────────────────────────────────

async def _post_discord(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    if not e("DISCORD_WEBHOOK_URL"):
        return _err("Set DISCORD_WEBHOOK_URL")
    r = await _http("post", e("DISCORD_WEBHOOK_URL"), json={"content": text})
    if r.status_code == 204:
        return _ok({"status": "posted", "platform": "discord"})
    return _err(f"Discord {r.status_code}: {r.text}")


# ─── Slack ────────────────────────────────────────────────────

async def _post_slack(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    if not e("SLACK_WEBHOOK_URL"):
        return _err("Set SLACK_WEBHOOK_URL")
    r = await _http("post", e("SLACK_WEBHOOK_URL"), json={"text": text})
    if r.status_code == 200:
        return _ok({"status": "posted", "platform": "slack"})
    return _err(f"Slack {r.status_code}: {r.text}")


# ─── Telegram ─────────────────────────────────────────────────

async def _post_telegram(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    chat_id = args.get("chat_id", e("TELEGRAM_CHAT_ID"))
    if not text:
        return _err("text is required")
    if not e("TELEGRAM_BOT_TOKEN") or not chat_id:
        return _err("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    r = await _http("post", f"https://api.telegram.org/bot{e('TELEGRAM_BOT_TOKEN')}/sendMessage",
                     json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    if r.status_code == 200:
        return _ok({"status": "posted", "platform": "telegram", "response": r.json()})
    return _err(f"Telegram {r.status_code}: {r.text}")


# ─── Bluesky ──────────────────────────────────────────────────

async def _post_bluesky(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    if not e("BLUESKY_HANDLE") or not e("BLUESKY_APP_PASSWORD"):
        return _err("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD")
    # Create session
    sr = await _http("post", "https://bsky.social/xrpc/com.atproto.server.createSession",
                      json={"identifier": e("BLUESKY_HANDLE"), "password": e("BLUESKY_APP_PASSWORD")})
    if sr.status_code != 200:
        return _err(f"Bluesky auth {sr.status_code}: {sr.text}")
    session = sr.json()
    from datetime import datetime, timezone
    r = await _http("post", "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                     json={"repo": session["did"], "collection": "app.bsky.feed.post",
                           "record": {"$type": "app.bsky.feed.post", "text": text,
                                      "createdAt": datetime.now(timezone.utc).isoformat()}},
                     headers={"Authorization": f"Bearer {session['accessJwt']}"})
    if r.status_code == 200:
        return _ok({"status": "posted", "platform": "bluesky", "response": r.json()})
    return _err(f"Bluesky {r.status_code}: {r.text}")


# ─── Mastodon ─────────────────────────────────────────────────

async def _post_mastodon(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    instance = e("MASTODON_INSTANCE") or "https://mastodon.social"
    if not e("MASTODON_ACCESS_TOKEN"):
        return _err("Set MASTODON_ACCESS_TOKEN and MASTODON_INSTANCE")
    r = await _http("post", f"{instance}/api/v1/statuses",
                     data={"status": text},
                     headers={"Authorization": f"Bearer {e('MASTODON_ACCESS_TOKEN')}"})
    if r.status_code == 200:
        return _ok({"status": "posted", "platform": "mastodon", "response": r.json()})
    return _err(f"Mastodon {r.status_code}: {r.text}")


# ─── Medium ───────────────────────────────────────────────────

async def _post_medium(args: dict) -> list[TextContent]:
    title = args.get("title", args.get("text", ""))
    content = args.get("content", args.get("text", ""))
    tags = args.get("tags", [])
    if not title or not content:
        return _err("title and content are required")
    if not e("MEDIUM_ACCESS_TOKEN"):
        return _err("Set MEDIUM_ACCESS_TOKEN and MEDIUM_AUTHOR_ID")
    author_id = e("MEDIUM_AUTHOR_ID")
    if not author_id:
        me = await _http("get", "https://api.medium.com/v1/me",
                          headers={"Authorization": f"Bearer {e('MEDIUM_ACCESS_TOKEN')}"})
        author_id = me.json().get("data", {}).get("id", "")
    r = await _http("post", f"https://api.medium.com/v1/users/{author_id}/posts",
                     json={"title": title, "contentFormat": "markdown", "content": content,
                           "tags": tags, "publishStatus": "draft"},
                     headers={"Authorization": f"Bearer {e('MEDIUM_ACCESS_TOKEN')}"})
    if r.status_code in (200, 201):
        return _ok({"status": "draft_created", "platform": "medium", "response": r.json()})
    return _err(f"Medium {r.status_code}: {r.text}")


# ─── Dev.to ───────────────────────────────────────────────────

async def _post_devto(args: dict) -> list[TextContent]:
    title = args.get("title", args.get("text", ""))
    body = args.get("content", args.get("text", ""))
    tags = args.get("tags", [])
    published = args.get("published", False)
    if not title or not body:
        return _err("title and content are required")
    if not e("DEVTO_API_KEY"):
        return _err("Set DEVTO_API_KEY")
    r = await _http("post", "https://dev.to/api/articles",
                     json={"article": {"title": title, "body_markdown": body,
                                       "tags": tags, "published": published}},
                     headers={"api-key": e("DEVTO_API_KEY")})
    if r.status_code in (200, 201):
        return _ok({"status": "posted", "platform": "devto", "response": r.json()})
    return _err(f"Dev.to {r.status_code}: {r.text}")


# ─── Hashnode ─────────────────────────────────────────────────

async def _post_hashnode(args: dict) -> list[TextContent]:
    title = args.get("title", args.get("text", ""))
    content = args.get("content", args.get("text", ""))
    tags = args.get("tags", [])
    if not title or not content:
        return _err("title and content are required")
    if not e("HASHNODE_TOKEN") or not e("HASHNODE_PUBLICATION_ID"):
        return _err("Set HASHNODE_TOKEN and HASHNODE_PUBLICATION_ID")
    query = """mutation PublishPost($input: PublishPostInput!) {
        publishPost(input: $input) { post { id url title } }
    }"""
    tag_objs = [{"slug": t, "name": t} for t in tags]
    r = await _http("post", "https://gql.hashnode.com",
                     json={"query": query, "variables": {"input": {
                         "title": title, "contentMarkdown": content,
                         "publicationId": e("HASHNODE_PUBLICATION_ID"),
                         "tags": tag_objs}}},
                     headers={"Authorization": e("HASHNODE_TOKEN")})
    return _ok({"status": "posted", "platform": "hashnode", "response": r.json()})


# ─── WordPress ────────────────────────────────────────────────

async def _post_wordpress(args: dict) -> list[TextContent]:
    title = args.get("title", args.get("text", ""))
    content = args.get("content", args.get("text", ""))
    status = args.get("status", "draft")
    if not title or not content:
        return _err("title and content are required")
    wp_url = e("WORDPRESS_URL").rstrip("/")
    if not wp_url or not e("WORDPRESS_USERNAME") or not e("WORDPRESS_APP_PASSWORD"):
        return _err("Set WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD")
    import base64
    creds = base64.b64encode(f"{e('WORDPRESS_USERNAME')}:{e('WORDPRESS_APP_PASSWORD')}".encode()).decode()
    r = await _http("post", f"{wp_url}/wp-json/wp/v2/posts",
                     json={"title": title, "content": content, "status": status},
                     headers={"Authorization": f"Basic {creds}"})
    if r.status_code in (200, 201):
        return _ok({"status": status, "platform": "wordpress", "response": r.json()})
    return _err(f"WordPress {r.status_code}: {r.text}")


# ─── Google My Business ──────────────────────────────────────

async def _post_gmb(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    if not text:
        return _err("text is required")
    if not e("GMB_ACCESS_TOKEN") or not e("GMB_LOCATION_ID"):
        return _err("Set GMB_ACCESS_TOKEN and GMB_LOCATION_ID")
    r = await _http("post",
                     f"https://mybusiness.googleapis.com/v4/{e('GMB_LOCATION_ID')}/localPosts",
                     json={"languageCode": "en", "summary": text,
                           "topicType": "STANDARD"},
                     headers={"Authorization": f"Bearer {e('GMB_ACCESS_TOKEN')}"})
    if r.status_code == 200:
        return _ok({"status": "posted", "platform": "gmb", "response": r.json()})
    return _err(f"GMB {r.status_code}: {r.text}")


# ─── Dribbble ─────────────────────────────────────────────────

async def _post_dribbble(args: dict) -> list[TextContent]:
    title = args.get("title", args.get("text", ""))
    description = args.get("text", "")
    image_url = args.get("image_url", "")
    if not title or not image_url:
        return _err("title and image_url are required")
    if not e("DRIBBBLE_ACCESS_TOKEN"):
        return _err("Set DRIBBBLE_ACCESS_TOKEN")
    r = await _http("post", "https://api.dribbble.com/v2/shots",
                     data={"title": title, "description": description, "image_url": image_url},
                     headers={"Authorization": f"Bearer {e('DRIBBBLE_ACCESS_TOKEN')}"})
    if r.status_code in (200, 201, 202):
        return _ok({"status": "posted", "platform": "dribbble", "response": r.json()})
    return _err(f"Dribbble {r.status_code}: {r.text}")


# ─── Cross-post ───────────────────────────────────────────────

ALL_HANDLERS = {}  # populated below

async def _crosspost(args: dict) -> list[TextContent]:
    text = args.get("text", "")
    platforms = args.get("platforms", [])
    if not text:
        return _err("text is required")
    if not platforms:
        return _err("platforms list is required")
    results = {}
    for p in platforms:
        handler_name = f"post_{p.replace('-', '_').replace('.', '')}"
        h = ALL_HANDLERS.get(handler_name)
        if h:
            r = await h({**args, "text": text})
            results[p] = json.loads(r[0].text)
        else:
            results[p] = {"error": f"Unknown platform: {p}"}
    return _ok({"crosspost_results": results})


# ─── Status ───────────────────────────────────────────────────

PLATFORM_CHECKS = {
    "twitter": lambda: bool(e("TWITTER_ACCESS_TOKEN") and e("TWITTER_API_KEY")),
    "linkedin": lambda: bool(e("LINKEDIN_ACCESS_TOKEN") and e("LINKEDIN_PERSON_ID")),
    "linkedin-page": lambda: bool(e("LINKEDIN_ACCESS_TOKEN") and e("LINKEDIN_PAGE_ID")),
    "facebook": lambda: bool(e("FB_PAGE_ACCESS_TOKEN") and e("FB_PAGE_ID")),
    "instagram": lambda: bool(e("IG_ACCESS_TOKEN") and e("IG_USER_ID")),
    "threads": lambda: bool(e("IG_ACCESS_TOKEN") and (e("THREADS_USER_ID") or e("IG_USER_ID"))),
    "tiktok": lambda: bool(e("TIKTOK_ACCESS_TOKEN")),
    "youtube": lambda: bool(e("YOUTUBE_ACCESS_TOKEN")),
    "reddit": lambda: bool(e("REDDIT_CLIENT_ID") and e("REDDIT_USERNAME")),
    "pinterest": lambda: bool(e("PINTEREST_ACCESS_TOKEN")),
    "discord": lambda: bool(e("DISCORD_WEBHOOK_URL")),
    "slack": lambda: bool(e("SLACK_WEBHOOK_URL")),
    "telegram": lambda: bool(e("TELEGRAM_BOT_TOKEN") and e("TELEGRAM_CHAT_ID")),
    "bluesky": lambda: bool(e("BLUESKY_HANDLE") and e("BLUESKY_APP_PASSWORD")),
    "mastodon": lambda: bool(e("MASTODON_ACCESS_TOKEN")),
    "medium": lambda: bool(e("MEDIUM_ACCESS_TOKEN")),
    "devto": lambda: bool(e("DEVTO_API_KEY")),
    "hashnode": lambda: bool(e("HASHNODE_TOKEN") and e("HASHNODE_PUBLICATION_ID")),
    "wordpress": lambda: bool(e("WORDPRESS_URL") and e("WORDPRESS_USERNAME")),
    "gmb": lambda: bool(e("GMB_ACCESS_TOKEN") and e("GMB_LOCATION_ID")),
    "dribbble": lambda: bool(e("DRIBBBLE_ACCESS_TOKEN")),
}

async def _check_connections(args: dict) -> list[TextContent]:
    connected = {k: v() for k, v in PLATFORM_CHECKS.items()}
    ready = [k for k, v in connected.items() if v]
    not_ready = [k for k, v in connected.items() if not v]
    return _ok({"total_platforms": len(connected), "ready_count": len(ready),
                "ready": ready, "not_configured": not_ready})


# ─── Tool definitions ────────────────────────────────────────

def _t(name, desc, props, req=None):
    return Tool(name=name, description=desc, inputSchema={
        "type": "object", "properties": props, "required": req or list(props.keys())[:1]})

_text = {"text": {"type": "string", "description": "Post text"}}
_text_link = {**_text, "link": {"type": "string", "description": "Optional URL to share"}}
_text_img = {**_text, "image_url": {"type": "string", "description": "Public image URL"}}
_article = {"title": {"type": "string"}, "content": {"type": "string", "description": "Markdown content"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
            "published": {"type": "boolean", "description": "Publish immediately (default: draft)"}}

TOOLS = [
    _t("post_tweet", "Post to Twitter/X (280 char max)", _text),
    _t("get_twitter_me", "Get your Twitter/X profile", {}, []),
    _t("post_linkedin", "Post to LinkedIn (personal)", _text),
    _t("post_linkedin_page", "Post to a LinkedIn Company Page", _text),
    _t("post_facebook", "Post to Facebook Page", _text_link),
    _t("post_instagram", "Post photo to Instagram", {**_text, "image_url": {"type": "string"}}, ["text", "image_url"]),
    _t("post_threads", "Post to Threads", _text),
    _t("post_tiktok", "Post video to TikTok", {**_text, "video_url": {"type": "string"}}, ["text", "video_url"]),
    _t("post_youtube", "Post to YouTube", {"title": {"type": "string"}, "description": {"type": "string"}}, ["title"]),
    _t("post_reddit", "Post to a subreddit", {**_text, "title": {"type": "string"}, "subreddit": {"type": "string"}}, ["title", "subreddit"]),
    _t("post_pinterest", "Create a Pinterest pin", {**_text, "title": {"type": "string"}, "image_url": {"type": "string"},
        "board_id": {"type": "string"}, "link": {"type": "string"}}, ["title", "image_url", "board_id"]),
    _t("post_discord", "Post to Discord via webhook", _text),
    _t("post_slack", "Post to Slack via webhook", _text),
    _t("post_telegram", "Send Telegram message", {**_text, "chat_id": {"type": "string", "description": "Override chat ID"}}, ["text"]),
    _t("post_bluesky", "Post to Bluesky", _text),
    _t("post_mastodon", "Post to Mastodon (toot)", _text),
    _t("post_medium", "Create a Medium article (draft)", _article, ["title", "content"]),
    _t("post_devto", "Create a Dev.to article", _article, ["title", "content"]),
    _t("post_hashnode", "Publish to Hashnode blog", _article, ["title", "content"]),
    _t("post_wordpress", "Create a WordPress post", {**_article, "status": {"type": "string", "enum": ["draft", "publish"], "description": "Post status"}}, ["title", "content"]),
    _t("post_gmb", "Post to Google My Business", _text),
    _t("post_dribbble", "Post a shot to Dribbble", {**_text, "title": {"type": "string"}, "image_url": {"type": "string"}}, ["title", "image_url"]),
    _t("crosspost", "Post to multiple platforms at once", {
        **_text, "platforms": {"type": "array", "items": {"type": "string",
            "enum": ["twitter", "linkedin", "linkedin_page", "facebook", "instagram", "threads",
                     "bluesky", "mastodon", "discord", "slack", "telegram", "reddit", "pinterest",
                     "tiktok", "youtube", "medium", "devto", "hashnode", "wordpress", "gmb", "dribbble"]}}
    }, ["text", "platforms"]),
    _t("check_social_connections", "Check which platforms are configured and ready", {}, []),
]

ALL_HANDLERS = {
    "post_tweet": _post_tweet,
    "get_twitter_me": _get_twitter_me,
    "post_linkedin": _post_linkedin,
    "post_linkedin_page": _post_linkedin_page,
    "post_facebook": _post_facebook,
    "post_instagram": _post_instagram,
    "post_threads": _post_threads,
    "post_tiktok": _post_tiktok,
    "post_youtube": _post_youtube,
    "post_reddit": _post_reddit,
    "post_pinterest": _post_pinterest,
    "post_discord": _post_discord,
    "post_slack": _post_slack,
    "post_telegram": _post_telegram,
    "post_bluesky": _post_bluesky,
    "post_mastodon": _post_mastodon,
    "post_medium": _post_medium,
    "post_devto": _post_devto,
    "post_hashnode": _post_hashnode,
    "post_wordpress": _post_wordpress,
    "post_gmb": _post_gmb,
    "post_dribbble": _post_dribbble,
    "crosspost": _crosspost,
    "check_social_connections": _check_connections,
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = ALL_HANDLERS.get(name)
    if not handler:
        return _err(f"Unknown tool: {name}")
    return await handler(arguments or {})


async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
