import os
import discord
import tweepy
import asyncio
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Twitter API Keys
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# Discord Token dan Config
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")

# Setup Twitter API
auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
twitter_api = tweepy.API(auth)

# Setup Discord Client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

last_tweet_id = None

def get_tweet_url(username, tweet_id):
    return f"https://twitter.com/{username}/status/{tweet_id}"

def extract_media_url(tweet):
    media = tweet.entities.get('media', [])
    if media:
        return media[0]['media_url_https']
    return None

async def check_tweets():
    global last_tweet_id
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    while not client.is_closed():
        try:
            tweets = twitter_api.user_timeline(
                screen_name=TWITTER_USERNAME,
                count=1,
                tweet_mode='extended',
                exclude_replies=True,
                include_rts=False
            )
            if tweets:
                tweet = tweets[0]
                if tweet.id != last_tweet_id:
                    last_tweet_id = tweet.id
                    tweet_url = get_tweet_url(TWITTER_USERNAME, tweet.id)
                    media_url = extract_media_url(tweet)

                    embed = discord.Embed(
                        title=f"🕊️ Tweet Baru dari @{TWITTER_USERNAME}",
                        description=tweet.full_text,
                        url=tweet_url,
                        color=discord.Color.blue()
                    )

                    embed.set_author(
                        name=tweet.user.name,
                        icon_url=tweet.user.profile_image_url_https,
                        url=f"https://twitter.com/{TWITTER_USERNAME}"
                    )

                    if media_url:
                        embed.set_image(url=media_url)

                    embed.set_footer(
                        text="Twitter",
                        icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
                    )
                    embed.timestamp = tweet.created_at

                    await channel.send(embed=embed)
        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(60)
import asyncio

class MyClient(discord.Client):
    async def setup_hook(self):
        self.bg_task = asyncio.create_task(check_tweets())

    async def on_ready(self):
        print(f'✅ Bot {self.user} is now running.')

client = MyClient(intents=intents)
client.run(DISCORD_TOKEN)
