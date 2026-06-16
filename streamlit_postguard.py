#!/usr/bin/env python3
"""
PostGuard Web - Streamlit version for iPhone & iPad
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Optional

import streamlit as st
import pandas as pd

try:
    import tweepy
except ImportError:
    tweepy = None

st.set_page_config(page_title="PostGuard Web", page_icon="🛡️", layout="centered", initial_sidebar_state="expanded")

DEFAULT_TOXIC_WORDS = ["example_hate_word", "stupid example", "die in a fire", "crypto scam", "buy my nft"]
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')

def analyze_post(text, created_at, custom_keywords, min_age_days=0, enable_heuristics=True):
    if not text or not text.strip():
        return []
    reasons = []
    text_lower = text.lower()
    text_stripped = text.strip()

    for kw in custom_keywords:
        if kw.lower() in text_lower:
            reasons.append(f"Contains keyword: '{kw}'")
            break

    if not enable_heuristics:
        return reasons

    if text_stripped.isupper() and len(text_stripped) > 25:
        reasons.append("All uppercase (shouting)")

    urls = re.findall(r'https?://\S+', text)
    if len(urls) >= 3:
        reasons.append(f"Multiple URLs ({len(urls)}) — possible spam")

    hashtags = re.findall(r'#\w+', text)
    if len(hashtags) >= 6:
        reasons.append(f"Excessive hashtags ({len(hashtags)})")

    if EMAIL_PATTERN.search(text):
        reasons.append("Contains email address pattern")
    if PHONE_PATTERN.search(text):
        reasons.append("Contains phone number pattern")

    for toxic in DEFAULT_TOXIC_WORDS:
        if toxic.lower() in text_lower:
            reasons.append(f"Contains potentially problematic word: '{toxic}'")
            break

    if created_at and min_age_days > 0:
        now = datetime.now(timezone.utc)
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_at = None
        if created_at:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age = (now - created_at).days
            if age >= min_age_days:
                reasons.append(f"Old post ({age} days)")

    return reasons

def get_x_client(api_key, api_secret, access_token, access_token_secret):
    if tweepy is None:
        st.error("tweepy not installed")
        return None
    if not all([api_key, api_secret, access_token, access_token_secret]):
        st.error("Please fill in all four X API credentials")
        return None
    try:
        client = tweepy.Client(consumer_key=api_key, consumer_secret=api_secret,
                               access_token=access_token, access_token_secret=access_token_secret,
                               wait_on_rate_limit=True)
        me = client.get_me(user_fields=["id", "username", "name"])
        if me and me.data:
            st.success(f"✅ Connected as @{me.data.username}")
            return client
        else:
            st.error("Could not verify credentials")
            return None
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None

def fetch_user_posts(client, max_tweets=100):
    try:
        me = client.get_me()
        user_id = me.data.id
        posts = []
        for tweet in tweepy.Paginator(client.get_users_tweets, id=user_id, max_results=100,
                                      tweet_fields=["id", "text", "created_at", "public_metrics"],
                                      user_auth=True).flatten(limit=max_tweets):
            posts.append({
                "id": str(tweet["id"]),
                "text": tweet.get("text", ""),
                "created_at": tweet.get("created_at"),
            })
        return posts
    except Exception as e:
        st.error(f"Error fetching posts: {e}")
        return []

def main():
    st.title("🛡️ PostGuard Web")
    st.caption("Find & safely delete problematic X posts • Works in Safari on iPhone & iPad")

    with st.sidebar:
        st.header("⚙️ Settings")
        st.subheader("X API Credentials")
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        access_token = st.text_input("Access Token", type="password")
        access_token_secret = st.text_input("Access Token Secret", type="password")

        st.divider()
        max_tweets = st.slider("Max posts to scan", 10, 500, 100, step=10)
        min_age_days = st.number_input("Only flag posts older than (days)", 0, 5000, 0)
        keywords_text = st.text_area("Your problematic keywords (one per line)",
                                     value="old hot take\nembarrassing story\ncrypto promotion", height=100)
        custom_keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]
        enable_heuristics = st.checkbox("Enable extra heuristics", value=True)

    if not all([api_key, api_secret, access_token, access_token_secret]):
        st.info("Enter your X API credentials in the sidebar to begin")
        st.stop()

    if st.button("🔌 Connect & Scan Posts", type="primary", use_container_width=True):
        client = get_x_client(api_key, api_secret, access_token, access_token_secret)
        if client:
            st.session_state["client"] = client
            with st.spinner("Fetching posts..."):
                posts = fetch_user_posts(client, max_tweets)
            if posts:
                st.session_state["all_posts"] = posts
                st.success(f"Fetched {len(posts)} posts")

    if "all_posts" in st.session_state:
        posts = st.session_state["all_posts"]
        client = st.session_state.get("client")

        problematic = []
        for post in posts:
            reasons = analyze_post(post["text"], post.get("created_at"), custom_keywords, min_age_days, enable_heuristics)
            if reasons:
                post_copy = post.copy()
                post_copy["reasons"] = reasons
                post_copy["link"] = f"https://x.com/user/status/{post['id']}"
                problematic.append(post_copy)

        st.metric("Posts Scanned", len(posts))
        st.metric("Flagged as Problematic", len(problematic))

        if problematic:
            df_data = []
            for p in problematic:
                date_str = p["created_at"].strftime("%Y-%m-%d") if p.get("created_at") else "N/A"
                df_data.append({
                    "Date": date_str,
                    "Text": p["text"][:120] + "..." if len(p["text"]) > 120 else p["text"],
                    "Reasons": " | ".join(p["reasons"]),
                    "Link": p["link"],
                    "ID": p["id"]
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={"Link": st.column_config.LinkColumn("Link", display_text="Open on X")})

            st.subheader("Delete Posts")
            selected = st.multiselect("Select Tweet IDs to delete", [p["id"] for p in problematic])
            if selected and st.button("🗑️ DELETE SELECTED", type="primary"):
                deleted_count = 0
                for tid in selected:
                    try:
                        resp = client.delete_tweet(id=tid, user_auth=True)
                        if resp.data.get("deleted"):
                            deleted_count += 1
                    except Exception as e:
                        st.error(f"Failed to delete {tid}: {e}")
                if deleted_count:
                    st.success(f"Deleted {deleted_count} posts!")
                    st.balloons()
                    st.session_state["all_posts"] = [p for p in st.session_state["all_posts"] if p["id"] not in selected]
                    st.rerun()
        else:
            st.success("No problematic posts found!")

if __name__ == "__main__":
    main()