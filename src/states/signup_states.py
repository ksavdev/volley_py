from aiogram.fsm.state import State, StatesGroup


class SignupStates(StatesGroup):
    """FSM игрока при подаче заявки"""
    waiting_for_role = State()           # ввод роли игрока


class DeclineStates(StatesGroup):
    """FSM автора, когда он отклоняет и пишет причину"""
    waiting_reason = State()
