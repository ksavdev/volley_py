from aiogram.fsm.state import State, StatesGroup


class EditStates(StatesGroup):
    choosing_field      = State()
    editing_date        = State()
    editing_time        = State()
    editing_players     = State()
    editing_roles       = State()
    editing_balls       = State()
    editing_restrict    = State()
    editing_is_paid     = State()