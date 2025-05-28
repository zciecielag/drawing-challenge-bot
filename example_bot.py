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

bot = commands.Bot(command_prefix='$', intents=intents)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

cest = ZoneInfo("Europe/Warsaw")
time_reminder = datetime.time(hour=13, minute=31, tzinfo=cest)
time_reset = datetime.time(hour=13, minute=2, tzinfo=cest)

users_participating = {}

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder.start()
        self.reset_users.start()

    def cog_unload(self):
        self.reminder.cancel()
        self.reset_users.cancel()
        
    @tasks.loop(time=time_reminder)
    async def reminder(self):
        channel = discord.utils.get(self.bot.get_all_channels(), name='30-days-challenge')
        for user in users_participating:
            if users_participating[user] == False:
                if channel:
                    await channel.send(f"Don't forget to submit your drawing for today, {user.mention}!")

    '''Users' participation statuses reset at midnight by default'''
    @tasks.loop(time=time_reset)
    async def reset_users(self):
        for user in users_participating:
            if users_participating[user] == True:
                users_participating[user] = False

    async def update_reminder_time(self, new_time):
        self.reminder.change_interval(time=new_time)

    async def update_reset_time(self, new_time):
        self.reset_users.change_interval(time=new_time)

@bot.command()
async def setReminderTime(ctx, arg):
    if ctx.channel.name == '30-days-challenge':
        try:
            hour, minute = map(int, arg.split(':'))
            time_reminder = datetime.time(hour=hour, minute=minute, tzinfo=cest)
            await bot.get_cog('Reminder').update_reminder_time(time_reminder)
            await ctx.send(f'Daily reminder time set to {time_reminder.strftime("%H:%M")}.')
        except ValueError:
            await ctx.send('Please provide the time in the HH:MM format.')

@bot.command()
async def setResetTime(ctx, arg):
    if ctx.channel.name == '30-days-challenge':
        try:
            hour, minute = map(int, arg.split(':'))
            time_reset = datetime.time(hour=hour, minute=minute, tzinfo=cest)
            await bot.get_cog('Reminder').update_reset_time(time_reset)
            await ctx.send(f'Daily reset time set to {time_reset.strftime("%H:%M")}.')
        except ValueError:
            await ctx.send('Please provide the time in the HH:MM format.')

@bot.command()
async def join(ctx, *args, member: discord.Member = None):
    if ctx.channel.name == '30-days-challenge':
        member = member or ctx.author
        if member not in users_participating:
            users_participating[member] = False
            await ctx.send(f'{member.name} has joined the 30 day drawing challenge!')
        else:
            await ctx.send(f'{member.name}, you are already participating!')

@bot.command()
async def leave(ctx, *args, member: discord.Member = None):
    if ctx.channel.name == '30-days-challenge':
        member = member or ctx.author
        if member in users_participating:
            del users_participating[member]
            await ctx.send(f'{member.name} has left the 30 day drawing challenge!')
        else:
            await ctx.send(f'{member.name}, you are not participating!')

@bot.command()
async def resetMe(ctx):
    if ctx.channel.name == '30-days-challenge':
        author = ctx.author
        if author in users_participating:
            users_participating[author] = False
            await ctx.send(f'{author.name}, your participation has been reset for today\'s challenge!')
        else:
            await ctx.send(f'{author.name}, you are not participating in the challenge!')

@bot.command()
async def resetAllDaily(ctx):
    if ctx.channel.name == '30-days-challenge':
        for user in users_participating:
            users_participating[user] = False
        await ctx.send('All users have been reset for today\'s challenge!')

@bot.command() 
async def resetAll(ctx):
    if ctx.channel.name == '30-days-challenge':
        users_participating.clear()
        await ctx.send(f'All users have been removed from the 30 day drawing challenge!')

@bot.command()
async def myStatus(ctx):
    if ctx.channel.name == '30-days-challenge':
        author = ctx.author
        if author in users_participating:
            status = 'submitted' if users_participating[author] else 'not submitted'
            await ctx.send(f'{author.name}, you have {status} your daily drawing today.')
        else:
            await ctx.send(f'{author.name}, you are not participating in the challenge!')

@bot.command()
async def info(ctx):
    if ctx.channel.name == '30-days-challenge':
        await ctx.send(
            "This is a 30 day drawing challenge bot.\n"
            "Available commands:\n"
            "`$join` - Join the challenge\n"
            "`$leave` - Leave the challenge\n"
            "`$resetMe` - Reset your participation for today\n"
            "`$resetAllDaily` - Reset all users' participation for today\n"
            "`$resetAll` - Remove all users from the challenge\n"
            "`$myStatus` - Check your participation status\n"
            "`$setReminderTime HH:MM` - Set the daily reminder time\n"
            "`$setResetTime HH:MM` - Set the daily reset time\n"
            "`$info` - Display this information"
        )

@bot.event
async def on_ready():
    print(f'Starting bot as {bot.user}')
    await bot.add_cog(Reminder(bot))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name == '30-days-challenge':
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(('.png', '.jpg', '.jpeg')):
                    author = message.author
                    if author in users_participating:
                        if users_participating[author] == False:
                            await message.channel.send(f'{author.name} has completed the daily challenge!')
                            users_participating[author] = True
                        else:
                            await message.channel.send(f'{author.name}, you have already submitted your drawing for today!')

    await bot.process_commands(message)


bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)