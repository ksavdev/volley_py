async def notify_user(bot, user_id: int, text: str):
    await bot.send_message(user_id, text)
