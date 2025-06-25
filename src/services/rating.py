from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


async def apply_penalty(session: AsyncSession, user_id: int, amount: int = 1) -> bool:
    """
    Понизить рейтинг пользователя на `amount` (целых баллов).
    Использует поле `penalties`, не трогает rating_sum/votes.
    """
    user = await session.get(User, user_id, with_for_update=True)
    if not user:
        return False

    user.penalties += amount
    await session.commit()
    return True
