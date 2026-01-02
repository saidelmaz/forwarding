# Telegram CA Forwarder

A Telegram userbot that monitors messages from a specific bot/chat, extracts Solana contract addresses (CAs), and forwards them to a destination chat.

## Features

- Monitors messages from a specified source chat (bot or channel)
- Extracts Solana contract addresses using regex pattern matching
- Sends only the raw CA to a destination chat (not a forward)
- Handles reconnects gracefully with exponential backoff
- Basic logging for monitoring activity

## Requirements

- Python 3.10+
- Telegram account
- API credentials from [my.telegram.org](https://my.telegram.org/apps)

## Installation

1. Clone or download this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` with your credentials:
   - `API_ID`: Your Telegram API ID (from my.telegram.org)
   - `API_HASH`: Your Telegram API hash (from my.telegram.org)
   - `SOURCE_CHAT`: The bot/chat to monitor (username or ID)
   - `DESTINATION_CHAT`: Where to send extracted CAs (username, ID, or `me` for Saved Messages)

## Getting API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click on "API development tools"
4. Create a new application (if you haven't already)
5. Copy the `api_id` and `api_hash`

## Usage

Run the script:

```bash
python main.py
```

On first run, you'll be prompted to:
1. Enter your phone number
2. Enter the verification code sent to your Telegram
3. Enter your 2FA password (if enabled)

A session file (`userbot_session.session`) will be created to remember your login.

## Message Format

The bot is designed to extract Solana addresses from messages like:

```
remove the pedophile (pf) - $pedo - AGE: 0d 0h 21m
    Token Rating: ⭐⭐⭐⭐
    6XYKQxMtYJT34RhUrCtRFd5LKX4YUqHHatdaLC2Jpump

    Market Cap: $27.23K
    ...
```

The CA (`6XYKQxMtYJT34RhUrCtRFd5LKX4YUqHHatdaLC2Jpump`) appears on its own line and will be extracted and sent to your destination chat.

## Solana Address Detection

The script uses the following criteria to detect Solana addresses:
- **Base58 characters only**: 1-9, A-H, J-N, P-Z, a-k, m-z (excludes 0, O, I, l)
- **Length**: 32-44 characters
- **Format**: Must appear on its own line (with optional whitespace)

## Configuration Examples

### Monitor a bot and send to Saved Messages
```env
SOURCE_CHAT=@SomeSignalBot
DESTINATION_CHAT=me
```

### Monitor a channel and send to a group
```env
SOURCE_CHAT=-1001234567890
DESTINATION_CHAT=-1009876543210
```

### Monitor a bot and send to a channel you admin
```env
SOURCE_CHAT=SignalBot
DESTINATION_CHAT=@MyPrivateChannel
```

## Troubleshooting

### "Cannot access source/destination chat"
- Make sure you have joined or have access to both chats
- Verify the username or ID is correct
- For private channels, use the numeric ID (starts with -100)

### "Session expired"
- Delete `userbot_session.session` and run the script again to re-authenticate

### "Two-factor authentication is enabled"
- Run the script interactively (not in background) to enter your 2FA password

### Rate limiting
- The script handles FloodWaitError automatically by waiting the required time
- If you're getting rate limited frequently, the source chat may be too active

## Security Notes

- Keep your `.env` file private - never commit it to version control
- The session file (`userbot_session.session`) contains your login credentials - keep it secure
- This is a userbot (runs as your account), not a bot - use responsibly

## License

MIT
