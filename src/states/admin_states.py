# src/states/admin_states.py

from aiogram.fsm.state import StatesGroup, State

class AdminDMStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_text    = State()
