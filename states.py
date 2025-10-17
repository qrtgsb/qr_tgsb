from aiogram.dispatcher.filters.state import State, StatesGroup

class LocationStates(StatesGroup):
    waiting_for_employee_search = State()
    waiting_for_employee_selection = State()
    waiting_for_location = State()
