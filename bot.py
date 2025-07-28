import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from keep_alive import keep_alive
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import os
token = os.getenv("DISCORD_BOT_TOKEN")


class DiscordBot:
    def __init__(self):
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True

        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.sheet = None

        self.bot.event(self.on_ready)
        self.register_commands()
        self.init_google_sheet()

    def init_google_sheet(self):
        """Initialize connection to Google Sheets"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
            client = gspread.authorize(creds)
            self.sheet = client.open("Daily Expenses Bot").sheet1
            print("✅ Connected to Google Sheet successfully.")
        except Exception as e:
            print(f"❌ Failed to connect to Google Sheet: {e}")
            self.sheet = None

    async def on_ready(self):
        print(f"✅ Logged in as {self.bot.user}")
        try:
            synced = await self.bot.tree.sync()
            print(f"🔧 Synced {len(synced)} slash command(s)")
        except Exception as e:
            print(f"⚠️ Failed to sync commands: {e}")

    def register_commands(self):
        @self.bot.command(name="ping")
        async def ping(ctx):
            await ctx.send("🏓 Pong!")

        @self.bot.command(name="log")
        async def log(ctx, item: str, amount: float, note: str = ""):
            """Logs an expense via !log command"""
            if self.sheet:
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    user = ctx.author.name
                    self.sheet.append_row([timestamp, item, amount, note, user])
                    await ctx.send(f"✅ Logged: `{item}` - RM{amount:.2f} by {user}")
                except Exception as e:
                    await ctx.send(f"❌ Failed to write to sheet: {e}")
            else:
                await ctx.send("❌ Google Sheet is not connected.")

        @self.bot.command(name="test_sheet")
        async def test_sheet(ctx):
            """Test if the bot can write to Google Sheet"""
            if self.sheet:
                try:
                    self.sheet.append_row([
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Test",
                        "0",
                        "test",
                        ctx.author.name
                    ])
                    await ctx.send("✅ Successfully wrote test row to Google Sheet")
                except Exception as e:
                    await ctx.send(f"❌ Failed to write to sheet: {e}")
            else:
                await ctx.send("❌ Google Sheet is not connected.")

        @self.bot.tree.command(name="log", description="Log an expense (item, amount, optional note)")
        @app_commands.describe(item="What did you spend on?", amount="How much (RM)?", note="Extra note (optional)")
        async def slash_log(interaction: discord.Interaction, item: str, amount: float, note: str = ""):
            """Logs an expense via slash command"""
            if self.sheet:
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    user = interaction.user.name
                    self.sheet.append_row([timestamp, item, amount, note, user])
                    await interaction.response.send_message(
                        f"✅ Logged: `{item}` - RM{amount:.2f} by {user}"
                    )
                except Exception as e:
                    await interaction.response.send_message(f"❌ Failed to write to sheet: {e}")
            else:
                await interaction.response.send_message("❌ Google Sheet is not connected.")

# Start Flask keep-alive server
keep_alive()

# Launch the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ DISCORD_BOT_TOKEN not set in environment!")
    else:
        DiscordBot().bot.run(token)
