#!/usr/bin/env python3
"""
Telegram Userbot - Forward Solana Contract Addresses from Bot Messages

Monitors messages from a specific Telegram bot and extracts Solana contract
addresses (CAs), then sends only the CA to a destination chat.
"""

import asyncio
import logging
import os
import re
import sys

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import (
    AuthKeyUnregisteredError,
    FloodWaitError,
    SessionPasswordNeededError,
)

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SOURCE_CHAT = os.getenv("SOURCE_CHAT")
DESTINATION_CHAT = os.getenv("DESTINATION_CHAT")

# Validate required environment variables
REQUIRED_VARS = ["API_ID", "API_HASH", "SOURCE_CHAT", "DESTINATION_CHAT"]
missing_vars = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please configure your .env file. See .env.example for reference.")
    sys.exit(1)

# Convert API_ID to integer
try:
    API_ID = int(API_ID)
except ValueError:
    print("Error: API_ID must be a valid integer")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Solana address regex pattern
# Base58 characters: 1-9, A-H, J-N, P-Z, a-k, m-z (excludes 0, O, I, l)
# Length: 32-44 characters
SOLANA_ADDRESS_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", re.MULTILINE)


def extract_solana_addresses(text: str) -> list[str]:
    """
    Extract Solana contract addresses from message text.

    Looks for addresses that appear on their own line, which is the typical
    format in bot messages after the "Token Rating" line.

    Args:
        text: The message text to search

    Returns:
        List of extracted Solana addresses
    """
    addresses = []

    # Split by lines and check each line
    for line in text.split("\n"):
        line = line.strip()
        # Check if the entire line is a valid Solana address
        if SOLANA_ADDRESS_PATTERN.match(line):
            addresses.append(line)

    return addresses


async def resolve_chat_id(client: TelegramClient, chat: str) -> int | str:
    """
    Resolve a chat identifier to a usable format.

    Handles numeric IDs, usernames, and other formats.

    Args:
        client: The Telegram client
        chat: The chat identifier (username, ID, etc.)

    Returns:
        Resolved chat ID or username
    """
    # Try to convert to integer if it looks like a numeric ID
    try:
        return int(chat)
    except ValueError:
        pass

    # Handle usernames (with or without @)
    if not chat.startswith("@") and not chat.startswith("-"):
        # Assume it's a username without @
        return chat

    return chat


async def main():
    """Main entry point for the userbot."""
    logger.info("Starting Telegram CA Forwarder...")

    # Create the client
    client = TelegramClient("userbot_session", API_ID, API_HASH)

    # Resolve chat identifiers
    source_chat = await resolve_chat_id(client, SOURCE_CHAT)
    destination_chat = await resolve_chat_id(client, DESTINATION_CHAT)

    @client.on(events.NewMessage(chats=source_chat, incoming=True, outgoing=True))
    async def handler(event):
        """Handle new messages from the source chat."""
        try:
            message_text = event.message.text or event.message.message or ""

            # Debug: log every message received
            logger.info(f"Message received from chat {event.chat_id}")
            logger.debug(f"Message content preview: {message_text[:100] if message_text else '(empty)'}...")

            if not message_text:
                return

            # Extract Solana addresses
            addresses = extract_solana_addresses(message_text)

            if not addresses:
                logger.info("No Solana addresses found in message")
                return

            logger.info(f"Found {len(addresses)} Solana address(es)")

            # Send each address to the destination chat
            for address in addresses:
                try:
                    await client.send_message(destination_chat, address)
                    logger.info(f"Forwarded CA: {address[:8]}...{address[-4:]}")
                except FloodWaitError as e:
                    logger.warning(f"Rate limited, waiting {e.seconds} seconds...")
                    await asyncio.sleep(e.seconds)
                    await client.send_message(destination_chat, address)
                    logger.info(f"Forwarded CA after wait: {address[:8]}...{address[-4:]}")
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    # Connect and run
    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            logger.info("Connecting to Telegram...")
            await client.start()

            # Get info about the connected account
            me = await client.get_me()
            logger.info(f"Logged in as: {me.first_name} (@{me.username or 'no username'})")

            # Verify source and destination chats are accessible
            try:
                source_entity = await client.get_entity(source_chat)
                logger.info(f"Monitoring source chat: {getattr(source_entity, 'title', None) or getattr(source_entity, 'username', source_chat)}")
            except Exception as e:
                logger.error(f"Cannot access source chat '{SOURCE_CHAT}': {e}")
                logger.error("Make sure you have access to this chat and the username/ID is correct")
                return

            try:
                dest_entity = await client.get_entity(destination_chat)
                logger.info(f"Forwarding to destination: {getattr(dest_entity, 'title', None) or getattr(dest_entity, 'username', destination_chat)}")
            except Exception as e:
                logger.error(f"Cannot access destination chat '{DESTINATION_CHAT}': {e}")
                logger.error("Make sure you have access to this chat and the username/ID is correct")
                return

            logger.info("Bot is now running. Press Ctrl+C to stop.")
            logger.info(f"Listening for messages from: {SOURCE_CHAT}")
            logger.info(f"Forwarding CAs to: {DESTINATION_CHAT}")

            # Run until disconnected
            await client.run_until_disconnected()

        except AuthKeyUnregisteredError:
            logger.error("Session expired. Please delete 'userbot_session.session' and re-authenticate.")
            break
        except SessionPasswordNeededError:
            logger.error("Two-factor authentication is enabled. Please run the script interactively to enter your password.")
            break
        except ConnectionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection error: {e}. Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to connect after {max_retries} attempts")
                raise
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise

    await client.disconnect()
    logger.info("Disconnected from Telegram")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
