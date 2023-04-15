import logging
import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
import config
from bd import db
from aiogram import executor, Bot, types, Dispatcher
from keyboards import *
from datetime import datetime

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.token)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


class RegistrationProcess(StatesGroup):  # FSM
    city = State()
    remote = State()
    grade = State()
    skills = State()
    salary = State()


@dp.message_handler(commands="menu")
async def start(message: types.Message):
    if db.check_user(message.from_user.id):
        await message.answer(text=f"Привет, {message.from_user.full_name}! Что ты хочешь сделать?",
                             reply_markup=menu_board)
    else:
        await message.answer(
            text="Привет! Я помогу тебе найти вакансии в сфере IT. Ответь на несколько вопросов, чтобы начать получать подходящие для тебя вакансии.",
            reply_markup=register_board)


@dp.callback_query_handler(lambda c: c.data == "check")
async def check_vacancies(c: types.CallbackQuery):
    user_data = db.get_user_data(c.from_user.id)
    latest_time = user_data[6]
    parsed_vacancies = db.get_vacancies(db.get_user_data(c.from_user.id))
    if not parsed_vacancies:
        await c.answer()
        await bot.send_message(c.from_user.id, text="К сожалению, новых вакансий пока что нет.",
                               reply_markup=delete_board)
    else:
        await c.answer()
        for vacancy in parsed_vacancies:
            temp_link_board = InlineKeyboardMarkup()
            link_button = InlineKeyboardButton(text="Открыть в браузере", url=vacancy[3])
            temp_link_board.add(link_button)
            temp_link_board.add(delete_button)
            await bot.send_message(c.from_user.id,
                                   text=f"Найдена вакансия!\n\nКомпания:{vacancy[1]}\n\nОписание: {vacancy[2]}",
                                   reply_markup=temp_link_board)
            latest_time = max(latest_time, vacancy[4])
        db.update_user_time(c.from_user.id, latest_time)


@dp.callback_query_handler(lambda c: c.data == "delete")
async def delete_message(c):
    await c.message.delete()


@dp.callback_query_handler(lambda c: c.data == "forget")
async def forget(c: types.CallbackQuery):
    db.delete_user(c.from_user.id)
    await c.answer()
    await bot.send_message(c.from_user.id, "Анкета удалена. Ты можешь создать новую.", reply_markup=register_board)


@dp.callback_query_handler(lambda c: c.data == "register")
async def start_registration(c: types.CallbackQuery):
    await RegistrationProcess.city.set()
    await c.answer()
    await bot.send_message(c.from_user.id,
                           "Вакансии из какого города тебе интересны? Если хочешь работать только удалённо, нажми на соответствующую кнопку.",
                           reply_markup=remote_board)


@dp.message_handler(lambda message: len(message.text) > 20, state=RegistrationProcess.city)
async def process_bad_city(message: types.Message):
    return await message.reply("Напиши название города ещё раз ☹️",
                               reply_markup=remote_board)


@dp.message_handler(lambda message: message.text == "Хочу только удалённо", state=RegistrationProcess.city)
async def get_city(message: types.Message, state: FSMContext):
    await RegistrationProcess.grade.set()
    await state.update_data(city="NULL")
    await state.update_data(remote=True)
    await message.reply("Я запомнил. Теперь выбери, на какой ты претендуешь грейд.",
                        reply_markup=grade_board)


@dp.message_handler(state=RegistrationProcess.city)
async def get_city(message: types.Message, state: FSMContext):
    await RegistrationProcess.next()
    await state.update_data(city=message.text)
    return await message.reply(
        "Я запомнил. Выбери, хочешь ли ты видеть вакансии с удалённой работой, и нажми на кнопку.",
        reply_markup=yesno_board)


@dp.message_handler(state=RegistrationProcess.remote)
async def process_remote(message: types.Message, state: FSMContext):
    if (message.text != "Да" and message.text != "Нет"):
        return await message.reply("Пожалуйста, выбери 'Да' или 'Нет'.")
    if (message.text == "Да"):
        await state.update_data(remote=True)
    else:
        await state.update_data(remote=False)
    await RegistrationProcess.grade.set()
    await message.reply("Хорошо. Теперь выбери, на какой ты претендуешь грейд.",
                        reply_markup=grade_board)


@dp.message_handler(lambda message: message.text not in ["Junior", "Middle", "Senior", "Lead"],
                    state=RegistrationProcess.grade)
async def process_bad_grade(message: types.Message):
    return await message.reply("Пожалуйста, выбери грейд из данных вариантов ☹️")


@dp.message_handler(state=RegistrationProcess.grade)  # skill board
async def process_grade(message: types.Message, state: FSMContext):
    await RegistrationProcess.skills.set()
    await state.update_data(grade=message.text)
    await message.reply("Грейд выбран. Выбери интересующие тебя технологии и нажми продолжить.",
                        reply_markup=aiogram.types.ReplyKeyboardRemove())
    async with state.proxy() as data:
        data['chosen_skills'] = set()
    await bot.send_message(message.from_user.id, text="Можно выбрать столько, сколько хочешь.",
                           reply_markup=skills_board)


@dp.callback_query_handler(lambda c: c.data == "askforsalary", state=RegistrationProcess.skills)
async def process_skills(c: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if not data['chosen_skills']:
            return await c.answer(text="Ты ничего не выбрал!")
        await state.update_data(skills=list(data['chosen_skills']))
    await RegistrationProcess.salary.set()
    await c.answer()
    await bot.send_message(c.from_user.id,
                           text="Хорошо! Последний шаг: если хочешь, укажи числом минимальную зп в долларах, и я не буду присылать вакансии с зп меньше неё и без указанной зарплаты. Если ты напишешь 0, то я буду присылать все вакансии, даже без указанной зп.")


@dp.callback_query_handler(state=RegistrationProcess.skills)
async def collecting_skills(c: types.CallbackQuery, state: FSMContext):
    refreshed_skills_board = InlineKeyboardMarkup(resize_keyboard=True, row_width=3)
    async with state.proxy() as data:
        if c.data in data['chosen_skills']:
            data['chosen_skills'].remove(c.data)
        else:
            data['chosen_skills'].add(c.data)
        for skill in skills_available:
            if skill.callback_data in data['chosen_skills']:
                refreshed_skills_board.add(
                    InlineKeyboardButton(text=skill.text + " 🟢", callback_data=skill.callback_data))
            else:
                refreshed_skills_board.add(skill)
    refreshed_skills_board.add(continue_button)
    await bot.edit_message_reply_markup(chat_id=c.from_user.id, message_id=c.message.message_id,
                                        reply_markup=refreshed_skills_board)


@dp.message_handler(lambda message: len(message.text) > 10 or not message.text.isdigit(),
                    state=RegistrationProcess.salary)
async def process_bad_salary(message: types.Message):
    return await message.reply("Напиши число еще раз ☹️")


@dp.message_handler(state=RegistrationProcess.salary)
async def process_salary(message: types.Message, state: FSMContext):
    await state.update_data(salary=int(message.text))
    async with state.proxy() as data:
        db.add_user(message.from_user.id, data['city'], data['remote'],
                    data['grade'], data['skills'], data['salary'])
    await bot.send_message(message.chat.id, text="Все готово, теперь я буду искать для тебя вакансии!",
                           reply_markup=InlineKeyboardMarkup().add(check_button))
    await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
