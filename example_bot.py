import os
import discord

from datetime import date
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

users_participating = {}

@client.event
async def on_ready():
    print(f'Starting bot as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.channel.name == '30-day-drawing-challenge':
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(('.png', '.jpg', '.jpeg')):
                    author_name = message.author.name
                    if author_name in users_participating:
                        if users_participating[author_name] == False:
                            await message.channel.send(f'{author_name} has completed the daily challenge!')
                            users_participating[author_name] = True
                            print(users_participating)
                        else:
                            await message.channel.send(f'{author_name}, you have already submitted your drawing for today!')
        if message.content.startswith('$join'):
            author_name = message.author.name
            if author_name not in users_participating:
                users_participating[author_name] = False
                await message.channel.send(f'{author_name} has joined the 30 day drawing challenge!')
            else:
                await message.channel.send(f'{author_name}, you are already participating!')
    
@client.event
async def daily_reminder():
    channel = discord.utils.get(client.get_all_channels(), name='30-day-drawing-challenge')
    for user in users_participating:
        if users_participating[user] == False:
            if channel:
                await channel.send(f"Don't forget to submit your drawing for today, {user}!")


client.run(TOKEN)