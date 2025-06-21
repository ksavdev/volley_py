from aiogram.fsm.state import State, StatesGroup

class AnnounceStates(StatesGroup):
    waiting_for_hall          = State()
    waiting_for_date          = State()
    waiting_for_time          = State()
    waiting_for_players_cnt   = State()
    waiting_for_roles         = State()
    waiting_for_balls_needed  = State()
    waiting_for_restrictions  = State()
    waiting_for_is_paid       = State()
