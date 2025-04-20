from aiogram.fsm.state import State, StatesGroup


class Register(StatesGroup):
    CONTACT = State()
    ADDRESS = State()  # Новое состояние для ввода адреса
    ORDER_STATUS = State()  # Состояние для обновления статуса заказа
