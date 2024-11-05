import os
import discord
from discord import app_commands
from discord.ext import commands
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv(".env")
URL: str = os.getenv("URL")

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
            # starts at 0 
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
            chart_id = getChartIdByDifficulty(difficulty) if difficulty else 3
            params = (title, chart_id)

            self.cursor.execute(query, params)
            row = self.cursor.fetchone()

            if row is not None:
                
                # Setting up the embed
                jacketPath = row[4]  
                thumbnailURL = f"https://{URL}/jacketArts/{jacketPath.replace('.dds', '.png')}" if jacketPath else None
                level = row[2]
                difficultyName = difficulty.upper() if difficulty else "MASTER"
                difficultyWithLevel = f"{difficultyName} (Level {level})"
                
                # Create the embed
                embed = discord.Embed(
                    title=f"Song Information: {row[1]}",
                    color=discord.Color.blue()
                )
                
                if thumbnailURL:
                    embed.set_thumbnail(url=thumbnailURL)

                embed.add_field(name="Title", value=row[1], inline=True)
                embed.add_field(name="Level", value=difficultyWithLevel, inline=True)
                embed.add_field(name="Genre", value=row[3], inline=True)
                embed.add_field(name="Artist", value=row[5], inline=True)

                await interaction.response.send_message(embed=embed, ephemeral=False)
            else:
                await interaction.response.send_message("No song found with that title and difficulty.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while fetching the song info.", ephemeral=True)
            print(f"Database error: {e}")
        finally:
            if self.cursor is not None:
                self.cursor.fetchall()

async def setup(bot):
    await bot.add_cog(SongInfo(bot))
