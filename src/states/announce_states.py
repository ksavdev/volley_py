from aiogram.fsm.state import StatesGroup, State

class AdStates(StatesGroup):
    waiting_for_hall             = State()  # выбор зала
    waiting_for_date             = State()  # ввод даты
    waiting_for_time             = State()  # ввод времени
    waiting_for_players_cnt      = State()  # ввод количества игроков
    waiting_for_roles            = State()  # ввод ролей
    waiting_for_balls_needed     = State()  # ответ Да/Нет на «мячи нужны?»
    waiting_for_restrictions     = State()  # ввод ограничений
    waiting_for_is_paid          = State()  # ответ Да/Нет на «платная?»
    waiting_for_price            = State()  # ← добавить для цены

    # Для редактирования:
    choosing_field      = State()
    editing_date        = State()
    editing_time        = State()
    editing_players     = State()
    editing_roles       = State()
    editing_balls       = State()
    editing_restrict    = State()
    editing_paid        = State()  # ← добавить для редактирования платности
    editing_price       = State()  # ← добавить для редактирования цены
