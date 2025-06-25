from functools import wraps
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

def with_cancel(back_state=None, back_text="Назад", cancel_text="Отмена", back_reply=None, cancel_reply=None):
    """
    Декоратор для FSM-хендлеров, чтобы обрабатывать "❌ Отмена" и "⬅️ Назад".
    back_state: состояние для возврата по "⬅️ Назад"
    back_text: текст для кнопки "Назад"
    cancel_text: текст для кнопки "Отмена"
    back_reply: функция (msg, state) для возврата
    cancel_reply: функция (msg, state) для отмены
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(msg: Message, state: FSMContext, *args, **kwargs):
            if msg.text == f"❌ {cancel_text}":
                if cancel_reply:
                    await cancel_reply(msg, state)
                else:
                    await msg.answer("Действие отменено.", reply_markup=None)
                    await state.clear()
                return
            if msg.text == f"⬅️ {back_text}":
                if back_reply:
                    await back_reply(msg, state)
                elif back_state:
                    await state.set_state(back_state)
                    await msg.answer("Назад.", reply_markup=None)
                else:
                    await msg.answer("Назад.", reply_markup=None)
                return
            return await func(msg, state, *args, **kwargs)
        return wrapper
    return decorator
