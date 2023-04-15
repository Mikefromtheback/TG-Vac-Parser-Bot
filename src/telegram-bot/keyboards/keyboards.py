from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# main menu
menu_board = InlineKeyboardMarkup(resize_keyboard=True)
forget_button = InlineKeyboardButton(text="Удалить анкету", callback_data="forget")
check_button = InlineKeyboardButton(text="Посмотреть вакансии", callback_data="check")
menu_board.add(forget_button, check_button)

# delete notification
delete_button = InlineKeyboardButton(text="Скрыть это сообщение", callback_data="delete")
delete_board = InlineKeyboardMarkup(resize_keyboard=True)
delete_board.add(delete_button)

# register
register_board = InlineKeyboardMarkup(resize_keyboard=True)
register_button = InlineKeyboardButton(text="Заполнить анкету", callback_data="register")
register_board.add(register_button)

# remote?
remote_board = ReplyKeyboardMarkup(resize_keyboard=True)
remote_button = KeyboardButton(text="Хочу только удалённо")
remote_board.add(remote_button)

# grade
grade_board = ReplyKeyboardMarkup(resize_keyboard=True)
gradej_button = KeyboardButton(text="Junior")
gradem_button = KeyboardButton(text="Middle")
grades_button = KeyboardButton(text="Senior")
gradel_button = KeyboardButton(text="Lead")
grade_board.add(gradej_button, gradem_button, grades_button, gradel_button)

# yes\no
yesno_board = ReplyKeyboardMarkup(resize_keyboard=True)
yes_button = KeyboardButton(text="Да")
no_button = KeyboardButton(text="Нет")
yesno_board.add(yes_button, no_button)

# skills
skills_board = InlineKeyboardMarkup(resize_keyboard=True, row_width=3)
java_button = InlineKeyboardButton(text="Java", callback_data="Java")
javascript_button = InlineKeyboardButton(text="JavaScript", callback_data="JavaScript")
sql_button = InlineKeyboardButton(text="SQL", callback_data="SQL")
cpp_button = InlineKeyboardButton(text="C++", callback_data="C++")
csharp_button = InlineKeyboardButton(text="C#", callback_data="C#")
c_button = InlineKeyboardButton(text="C", callback_data="C")
net_button = InlineKeyboardButton(text=".NET", callback_data=".NET")
python_button = InlineKeyboardButton(text="Python", callback_data="Python")
rust_button = InlineKeyboardButton(text="Rust", callback_data="Rust")
golang_button = InlineKeyboardButton(text="Golang", callback_data="Golang")
swift_button = InlineKeyboardButton(text="Swift", callback_data="Swift")
continue_button = InlineKeyboardButton(text="Продолжить", callback_data="askforsalary")
skills_available = [java_button, javascript_button, sql_button, cpp_button, csharp_button, c_button, net_button,
                    python_button, rust_button, golang_button, swift_button]
for skill in skills_available:
    skills_board.add(skill)
skills_board.add(continue_button)
