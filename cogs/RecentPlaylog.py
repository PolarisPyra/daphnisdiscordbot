import os
import discord
from discord import app_commands
from discord.ext import commands
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv(".env")
URL: str = os.getenv("URL")

class RecentPlayLog(commands.Cog):
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

    def get_grade(self, score: int) -> str:
        if score >= 1009000:
            return "SSS+"
        elif score >= 1007500:
            return "SSS"
        elif score >= 1005000:
            return "SS+"
        elif score >= 1000000:
            return "SS"
        elif score >= 990000:
            return "S+"
        elif score >= 975000:
            return "S"
        elif score >= 950000:
            return "AAA"
        elif score >= 925000:
            return "AA"
        elif score >= 900000:
            return "A"
        elif score >= 800000:
            return "BBB"
        elif score >= 700000:
            return "BB"
        elif score >= 600000:
            return "B"
        elif score >= 500000:
            return "C"
        else:
            return "D"

    @commands.Cog.listener()
    async def on_ready(self):
        print("RecentPlayLog Commands ready")

    @app_commands.command(name="recentplays", description="Fetches recent plays using username with an optional title filter.")
    @app_commands.describe(username="Enter the username to fetch recent plays.", version="Enter the version to filter.", title="(Optional) Enter the title to filter by song title.")
    async def recentPlays(self, interaction: discord.Interaction, username: str, version: str, title: str = None):
        if self.cursor is None:
            await interaction.response.send_message("Database connection failed.", ephemeral=True)
            return
    
        try:
            self.cursor.execute("SELECT id FROM aime_user WHERE username = %s", (username,))
            user_row = self.cursor.fetchone()
        
            if user_row is None:
                await interaction.response.send_message("User not found.", ephemeral=True)
                return
        
            user_id = user_row[0] 

            # starts at 0 
            query = """
                WITH RankedScores AS (
                    SELECT 
                        csp.maxCombo, 
                        csp.isFullCombo, 
                        csp.userPlayDate, 
                        csp.playerRating, 
                        csp.isAllJustice, 
                        csp.score,
                        csp.judgeHeaven, 
                        csp.judgeGuilty, 
                        csp.judgeJustice, 
                        csp.judgeAttack,
                        csp.judgeCritical, 
                        csp.isClear, 
                        csp.skillId, 
                        csp.isNewRecord, 
                        csm.chartId,  
                        csm.title, 
                        csm.level, 
                        csm.genre, 
                        csm.jacketPath, 
                        csm.artist,
                        au.username
                    FROM 
                        chuni_score_playlog csp
                        JOIN chuni_profile_data d ON csp.user = d.user
                        JOIN chuni_static_music csm ON csp.musicId = csm.songId AND csp.level = csm.chartId AND csm.version = d.version
                        JOIN aime_card a ON d.user = a.user
                        JOIN aime_user au ON a.user = au.id 
                    WHERE 
                        a.user = %s AND d.version = %s
            """
            params = [user_id, version]

            # Add like if a title is present in the query
            if title:
                query += " AND csm.title LIKE %s"
                params.append(f"%{title}%")

            # starts at 0 
            query += """
                )
                SELECT 
                    maxCombo, 
                    isFullCombo, 
                    userPlayDate, 
                    playerRating, 
                    isAllJustice, 
                    score,
                    judgeHeaven, 
                    judgeGuilty, 
                    judgeJustice, 
                    judgeAttack,
                    judgeCritical, 
                    isClear, 
                    skillId, 
                    isNewRecord, 
                    chartId,  
                    title, 
                    level, 
                    genre, 
                    jacketPath, 
                    artist,
                    username
                FROM 
                    RankedScores
                ORDER BY 
                    userPlayDate DESC
                LIMIT 1
            """
            self.cursor.execute(query, params)
            row = self.cursor.fetchone()
        
            if row is not None:

                title_text = f"[NEW] {row[15]}" if row[13] == 1 else row[15]
                jacketPath = row[18]  
                thumbnailURL = f"https://{URL}/jacketArts/{jacketPath.replace('.dds', '.png')}" if jacketPath else None
                difficultyName = self.DifficultyMap.get(row[14], "Unknown")
                level = row[16] 
                difficultyWithLevel = f"{difficultyName} (Level {level})"
                rank = self.get_grade(row[5])  

                embed = discord.Embed(
                    title=title_text,
                    color=discord.Color.dark_gray()
                )
                if thumbnailURL:
                    embed.set_thumbnail(url=thumbnailURL)

                embed.add_field(name="Artist", value=row[19], inline=True)
                embed.add_field(name="Played by", value=row[20], inline=True) 
                embed.add_field(name="Difficulty", value=difficultyWithLevel, inline=True)
                embed.add_field(name="Score", value=row[5], inline=True)
                embed.add_field(name="Rank", value=rank, inline=True)  
                embed.add_field(name="Max Combo", value=row[0], inline=True)
                embed.add_field(
                    name="Judgement:",
                        value=f"**Justice Critical**: {row[10] + row[6]}\n**Justice**: {row[8]}\n**Attack**: {row[9]}\n**Miss**: {row[7]}",
                    inline=True
                )

                await interaction.response.send_message(embed=embed, ephemeral=False)

            else:
                await interaction.response.send_message("User not found or no recent plays matching the title.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while fetching the play log.", ephemeral=True)
            print(f"Database error: {e}")

    @app_commands.command(name="recent3plays", description="Fetches the top ten recent plays using username.")
    @app_commands.describe(username="Enter the username to fetch the top ten recent plays.", version="Enter the version to filter.")
    async def recent3Plays(self, interaction: discord.Interaction, username: str, version: str):
        if self.cursor is None:
            await interaction.response.send_message("Database connection failed.", ephemeral=True)
            return
        
        try:
            self.cursor.execute("SELECT id FROM aime_user WHERE username = %s", (username,))
            user_row = self.cursor.fetchone()
        
            if user_row is None:
                await interaction.response.send_message("User not found.", ephemeral=True)
                return
            
            user_id = user_row[0]

            self.cursor.execute("""
                WITH RankedScores AS (
                    SELECT 
                        csp.maxCombo, 
                        csp.isFullCombo, 
                        csp.userPlayDate, 
                        csp.playerRating, 
                        csp.isAllJustice, 
                        csp.score,
                        csp.judgeHeaven, 
                        csp.judgeGuilty, 
                        csp.judgeJustice, 
                        csp.judgeAttack,
                        csp.judgeCritical, 
                        csp.isClear, 
                        csp.skillId, 
                        csp.isNewRecord, 
                        csm.chartId,  
                        csm.title, 
                        csm.level, 
                        csm.genre, 
                        csm.jacketPath, 
                        csm.artist
                    FROM 
                        chuni_score_playlog csp
                        JOIN chuni_profile_data d ON csp.user = d.user
                        JOIN chuni_static_music csm ON csp.musicId = csm.songId AND csp.level = csm.chartId AND csm.version = d.version
                        JOIN aime_card a ON d.user = a.user
                    WHERE 
                        a.user = %s AND d.version = %s
                )
                SELECT 
                    maxCombo, 
                    isFullCombo, 
                    userPlayDate, 
                    playerRating, 
                    isAllJustice, 
                    score,
                    judgeHeaven, 
                    judgeGuilty, 
                    judgeJustice, 
                    judgeAttack,
                    judgeCritical, 
                    isClear, 
                    skillId, 
                    isNewRecord, 
                    chartId,  
                    title, 
                    level, 
                    genre, 
                    jacketPath, 
                    artist
                FROM 
                    RankedScores
                ORDER BY 
                    userPlayDate DESC
                LIMIT 3
            """, (user_id, version))

            rows = self.cursor.fetchall()
            if rows:
                embeds = []
                for row in rows:

                    title_text = f"[NEW] {row[15]}" if row[13] == 1 else row[15]
                    jacketPath = row[18]
                    thumbnailURL = f"https://{URL}/jacketArts/{jacketPath.replace('.dds', '.png')}" if jacketPath else None
                    difficultyName = self.DifficultyMap.get(row[14], "Unknown")
                    level = row[16]
                    difficultyWithLevel = f"{difficultyName} (Level {level})"
                    rank = self.get_grade(row[5])

                    embed = discord.Embed(
                        title=title_text,
                        color=discord.Color.dark_gray()
                    )
                    if thumbnailURL:
                        embed.set_thumbnail(url=thumbnailURL)

                    embed.add_field(name="Artist", value=row[19], inline=True)
                    embed.add_field(name="Difficulty", value=difficultyWithLevel, inline=True)
                    embed.add_field(name="Score", value=row[5], inline=True)
                    embed.add_field(name="Rank", value=rank, inline=True)
                    embed.add_field(name="Max Combo", value=row[0], inline=True)
                    embed.add_field(
                        name="Judgement",
                        value=f"**Justice Critical**: {row[10] + row[6]}\n**Justice**: {row[8]}\n**Attack**: {row[9]}\n**Miss**: {row[7]}",                        inline=True
                    )
                    embeds.append(embed)

                await interaction.response.send_message(embeds=embeds, ephemeral=False)
            else:
                await interaction.response.send_message("No recent plays found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("An error occurred while fetching the top ten recent plays.", ephemeral=True)
            print(f"Database error: {e}")


async def setup(bot):
    await bot.add_cog(RecentPlayLog(bot))
