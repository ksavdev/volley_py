from aiogram.fsm.state import StatesGroup, State

class HallStates(StatesGroup):
    waiting_name    = State()
    waiting_address = State()
