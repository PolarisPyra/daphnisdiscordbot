import discord
from discord.ext import commands,tasks
import os
import asyncio
from itertools import cycle
import logging
from dotenv import load_dotenv

load_dotenv(".env")
TOKEN = os.getenv("DISCORD_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())


@bot.event
async def on_ready():
    print("Bot Ready")
    print("https://discord.com/oauth2/authorize?client_id=1164707967619305482&permissions=8&integration_type=0&scope=bot+applications.commands")
    try:
        synced_commands = await bot.tree.sync()
        print(f"Synced {len(synced_commands)} commands.")
    except Exception as e:
        print("An error happened while syncing commands",e)


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loaded cog: {filename[:-3]}")


async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)

asyncio.run(main())
