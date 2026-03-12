import asyncio
import os
import discord
from quart import Quart, request, jsonify
from discord.ext import commands

with open("shh.txt") as f:
    bot_token = f.readline()
    api_key = f.readline()

# --- CONFIGURATION ---
BOT_TOKEN = bot_token
CHANNEL_ID = 1332831449623302248  # Replace with your Discord Channel ID
API_KEY = api_key
UPLOAD_FOLDER = "captures"

# Ensure the capture directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- INITIALIZATION ---
app = Quart(__name__)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- DISCORD INTERACTIVE COMPONENTS ---
class DoorControlView(discord.ui.View):
    """
    This class defines the buttons that appear under the photo in Discord.
    'timeout=None' ensures the buttons remain active even after a bot restart.
    """
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Lock Door", style=discord.ButtonStyle.red, custom_id="lock_door_btn")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Here you would trigger a signal back to the ESP32
        await interaction.response.send_message("Signal sent: Door Locked.", ephemeral=True)

    @discord.ui.button(label="Unlock Door", style=discord.ButtonStyle.green, custom_id="unlock_door_btn")
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Signal sent: Door Unlocked.", ephemeral=True)

# --- API ROUTES (QUART) ---
@app.route('/doorbell', methods=['POST'])
async def doorbell_event():
    # 1. Security Verification
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Extract RAW data directly from request.data
    raw_data = await request.get_data()
    
    if not raw_data:
        return jsonify({"error": "No image data found"}), 400

    # 3. Save directly
    file_path = os.path.join(UPLOAD_FOLDER, f"visitor_{int(asyncio.get_event_loop().time())}.jpg")
    with open(file_path, "wb") as f:
        f.write(raw_data)
    
    asyncio.create_task(send_discord_notification(file_path))
    return jsonify({"status": "success"}), 200

# --- DISCORD BOT LOGIC ---
async def send_discord_notification(file_path):
    """
    Reads the file from disk and uploads it to the Discord channel.
    """
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find channel {CHANNEL_ID}")
        return

    try:
        file = discord.File(file_path, filename="visitor.jpg")
        view = DoorControlView()
        
        embed = discord.Embed(
            title="🔔 Doorbell Alert", 
            description="Someone is at the front door.",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://visitor.jpg")
        
        await channel.send(file=file, embed=embed, view=view)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

# --- LIFECYCLE MANAGEMENT ---
@app.before_serving
async def startup():
    """Starts the Discord bot as a background task before the web server opens."""
    asyncio.create_task(bot.start(BOT_TOKEN))

@app.after_serving
async def shutdown():
    """Ensures the bot disconnects gracefully when the server stops."""
    await bot.close()

if __name__ == "__main__":
    # Runs the unified event loop on port 5000
    app.run(host='0.0.0.0', port=5000)