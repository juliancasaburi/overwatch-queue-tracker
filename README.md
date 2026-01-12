# Overwatch 2 South America Queue Tracker

A Discord bot for South American Overwatch 2 players to coordinate queue times. Players register their BattleTags, signal when they queue/unqueue, and check who else is actively looking for matches. The bot displays player counts grouped by skill tier.

## Features

- **Player Registration**: Link your BattleTag to your Discord account
- **Queue Management**: Signal when you're looking for a match
- **Rank Tracking**: Automatically fetches your highest role rank from your public profile
- **Queue Status**: See who's currently queuing, grouped by rank tier
- **Auto Updates**: Queue status posted every 10 minutes with refreshed ranks
- **24-Hour Timeout**: Players automatically removed from queue after 24 hours
- **Admin Controls**: Clear queue, remove players, force refresh ranks

## Commands

### User Commands

| Command | Description |
|---------|-------------|
| `/register <battletag>` | Register your BattleTag (e.g., `/register Player#1234`) |
| `/queue` | Join the queue (24h timeout, re-queue to refresh) |
| `/unqueue` | Leave the queue |
| `/status` | Show current queue status grouped by rank |
| `/help` | Show help information |

### Admin Commands (Discord Administrator only)

| Command | Description |
|---------|-------------|
| `/admin clear` | Clear the entire queue |
| `/admin remove <user>` | Remove a specific user from the queue |
| `/admin refresh` | Force refresh all queued player ranks |

## Setup

### Prerequisites

- Python 3.10 or higher
- A Discord bot token ([Create one here](https://discord.com/developers/applications))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd overwatch-queue-tracker
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the bot**
   ```bash
   # Copy the example config
   cp .env.example .env
   
   # Edit .env with your values
   ```

   Required environment variables:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `QUEUE_CHANNEL_ID`: The channel ID where the bot posts automatic updates

5. **Run the bot**
   ```bash
   python bot.py
   ```

### Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Enable these Privileged Gateway Intents:
   - Message Content Intent (for DM handling)
5. Copy the bot token and add it to your `.env` file
6. Go to OAuth2 > URL Generator:
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
7. Use the generated URL to invite the bot to your server

### Getting the Channel ID

1. Enable Developer Mode in Discord (Settings > App Settings > Advanced > Developer Mode)
2. Right-click the channel where you want automatic updates
3. Click "Copy Channel ID"
4. Add it to your `.env` file as `QUEUE_CHANNEL_ID`

## Project Structure

```
overwatch-queue-tracker/
├── bot.py                 # Main entry point
├── cogs/
│   ├── admin.py           # Admin commands
│   ├── help.py            # Help command
│   ├── queue.py           # Queue commands
│   └── registration.py    # Registration command
├── services/
│   ├── database.py        # SQLite operations
│   └── overfast_api.py    # OverFast API client
├── utils/
│   ├── embeds.py          # Discord embed builders
│   └── ranks.py           # Rank utilities
├── assets/
│   └── queue_icon.png     # Bot avatar (people in line)
├── scripts/
│   └── generate_avatar.py # Script used to create the avatar
├── data/
│   └── bot.db             # SQLite database (created at runtime)
├── .env.example           # Example configuration
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## How It Works

### Rank Detection

The bot uses the [OverFast API](https://overfast-api.tekrop.fr/) to fetch player ranks. It determines a player's rank by:

1. Fetching the player's competitive data for PC
2. Checking all three roles (Tank, Damage, Support)
3. Returning the **highest** ranked role's division

Players are categorized as:
- **Champion** through **Bronze**: Based on their highest role rank
- **Unranked**: Has PC data but no ranked roles this season
- **Unknown**: Private profile, invalid BattleTag, or API error

### Queue Status Updates

Every 10 minutes, the bot:
1. Removes players who have been in queue for more than 24 hours
2. Fetches updated ranks for all queued players from the API
3. Posts the queue status to the configured channel

### Database

Player data and queue state are stored in a local SQLite database at `data/bot.db`. This is created automatically on first run.

## Rank Tiers

| Tier | Emoji | Description |
|------|-------|-------------|
| Champion | 👑 | Top 500 / Ultimate |
| Grandmaster | 🏆 | Grandmaster |
| Master | 💜 | Master |
| Diamond | 💎 | Diamond |
| Platinum | 🥈 | Platinum |
| Gold | 🥇 | Gold |
| Silver | ⚪ | Silver |
| Bronze | 🥉 | Bronze |
| Unranked | 📊 | No ranked roles this season |
| Unknown | ❓ | Private/Invalid/Error |

## API Rate Limits

The OverFast API has these limits:
- 30 requests per second per IP
- 10 concurrent connections per IP

The bot respects these limits by adding delays between requests during batch rank refreshes.

## Troubleshooting

### Bot doesn't respond to commands
- Ensure the bot has the `applications.commands` scope
- Try re-syncing commands by restarting the bot
- Check that the bot has permission to send messages in the channel

### "Unknown" rank for all players
- Verify the BattleTag is correct (case-sensitive)
- Check if the player's profile is public on Blizzard's site
- The OverFast API may be temporarily unavailable

### Automatic updates not posting
- Verify `QUEUE_CHANNEL_ID` is set correctly in `.env`
- Ensure the bot has permission to send messages in that channel
- Check the bot logs for errors

## License

MIT License - see LICENSE file for details.

## Credits

- [OverFast API](https://overfast-api.tekrop.fr/) by TeKrop for Overwatch 2 player data
- [discord.py](https://discordpy.readthedocs.io/) for the Discord bot framework
