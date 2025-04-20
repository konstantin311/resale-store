from aiogram.fsm.state import State, StatesGroup


class Add(StatesGroup):
    MAIN = State()
    NAME = State()
    CATEGORY = State()
    PRICE = State()
    CURRENCY = State()
    PHOTO = State()
    CONTACT = State()
    DESCRIPTION = State()


class Edit(StatesGroup):
    CHOICE = State()
