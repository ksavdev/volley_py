from aiogram.fsm.state import StatesGroup, State

class HallRequestStates(StatesGroup):
    waiting_for_hall_name = State()
    waiting_for_hall_address = State()
