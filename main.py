import os
import discord
import requests
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")

intents = discord.Intents.default()

last_tweet_id = None
user_id = None  # Cache user ID supaya gak request berulang

async def check_tweets():
    global last_tweet_id, user_id
    await client.wait_until_ready()
    while not client.is_closed():
        print("[DEBUG] Mengecek tweet terbaru...")

        headers = {
            "Authorization": f"Bearer {TWITTER_BEARER}"
        }

        # Request user ID sekali saja
        if user_id is None:
            user_res = requests.get(
                f"https://api.twitter.com/2/users/by/username/{TWITTER_USERNAME}",
                headers=headers
            )
            if user_res.status_code != 200:
                print("❌ Gagal ambil user:", user_res.text)
                await asyncio.sleep(60)
                continue
            user_id = user_res.json()["data"]["id"]
            print(f"[DEBUG] User ID didapat: {user_id}")

        tweet_res = requests.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets?max_results=5&tweet.fields=created_at&expansions=attachments.media_keys&media.fields=url,preview_image_url",
            headers=headers
        )

        if tweet_res.status_code == 429:
            print("⚠️ Rate limit hit. Menunggu 5 menit sebelum coba lagi.")
            await asyncio.sleep(300)  # Delay lama untuk menghindari ban
            continue
        elif tweet_res.status_code != 200:
            print("❌ Gagal ambil tweet:", tweet_res.text)
            await asyncio.sleep(60)
            continue

        data = tweet_res.json()
        if "data" not in data:
            print("[DEBUG] Tidak ada data tweet.")
            await asyncio.sleep(60)
            continue

        tweet = data["data"][0]
        tweet_id = tweet["id"]
        print(f"[DEBUG] Tweet terbaru ID: {tweet_id}")

        if last_tweet_id is None or tweet_id != last_tweet_id:
            print(f"[DEBUG] Kirim embed tweet baru: {tweet_id}")
            last_tweet_id = tweet_id
            tweet_url = f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}"
            embed = discord.Embed(
                title=f"Tweet baru dari @{TWITTER_USERNAME}",
                description=tweet["text"],
                url=tweet_url,
                color=0x1DA1F2
            )

            # Tambahkan media jika ada
            if "includes" in data and "media" in data["includes"]:
                media = data["includes"]["media"][0]
                if "url" in media:
                    embed.set_image(url=media["url"])
                elif "preview_image_url" in media:
                    embed.set_image(url=media["preview_image_url"])

            channel = client.get_channel(CHANNEL_ID)
            await channel.send(embed=embed)
        else:
            print(f"[DEBUG] Tidak ada tweet baru (sama dengan sebelumnya): {tweet_id}")

        await asyncio.sleep(120)  # Cek tiap 2 menit agar aman dari rate limit

class MyClient(discord.Client):
    async def setup_hook(self):
        self.bg_task = asyncio.create_task(check_tweets())

    async def on_ready(self):
        print(f'✅ Bot {self.user} is now running.')

client = MyClient(intents=intents)
client.run(TOKEN)
        
