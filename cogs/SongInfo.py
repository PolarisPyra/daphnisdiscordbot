import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from database import get_db_connection

load_dotenv(".env")
URL = os.getenv("URL")

class SongInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor() if self.conn else None
        self.DifficultyMap = {
            0: "EASY",
            1: "ADVANCE",
            2: "EXPERT",
            3: "MASTER",
            4: "ULTIMA",
            5: "WORLDS END"
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print("Song Info Commands ready")

    @app_commands.command(name="songlookup", description="Fetches song info for the provided title and difficulty.")
    @app_commands.describe(title="Enter the song title to see more.", difficulty="Enter the difficulty level (EASY, ADVANCE, EXPERT, MASTER, ULTIMA, WORLDS END).")
    async def songLookup(self, interaction: discord.Interaction, title: str, difficulty: str = None):
        if self.cursor is None:
            await interaction.response.send_message("Database connection failed.", ephemeral=False)
            return

        def getChartIdByDifficulty(difficultyName):
            for chart_id, diff_name in self.DifficultyMap.items():
                if diff_name == difficultyName.upper():
                    return chart_id
            return 3  # Default to MASTER if difficulty is not provided

        if difficulty and difficulty.upper() not in self.DifficultyMap.values():
            await interaction.response.send_message("Invalid difficulty level. Please choose from: EASY, ADVANCE, EXPERT, MASTER, ULTIMA, WORLDS END.", ephemeral=True)
            return

        try:
            if difficulty:
                # If difficulty provided, show just that difficulty
                query = """
                    SELECT
                        chartId,
                        title,
                        level,
                        genre,
                        jacketPath,
                        artist
                    FROM
                        chuni_static_music
                    WHERE
                        title LIKE %s
                        AND chartId = %s
                """
                chart_id = getChartIdByDifficulty(difficulty)
                params = (title, chart_id)
            else:
                # If no difficulty provided, show all difficulties
                query = """
                    SELECT
                        chartId,
                        title,
                        level,
                        genre,
                        jacketPath,
                        artist
                    FROM
                        chuni_static_music
                    WHERE
                        title LIKE %s
                """
                params = (title,)

            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            if rows:
                # Create the embed using first row's common info
                jacketPath = rows[0][4]
                thumbnailURL = f"https://{URL}/jacketArts/{jacketPath.replace('.dds', '.png')}" if jacketPath else None

                embed = discord.Embed(
                    title=f"Song Information: {rows[0][1]}",
                    color=discord.Color.blue()
                )

                if thumbnailURL:
                    embed.set_thumbnail(url=thumbnailURL)

                embed.add_field(name="Title", value=rows[0][1], inline=True)
                embed.add_field(name="Genre", value=rows[0][3], inline=True)
                embed.add_field(name="Artist", value=rows[0][5], inline=True)

                # Add field for each difficulty
                difficulties = ""
                for row in rows:
                    chart_id = row[0]
                    difficulty_name = self.DifficultyMap[chart_id]
                    level = row[2]
                    difficulties += f"{difficulty_name}: Level {level}\n"

                embed.add_field(name="Difficulties", value=difficulties, inline=False)

                await interaction.response.send_message(embed=embed, ephemeral=False)
            else:
                await interaction.response.send_message("No song found with that title.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while fetching the song info.", ephemeral=True)
            print(f"Database error: {e}")
        finally:
            if self.cursor is not None:
                self.cursor.fetchall()

async def setup(bot):
    await bot.add_cog(SongInfo(bot))
