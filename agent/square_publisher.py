import asyncio
import logging
import pandas as pd
from datetime import datetime, timezone, timedelta
import aiohttp

# Import required project modules
from core.binance_api import fetch_klines
from core.indicators import calculate_binance_indicators
from agent.analyzer import ask_ai_analysis
from agent.skills import post_to_binance_square

# --- GLOBAL TOGGLE FOR TELEGRAM ---
AUTO_SQUARE_ENABLED = True

async def auto_square_poster(session: aiohttp.ClientSession):
    """Background task for twice-a-day Binance Square reports (09:09 and 21:09 UTC)"""
    global AUTO_SQUARE_ENABLED
    logging.info("🕒 Square Publisher task started. Scheduled for 09:09 and 21:09 UTC.")
    coins_to_post = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    while True:
        now = datetime.now(timezone.utc)

        # Calculate next target time (either today 09:09, today 21:09, or tomorrow 09:09)
        target_morning = now.replace(hour=9, minute=9, second=0, microsecond=0)
        target_evening = now.replace(hour=21, minute=9, second=0, microsecond=0)

        if now < target_morning:
            target_time = target_morning
        elif now < target_evening:
            target_time = target_evening
        else:
            # Skip to tomorrow morning
            target_time = target_morning + timedelta(days=1)

        sleep_sec = (target_time - now).total_seconds()

        # Failsafe in case of microsecond rounding issues
        if sleep_sec <= 0:
            sleep_sec = 60

        logging.info(f"⏳ Publisher sleeping for {sleep_sec:.0f}s until {target_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        await asyncio.sleep(sleep_sec)

        # --- CHECK IF USER DISABLED AUTO-POSTING VIA TELEGRAM ---
        if not AUTO_SQUARE_ENABLED:
            logging.info("⏸ Auto-post is DISABLED. Woke up, but skipping publication.")
            await asyncio.sleep(120)
            continue

        # Woke up at target time (09:09 or 21:09) and posting IS enabled
        for symbol in coins_to_post:
            try:
                logging.info(f"Generating Square post for {symbol}...")

                # Request 1H timeframe for a good intraday snapshot
                raw_df = await fetch_klines(session, symbol, "1h", 100)
                if not raw_df: continue

                df = pd.DataFrame(raw_df)
                last_row, _ = calculate_binance_indicators(df, "1H")

                # AI will automatically include $COIN and #AIBinance #BinanceSquare
                ai_text = await ask_ai_analysis(symbol, "1H", last_row, lang="en")

                # Adding a small introductory line
                square_text = f"🤖 Bi-Daily Market Pulse:\n\n{ai_text}"

                # Publish
                res = await post_to_binance_square(square_text)
                logging.info(f"✅ Square Auto-Post result for {symbol}: {res}")

                await asyncio.sleep(15) # API Spam protection between posts
            except Exception as e:
                logging.error(f"❌ Auto post error for {symbol}: {e}")

        # Sleep for 2 minutes to ensure we don't double-trigger in the same minute
        await asyncio.sleep(120)
