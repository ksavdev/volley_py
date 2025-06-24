# src/states/admin_states.py

from aiogram.fsm.state import StatesGroup, State

class AdminStates(StatesGroup):
    waiting_for_action = State()
    waiting_for_broadcast_text = State()
    # Добавь другие состояния по необходимости

class AdminDMStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_text = State()
