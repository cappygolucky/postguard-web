{\rtf1\ansi\ansicpg1252\cocoartf2870
\cocoatextscaling1\cocoaplatform1{\fonttbl\f0\fnil\fcharset0 .AppleSystemUIFontMonospaced-Regular;}
{\colortbl;\red255\green255\blue255;\red124\green124\blue124;\red248\green248\blue248;\red168\green255\blue96;
\red150\green203\blue254;\red255\green255\blue182;\red198\green197\blue254;\red255\green115\blue253;\red218\green239\blue163;
}
{\*\expandedcolortbl;;\cssrgb\c48627\c48627\c48627;\cssrgb\c97255\c97255\c97255;\cssrgb\c65882\c100000\c37647;
\cssrgb\c58824\c79608\c99608;\cssrgb\c100000\c100000\c71373;\cssrgb\c77647\c77255\c99608;\cssrgb\c100000\c45098\c99216;\cssrgb\c85490\c93725\c63922;
}
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\slleading100\pardirnatural\partightenfactor0

\f0\fs26 \cf2 #!/usr/bin/env python3\cf3 \
\cf4 """\
PostGuard Web - Streamlit version for iPhone & iPad\
"""\cf3 \
\
\cf5 import\cf3  re\
\cf5 from\cf3  datetime \cf5 import\cf3  datetime, timezone\
\cf5 from\cf3  typing \cf5 import\cf3  \cf6 List\cf3 , \cf6 Dict\cf3 , \cf6 Optional\cf3 \
\
\cf5 import\cf3  streamlit \cf5 as\cf3  st\
\cf5 import\cf3  pandas \cf5 as\cf3  pd\
\
\cf5 try\cf3 :\
    \cf5 import\cf3  tweepy\
\cf5 except\cf3  ImportError:\
    tweepy = \cf7 None\cf3 \
\
st.set_page_config(page_title=\cf4 "PostGuard Web"\cf3 , page_icon=\cf4 "\uc0\u55357 \u57057 \u65039 "\cf3 , layout=\cf4 "centered"\cf3 , initial_sidebar_state=\cf4 "expanded"\cf3 )\
\
DEFAULT_TOXIC_WORDS = [\cf4 "example_hate_word"\cf3 , \cf4 "stupid example"\cf3 , \cf4 "die in a fire"\cf3 , \cf4 "crypto scam"\cf3 , \cf4 "buy my nft"\cf3 ]\
EMAIL_PATTERN = re.compile(\cf4 r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]\{2,\}\\b'\cf3 )\
PHONE_PATTERN = re.compile(\cf4 r'\\b(?:\\+?1[-.\\s]?)?\\(?\\d\{3\}\\)?[-.\\s]?\\d\{3\}[-.\\s]?\\d\{4\}\\b'\cf3 )\
\
\cf5 def\cf3  analyze_post(text, created_at, custom_keywords, min_age_days=\cf8 0\cf3 , enable_heuristics=\cf7 True\cf3 ):\
    \cf5 if\cf3  \cf5 not\cf3  text \cf5 or\cf3  \cf5 not\cf3  text.strip():\
        \cf5 return\cf3  []\
    reasons = []\
    text_lower = text.lower()\
    text_stripped = text.strip()\
\
    \cf5 for\cf3  kw \cf5 in\cf3  custom_keywords:\
        \cf5 if\cf3  kw.lower() \cf5 in\cf3  text_lower:\
            reasons.append(\cf4 f"Contains keyword: '\cf9 \{kw\}\cf4 '"\cf3 )\
            \cf5 break\cf3 \
\
    \cf5 if\cf3  \cf5 not\cf3  enable_heuristics:\
        \cf5 return\cf3  reasons\
\
    \cf5 if\cf3  text_stripped.isupper() \cf5 and\cf3  len(text_stripped) > \cf8 25\cf3 :\
        reasons.append(\cf4 "All uppercase (shouting)"\cf3 )\
\
    urls = re.findall(\cf4 r'https?://\\S+'\cf3 , text)\
    \cf5 if\cf3  len(urls) >= \cf8 3\cf3 :\
        reasons.append(\cf4 f"Multiple URLs (\cf9 \{len(urls)\}\cf4 ) \'97 possible spam"\cf3 )\
\
    hashtags = re.findall(\cf4 r'#\\w+'\cf3 , text)\
    \cf5 if\cf3  len(hashtags) >= \cf8 6\cf3 :\
        reasons.append(\cf4 f"Excessive hashtags (\cf9 \{len(hashtags)\}\cf4 )"\cf3 )\
\
    \cf5 if\cf3  EMAIL_PATTERN.search(text):\
        reasons.append(\cf4 "Contains email address pattern"\cf3 )\
    \cf5 if\cf3  PHONE_PATTERN.search(text):\
        reasons.append(\cf4 "Contains phone number pattern"\cf3 )\
\
    \cf5 for\cf3  toxic \cf5 in\cf3  DEFAULT_TOXIC_WORDS:\
        \cf5 if\cf3  toxic.lower() \cf5 in\cf3  text_lower:\
            reasons.append(\cf4 f"Contains potentially problematic word: '\cf9 \{toxic\}\cf4 '"\cf3 )\
            \cf5 break\cf3 \
\
    \cf5 if\cf3  created_at \cf5 and\cf3  min_age_days > \cf8 0\cf3 :\
        now = datetime.now(timezone.utc)\
        \cf5 if\cf3  isinstance(created_at, str):\
            \cf5 try\cf3 :\
                created_at = datetime.fromisoformat(created_at.replace(\cf4 'Z'\cf3 , \cf4 '+00:00'\cf3 ))\
            \cf5 except\cf3 :\
                created_at = \cf7 None\cf3 \
        \cf5 if\cf3  created_at:\
            \cf5 if\cf3  created_at.tzinfo \cf5 is\cf3  \cf7 None\cf3 :\
                created_at = created_at.replace(tzinfo=timezone.utc)\
            age = (now - created_at).days\
            \cf5 if\cf3  age >= min_age_days:\
                reasons.append(\cf4 f"Old post (\cf9 \{age\}\cf4  days)"\cf3 )\
\
    \cf5 return\cf3  reasons\
\
\cf5 def\cf3  get_x_client(api_key, api_secret, access_token, access_token_secret):\
    \cf5 if\cf3  tweepy \cf5 is\cf3  \cf7 None\cf3 :\
        st.error(\cf4 "tweepy not installed"\cf3 )\
        \cf5 return\cf3  \cf7 None\cf3 \
    \cf5 if\cf3  \cf5 not\cf3  all([api_key, api_secret, access_token, access_token_secret]):\
        st.error(\cf4 "Please fill in all four X API credentials"\cf3 )\
        \cf5 return\cf3  \cf7 None\cf3 \
    \cf5 try\cf3 :\
        client = tweepy.Client(consumer_key=api_key, consumer_secret=api_secret,\
                               access_token=access_token, access_token_secret=access_token_secret,\
                               wait_on_rate_limit=\cf7 True\cf3 )\
        me = client.get_me(user_fields=[\cf4 "id"\cf3 , \cf4 "username"\cf3 , \cf4 "name"\cf3 ])\
        \cf5 if\cf3  me \cf5 and\cf3  me.data:\
            st.success(\cf4 f"\uc0\u9989  Connected as @\cf9 \{me.data.username\}\cf4 "\cf3 )\
            \cf5 return\cf3  client\
        \cf5 else\cf3 :\
            st.error(\cf4 "Could not verify credentials"\cf3 )\
            \cf5 return\cf3  \cf7 None\cf3 \
    \cf5 except\cf3  Exception \cf5 as\cf3  e:\
        st.error(\cf4 f"Authentication failed: \cf9 \{e\}\cf4 "\cf3 )\
        \cf5 return\cf3  \cf7 None\cf3 \
\
\cf5 def\cf3  fetch_user_posts(client, max_tweets=\cf8 100\cf3 ):\
    \cf5 try\cf3 :\
        me = client.get_me()\
        user_id = me.data.id\
        posts = []\
        \cf5 for\cf3  tweet \cf5 in\cf3  tweepy.Paginator(client.get_users_tweets, id=user_id, max_results=\cf8 100\cf3 ,\
                                      tweet_fields=[\cf4 "id"\cf3 , \cf4 "text"\cf3 , \cf4 "created_at"\cf3 , \cf4 "public_metrics"\cf3 ],\
                                      user_auth=\cf7 True\cf3 ).flatten(limit=max_tweets):\
            posts.append(\{\
                \cf4 "id"\cf3 : str(tweet[\cf4 "id"\cf3 ]),\
                \cf4 "text"\cf3 : tweet.get(\cf4 "text"\cf3 , \cf4 ""\cf3 ),\
                \cf4 "created_at"\cf3 : tweet.get(\cf4 "created_at"\cf3 ),\
            \})\
        \cf5 return\cf3  posts\
    \cf5 except\cf3  Exception \cf5 as\cf3  e:\
        st.error(\cf4 f"Error fetching posts: \cf9 \{e\}\cf4 "\cf3 )\
        \cf5 return\cf3  []\
\
\cf5 def\cf3  main():\
    st.title(\cf4 "\uc0\u55357 \u57057 \u65039  PostGuard Web"\cf3 )\
    st.caption(\cf4 "Find & safely delete problematic X posts \'95 Works in Safari on iPhone & iPad"\cf3 )\
\
    \cf5 with\cf3  st.sidebar:\
        st.header(\cf4 "\uc0\u9881 \u65039  Settings"\cf3 )\
        st.subheader(\cf4 "X API Credentials"\cf3 )\
        api_key = st.text_input(\cf4 "API Key"\cf3 , type=\cf4 "password"\cf3 )\
        api_secret = st.text_input(\cf4 "API Secret"\cf3 , type=\cf4 "password"\cf3 )\
        access_token = st.text_input(\cf4 "Access Token"\cf3 , type=\cf4 "password"\cf3 )\
        access_token_secret = st.text_input(\cf4 "Access Token Secret"\cf3 , type=\cf4 "password"\cf3 )\
\
        st.divider()\
        max_tweets = st.slider(\cf4 "Max posts to scan"\cf3 , \cf8 10\cf3 , \cf8 500\cf3 , \cf8 100\cf3 , step=\cf8 10\cf3 )\
        min_age_days = st.number_input(\cf4 "Only flag posts older than (days)"\cf3 , \cf8 0\cf3 , \cf8 5000\cf3 , \cf8 0\cf3 )\
        keywords_text = st.text_area(\cf4 "Your problematic keywords (one per line)"\cf3 ,\
                                     value=\cf4 "old hot take\\nembarrassing story\\ncrypto promotion"\cf3 , height=\cf8 100\cf3 )\
        custom_keywords = [k.strip() \cf5 for\cf3  k \cf5 in\cf3  keywords_text.split(\cf4 "\\n"\cf3 ) \cf5 if\cf3  k.strip()]\
        enable_heuristics = st.checkbox(\cf4 "Enable extra heuristics"\cf3 , value=\cf7 True\cf3 )\
\
    \cf5 if\cf3  \cf5 not\cf3  all([api_key, api_secret, access_token, access_token_secret]):\
        st.info(\cf4 "Enter your X API credentials in the sidebar to begin"\cf3 )\
        st.stop()\
\
    \cf5 if\cf3  st.button(\cf4 "\uc0\u55357 \u56588  Connect & Scan Posts"\cf3 , type=\cf4 "primary"\cf3 , use_container_width=\cf7 True\cf3 ):\
        client = get_x_client(api_key, api_secret, access_token, access_token_secret)\
        \cf5 if\cf3  client:\
            st.session_state[\cf4 "client"\cf3 ] = client\
            \cf5 with\cf3  st.spinner(\cf4 "Fetching posts..."\cf3 ):\
                posts = fetch_user_posts(client, max_tweets)\
            \cf5 if\cf3  posts:\
                st.session_state[\cf4 "all_posts"\cf3 ] = posts\
                st.success(\cf4 f"Fetched \cf9 \{len(posts)\}\cf4  posts"\cf3 )\
\
    \cf5 if\cf3  \cf4 "all_posts"\cf3  \cf5 in\cf3  st.session_state:\
        posts = st.session_state[\cf4 "all_posts"\cf3 ]\
        client = st.session_state.get(\cf4 "client"\cf3 )\
\
        problematic = []\
        \cf5 for\cf3  post \cf5 in\cf3  posts:\
            reasons = analyze_post(post[\cf4 "text"\cf3 ], post.get(\cf4 "created_at"\cf3 ), custom_keywords, min_age_days, enable_heuristics)\
            \cf5 if\cf3  reasons:\
                post_copy = post.copy()\
                post_copy[\cf4 "reasons"\cf3 ] = reasons\
                post_copy[\cf4 "link"\cf3 ] = \cf4 f"https://x.com/user/status/\cf9 \{post[\cf4 'id'\cf9 ]\}\cf4 "\cf3 \
                problematic.append(post_copy)\
\
        st.metric(\cf4 "Posts Scanned"\cf3 , len(posts))\
        st.metric(\cf4 "Flagged as Problematic"\cf3 , len(problematic))\
\
        \cf5 if\cf3  problematic:\
            df_data = []\
            \cf5 for\cf3  p \cf5 in\cf3  problematic:\
                date_str = p[\cf4 "created_at"\cf3 ].strftime(\cf4 "%Y-%m-%d"\cf3 ) \cf5 if\cf3  p.get(\cf4 "created_at"\cf3 ) \cf5 else\cf3  \cf4 "N/A"\cf3 \
                df_data.append(\{\
                    \cf4 "Date"\cf3 : date_str,\
                    \cf4 "Text"\cf3 : p[\cf4 "text"\cf3 ][:\cf8 120\cf3 ] + \cf4 "..."\cf3  \cf5 if\cf3  len(p[\cf4 "text"\cf3 ]) > \cf8 120\cf3  \cf5 else\cf3  p[\cf4 "text"\cf3 ],\
                    \cf4 "Reasons"\cf3 : \cf4 " | "\cf3 .join(p[\cf4 "reasons"\cf3 ]),\
                    \cf4 "Link"\cf3 : p[\cf4 "link"\cf3 ],\
                    \cf4 "ID"\cf3 : p[\cf4 "id"\cf3 ]\
                \})\
            df = pd.DataFrame(df_data)\
            st.dataframe(df, use_container_width=\cf7 True\cf3 , hide_index=\cf7 True\cf3 ,\
                         column_config=\{\cf4 "Link"\cf3 : st.column_config.LinkColumn(\cf4 "Link"\cf3 , display_text=\cf4 "Open on X"\cf3 )\})\
\
            st.subheader(\cf4 "Delete Posts"\cf3 )\
            selected = st.multiselect(\cf4 "Select Tweet IDs to delete"\cf3 , [p[\cf4 "id"\cf3 ] \cf5 for\cf3  p \cf5 in\cf3  problematic])\
            \cf5 if\cf3  selected \cf5 and\cf3  st.button(\cf4 "\uc0\u55357 \u56785 \u65039  DELETE SELECTED"\cf3 , type=\cf4 "primary"\cf3 ):\
                deleted_count = \cf8 0\cf3 \
                \cf5 for\cf3  tid \cf5 in\cf3  selected:\
                    \cf5 try\cf3 :\
                        resp = client.delete_tweet(id=tid, user_auth=\cf7 True\cf3 )\
                        \cf5 if\cf3  resp.data.get(\cf4 "deleted"\cf3 ):\
                            deleted_count += \cf8 1\cf3 \
                    \cf5 except\cf3  Exception \cf5 as\cf3  e:\
                        st.error(\cf4 f"Failed to delete \cf9 \{tid\}\cf4 : \cf9 \{e\}\cf4 "\cf3 )\
                \cf5 if\cf3  deleted_count:\
                    st.success(\cf4 f"Deleted \cf9 \{deleted_count\}\cf4  posts!"\cf3 )\
                    st.balloons()\
                    st.session_state[\cf4 "all_posts"\cf3 ] = [p \cf5 for\cf3  p \cf5 in\cf3  st.session_state[\cf4 "all_posts"\cf3 ] \cf5 if\cf3  p[\cf4 "id"\cf3 ] \cf5 not\cf3  \cf5 in\cf3  selected]\
                    st.rerun()\
        \cf5 else\cf3 :\
            st.success(\cf4 "No problematic posts found!"\cf3 )\
\
\cf5 if\cf3  __name__ == \cf4 "__main__"\cf3 :\
    main()}