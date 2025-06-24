from aiogram.fsm.state import StatesGroup, State

class RatingStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_comment = State()