from aiogram.fsm.state import State, StatesGroup

class CategoryStates(StatesGroup):
    adding_name = State()
    editing_name = State()
    editing_category_id = State()
    editing_user_id = State() 