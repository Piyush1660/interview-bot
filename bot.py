import discord
from discord.ext import commands
import datetime
import sqlite3
import csv
import os

# Bot Configuration
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Replace with your actual bot token
GUILD_ID = 1315015035264700477  # Replace with your server's ID
CHANNEL_ID = 1339464747145363487  # Replace with your interview voice channel ID
ALLOWED_USERS = [971987911757135963, 1070277989910204486]  # Replace with allowed user IDs

# Set up intents
intents = discord.Intents.all()  # Ensure all required intents are enabled
bot = commands.Bot(command_prefix="!", intents=intents)

# File and database setup
DB_FILE = "interviews.db"
LOG_FILE = "interview_logs.txt"
CSV_FILE = "interview_logs.csv"

# Dictionary to track users' join times
join_times = {}

# Ensure the database exists
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS interview_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        joined_at TEXT,
        left_at TEXT,
        duration TEXT
    )
''')
conn.commit()
conn.close()


def save_to_file(username, joined_at, left_at, duration):
    """Append interview log to a text file"""
    try:
        with open(LOG_FILE, "a") as file:
            file.write(f"{username} | Joined: {joined_at} | Left: {left_at} | Duration: {duration}\n")
        print(f"✅ Log written: {username}, {duration}")
    except Exception as e:
        print(f"❌ File Write Error: {e}")


def save_to_database(user_id, username, joined_at, left_at, duration):
    """Insert interview record into SQLite database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO interview_logs (user_id, username, joined_at, left_at, duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, joined_at, left_at, duration))
        conn.commit()
        conn.close()
        print(f"✅ Saved to database: {username}, {joined_at}, {left_at}, {duration}")

        # Automatically update CSV
        update_csv()
    except Exception as e:
        print(f"❌ Database Error: {e}")


def update_csv():
    """Automatically update CSV file"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, joined_at, left_at, duration FROM interview_logs ORDER BY id DESC")
        logs = cursor.fetchall()
        conn.close()

        with open(CSV_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Username", "Joined At", "Left At", "Duration"])
            writer.writerows(logs)
        print("✅ CSV file updated")
    except Exception as e:
        print(f"❌ CSV Update Error: {e}")


@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    guild = bot.get_guild(GUILD_ID)
    if guild:
        print(f"✅ Connected to Guild: {guild.name} ({guild.id})")


@bot.event
async def on_voice_state_update(member, before, after):
    """Track when a user joins or leaves a specific voice channel"""
    if before.channel != after.channel:
        now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # User joined the interview channel
        if after.channel and after.channel.id == CHANNEL_ID:
            join_times[member.id] = now
            print(f"✅ {member.name} joined at {now} UTC")

        # User left the interview channel
        elif before.channel and before.channel.id == CHANNEL_ID and not after.channel:
            if member.id in join_times:
                joined_at = join_times.pop(member.id)
                left_at = now
                duration = (datetime.datetime.strptime(left_at, '%Y-%m-%d %H:%M:%S') -
                            datetime.datetime.strptime(joined_at, '%Y-%m-%d %H:%M:%S'))
                print(f"✅ {member.name} left. Duration: {duration}")

                # Save data to file & database
                save_to_file(member.name, joined_at, left_at, str(duration))
                save_to_database(member.id, member.name, joined_at, left_at, str(duration))


bot.run(TOKEN)
