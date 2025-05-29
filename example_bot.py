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
time_reminder = datetime.time(hour=19, minute=00, tzinfo=cest)
time_reset = datetime.time(hour=24, minute=00, tzinfo=cest)
time_end = datetime.now(tz=cest) + datetime.timedelta(days=30)

current_challenge = None

class Challenge():
    def __init__(self):
        self.users_participating = {}
        self.time_end = datetime.now(tz=cest) + datetime.timedelta(days=30)

    def join(self, user):
        self.users_participating[user] = False

    def leave(self, user):
        if user in self.users_participating:
            del self.users_participating[user]

    def reset(self, user):
        if user in self.users_participating:
            self.users_participating[user] = False

    def reset_all(self):
        for user in self.users_participating:
            self.users_participating[user] = False

    def get_status(self, user):
        return self.users_participating.get(user, None)

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
        if current_challenge:
            for user in current_challenge.users_participating:
                if current_challenge.get_status(user) == False:
                    if channel:
                        await channel.send(f"Don't forget to submit your drawing for today, {user.mention}!")

    '''Users' participation statuses reset at midnight by default'''
    @tasks.loop(time=time_reset)
    async def reset_users(self):
        for user in current_challenge.users_participating:
            if current_challenge.get_status(user) == True:
                current_challenge.reset(user)
    
    @tasks.loop(time=time_end)
    async def end_challenge(self):
        if current_challenge:
            channel = discord.utils.get(self.bot.get_all_channels(), name='30-days-challenge')
            if channel:
                await channel.send("The 30 day drawing challenge has ended! Thank you for participating!")
            global current_challenge
            current_challenge = None

    async def update_reminder_time(self, new_time):
        self.reminder.change_interval(time=new_time)

    async def update_reset_time(self, new_time):
        self.reset_users.change_interval(time=new_time)

    async def update_end_time(self, new_time):
        self.end_challenge.change_interval(time=new_time)

@bot.command('startChallenge')
async def start_challenge(ctx):
    if ctx.channel.name == '30-days-challenge':
        global current_challenge
        if current_challenge is None:
            current_challenge = Challenge()
            await bot.get_cog('Reminder').update_end_time(current_challenge.time_end)
            await ctx.send('A 30 day drawing challenge has been started! Use `$join` to participate.')
        else:
            await ctx.send('A challenge is already in progress. Use `$join` to participate.')

@bot.command('stopChallenge')
async def stop_challenge(ctx):
    global current_challenge
    if ctx.channel.name == '30-days-challenge':
        if current_challenge:
            current_challenge = None
            await ctx.send('The 30 day drawing challenge has been stopped.')
        else:
            await ctx.send('No challenge is currently in progress. Use `$startChallenge` to start a new one.')

@bot.command('setReminderTime')
async def set_reminder_time(ctx, arg):
    if ctx.channel.name == '30-days-challenge':
        try:
            hour, minute = map(int, arg.split(':'))
            time_reminder = datetime.time(hour=hour, minute=minute, tzinfo=cest)
            await bot.get_cog('Reminder').update_reminder_time(time_reminder)
            await ctx.send(f'Daily reminder time set to {time_reminder.strftime("%H:%M")}.')
        except ValueError:
            await ctx.send('Please provide the time in the HH:MM format.')

@bot.command('setResetTime')
async def set_reset_time(ctx, arg):
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
        global current_challenge
        if current_challenge:
            member = member or ctx.author
            if member not in current_challenge.users_participating:
                current_challenge.join(member)
                await ctx.send(f'{member.name} has joined the 30 day drawing challenge!')
            else:
                await ctx.send(f'{member.name}, you are already participating!')
        else:
            await ctx.send('No challenge is currently in progress. Use `$startChallenge` to start a new one.')

@bot.command()
async def leave(ctx, *args, member: discord.Member = None):
    if ctx.channel.name == '30-days-challenge':
        global current_challenge
        if current_challenge:
            member = member or ctx.author
            if member in current_challenge.users_participating:
                current_challenge.leave(member)
                await ctx.send(f'{member.name} has left the 30 day drawing challenge!')
            else:
                await ctx.send(f'{member.name}, you are not participating!')
        else:
            await ctx.send('No challenge is currently in progress. Use `$startChallenge` to start a new one.')

@bot.command('resetMe')
async def reset_me(ctx):
    if ctx.channel.name == '30-days-challenge':
        global current_challenge
        if current_challenge:
            author = ctx.author
            if author in current_challenge.users_participating:
                current_challenge.reset(author)
                await ctx.send(f'{author.name}, your participation has been reset for today\'s challenge!')
            else:
                await ctx.send(f'{author.name}, you are not participating in the challenge!')
        else:
            await ctx.send('No challenge is currently in progress. Use `$startChallenge` to start a new one.')

@bot.command('resetAllDaily')
async def reset_all_daily(ctx):
    if ctx.channel.name == '30-days-challenge':
        global current_challenge
        if current_challenge:
            for user in current_challenge.users_participating:
                current_challenge.reset(user)
            await ctx.send('All users have been reset for today\'s challenge!')
        else:
            await ctx.send('No challenge is currently in progress. Use `$startChallenge` to start a new one.')

@bot.command('resetAll') 
async def reset_all(ctx):
    if ctx.channel.name == '30-days-challenge':
        global current_challenge
        if current_challenge:
            current_challenge.users_participating.clear()
            await ctx.send(f'All users have been removed from the 30 day drawing challenge!')
        else:
            await ctx.send('No challenge is currently in progress. Use `$startChallenge` to start a new one.')

@bot.command('myStatus')
async def my_status(ctx):
    if ctx.channel.name == '30-days-challenge':
        global current_challenge
        if current_challenge:
            author = ctx.author
            if author in current_challenge.users_participating:
                status = 'submitted' if current_challenge.get_status(author) else 'not submitted'
                await ctx.send(f'{author.name}, you have {status} your daily drawing today.')
            else:
                await ctx.send(f'{author.name}, you are not participating in the challenge!')
        else:
            await ctx.send('No challenge is currently in progress. Use `$startChallenge` to start a new one.')

@bot.command()
async def info(ctx):
    if ctx.channel.name == '30-days-challenge':
        await ctx.send(
            "This is a 30 day drawing challenge bot.\n"
            "Available commands:\n"
            "`$startChallenge` - Start a new challenge\n"
            "`$stopChallenge` - Stop the current challenge\n"
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
        global current_challenge
        if current_challenge:
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.endswith(('.png', '.jpg', '.jpeg')):
                        author = message.author
                        if author in current_challenge.users_participating:
                            if current_challenge.get_status(author) == False:
                                await message.channel.send(f'{author.name} has completed the daily challenge!')
                                current_challenge.users_participating[author] = True
                            else:
                                await message.channel.send(f'{author.name}, you have already submitted your drawing for today!')

    await bot.process_commands(message)

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)