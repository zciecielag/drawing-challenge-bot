import os
import discord
from dotenv import load_dotenv
from datetime import date

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

users_participating = []

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
                    await message.channel.send(f'{author_name} has completed the daily challenge!')
                    users_participating[author_name] = True
                    break
    
@client._schedule_event
async def daily_reminder():
    channel = discord.utils.get(client.get_all_channels(), name='30-day-drawing-challenge')
    for user in users_participating:
        if users_participating[user] == False:
            if channel:
                await channel.send(f"Don't forget to submit your drawing for today, {user}!")

client.run(TOKEN)