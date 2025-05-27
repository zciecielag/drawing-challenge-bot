import os
import discord
import logging
import datetime

from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='$', intents=intents)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

cest = ZoneInfo("Europe/Warsaw")
time = datetime.time(hour=19, minute=00, tzinfo=cest)

users_participating = {}

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    async def daily_reminder(self):
        channel = discord.utils.get(client.get_all_channels(), name='30-day-drawing-challenge')
        for user in users_participating:
            if users_participating[user] == False:
                if channel:
                    await channel.send(f"Don't forget to submit your drawing for today, {user.mention}!")

    @tasks.loop(time=time)
    async def my_task(self):
        await self.daily_reminder()

@client.event
async def on_ready():
    print(f'Starting bot as {client.user}')
    await bot.add_cog(Reminder(bot))

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
                    author = message.author
                    if author in users_participating:
                        if users_participating[author] == False:
                            await message.channel.send(f'{author.name} has completed the daily challenge!')
                            users_participating[author] = True
                            print(users_participating)
                        else:
                            await message.channel.send(f'{author.name}, you have already submitted your drawing for today!')
        if message.content.startswith('$join'):
            author = message.author
            if author not in users_participating:
                users_participating[author] = False
                await message.channel.send(f'{author.name} has joined the 30 day drawing challenge!')
            else:
                await message.channel.send(f'{author.name}, you are already participating!')


client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)