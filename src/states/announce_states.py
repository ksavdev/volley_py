from aiogram.fsm.state import StatesGroup, State

class AnnounceStates(StatesGroup):
    waiting_for_hall             = State()  # выбор зала
    waiting_for_date             = State()  # ввод даты
    waiting_for_time             = State()  # ввод времени
    waiting_for_players_cnt      = State()  # ввод количества игроков
    waiting_for_roles            = State()  # ввод ролей
    waiting_for_balls_needed     = State()  # ответ Да/Нет на «мячи нужны?»
    waiting_for_restrictions     = State()  # ввод ограничений
    waiting_for_is_paid          = State()  # ответ Да/Нет на «платная?»
