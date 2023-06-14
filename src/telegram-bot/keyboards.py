from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# общее
continue_button = InlineKeyboardButton(text="Продолжить", callback_data="continue")
# БЭКНУТЬ БЭК
back_button = InlineKeyboardButton(text="На прошлый шаг", callback_data="back")
back_board = InlineKeyboardMarkup()
back_board.add(back_button)

# main menu
menu_board = InlineKeyboardMarkup()
forget_button = InlineKeyboardButton(text="Удалить анкету", callback_data="forget")
check_button = InlineKeyboardButton(text="Посмотреть вакансии", callback_data="check")
menu_board.add(forget_button, check_button)

# delete notification
delete_button = InlineKeyboardButton(text="Скрыть это сообщение", callback_data="delete")
delete_board = InlineKeyboardMarkup()
delete_board.add(delete_button)

# register
register_board = InlineKeyboardMarkup()
register_button = InlineKeyboardButton(text="Заполнить анкету", callback_data="register")
register_board.add(register_button)

# remote?
remote_board = InlineKeyboardMarkup()
remote_button = InlineKeyboardButton(text="Только удалённо", callback_data="remote_only")
remote_board.add(remote_button)

# yes\no
yesno_board = InlineKeyboardMarkup()
yes_button = InlineKeyboardButton(text="Да", callback_data="yes")
no_button = InlineKeyboardButton(text="Нет", callback_data="no")
yesno_board.row(yes_button, no_button)
yesno_board.row(back_button)

# skills
dev_skills_available = ["FrontEnd", "Node.js", "GameDev", "Embedded", "1C", "DB", "Fullstack", "C#", "C++", "Golang",
                        "Desktop",
                        "Mobile", "Java", "PHP", "Python", "Ruby", "Scala"]
other_skills_available = ["Devops", "QA", "CTO", "DA/DBA", "Architect", "Data engineer", "Data science",
                          "Data Analyst", "Техподдержка", "Технический писатель",
                          "Cистемный администратор",
                          "Cистемная аналитика", "Бизнес аналитика",
                          "Продуктовая аналитика", "Информационная безопасность"]

grades_available = ["Junior", "Middle", "Senior", "Lead"]
skill_next_button = InlineKeyboardButton(text="▶", callback_data="switch_board")
skill_back_button = InlineKeyboardButton(text="◀", callback_data="switch_board")


# динамическая клавиатура
async def grade_board(chosen: set[str]) -> InlineKeyboardMarkup:
    new_board = InlineKeyboardMarkup()
    for variant in grades_available:
        if variant in chosen:
            new_board.add(
                InlineKeyboardButton(text=f"{variant} ☑️", callback_data=variant))
        else:
            new_board.add(InlineKeyboardButton(text=variant, callback_data=variant))
    new_board.row(back_button, continue_button)
    return new_board


async def skills_board(chosen: set[str]) -> InlineKeyboardMarkup:
    if "switch_board" not in chosen:
        new_board = InlineKeyboardMarkup(row_width=3)
        for variant in dev_skills_available:
            if variant in chosen:
                new_board.insert(
                    InlineKeyboardButton(text=f"{variant} ☑️", callback_data=variant))
            else:
                new_board.insert(InlineKeyboardButton(text=variant, callback_data=variant))
        new_board.row(back_button, skill_next_button)
    else:
        new_board = InlineKeyboardMarkup(row_width=2)
        for variant in other_skills_available:
            if variant in chosen:
                new_board.insert(
                    InlineKeyboardButton(text=f"{variant} ☑️", callback_data=variant))
            else:
                new_board.insert(InlineKeyboardButton(text=variant, callback_data=variant))
        new_board.row(skill_back_button, continue_button)
    return new_board
