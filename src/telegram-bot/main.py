import asyncio
import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import TelegramAPIError
import config
from bd import DbInterface, datetime
from aiogram import executor, Bot, types, Dispatcher
from keyboards import *

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.token)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
db = DbInterface()


class RegistrationProcess(StatesGroup):  # FSM
    city = State()
    allow_remote = State()
    grade = State()
    allow_no_grade = State()
    skills = State()
    min_salary = State()
    allow_no_salary = State()


@dp.callback_query_handler(lambda c: c.data == "delete")
async def delete_message(c):
    await c.message.delete()


@dp.callback_query_handler(lambda c: c.data == "back", state=RegistrationProcess.allow_remote)
async def back_from_process_remote(c: types.CallbackQuery):
    await c.answer()
    await RegistrationProcess.city.set()
    await bot.send_message(c.from_user.id,
                           "Напиши через запятую, вакансии из каких городов тебе интересны. Если хочешь работать "
                           "только удалённо, нажми на соответствующую кнопку.",
                           reply_markup=remote_board)


@dp.callback_query_handler(lambda c: c.data == "back", state=RegistrationProcess.grade)
async def back_from_grade(c: types.CallbackQuery, state: FSMContext):
    await c.answer()
    async with state.proxy() as data:
        if not data.get("city", None):
            await RegistrationProcess.city.set()
            await bot.send_message(c.from_user.id,
                                   "Напиши через запятую, вакансии из каких городов тебе интересны. Если хочешь "
                                   "работать только удалённо, нажми на соответствующую кнопку.",
                                   reply_markup=remote_board)
        else:
            await RegistrationProcess.allow_remote.set()
            await bot.send_message(c.from_user.id,
                                   text="Выбери, хочешь ли ты видеть вакансии с удалённой работой, и нажми на кнопку.",
                                   reply_markup=yesno_board)


@dp.callback_query_handler(lambda c: c.data == "back", state=RegistrationProcess.allow_no_grade)
async def back_from_allow_no_grade(c: types.CallbackQuery, state: FSMContext):
    await c.answer()
    await RegistrationProcess.grade.set()
    grades_chosen = (await state.get_data())["grade"]
    await bot.send_message(c.from_user.id, text="Выбери желаемые грейды.",
                           reply_markup=await grade_board(grades_chosen))


@dp.callback_query_handler(lambda c: c.data == "back", state=RegistrationProcess.skills)
async def back_from_skills(c: types.CallbackQuery):
    await c.answer()
    await RegistrationProcess.allow_no_grade.set()
    await bot.send_message(c.from_user.id,
                           text="Выбери, показывать ли вакансии без указанного грейда - их немного, но они есть.",
                           reply_markup=yesno_board)


@dp.callback_query_handler(lambda c: c.data == "back", state=RegistrationProcess.min_salary)
async def back_from_salary(c: types.CallbackQuery, state: FSMContext):
    await c.answer()
    await RegistrationProcess.skills.set()
    skills_chosen = (await state.get_data())["grade"]
    await bot.send_message(chat_id=c.from_user.id,
                           text="Выбери интересующие тебя специализации. Ты можешь дополнительно написать свои через запятую.",
                           reply_markup=await skills_board(skills_chosen))


@dp.callback_query_handler(lambda c: c.data == "back", state=RegistrationProcess.allow_no_salary)
async def back_from_allow_no_salary(c: types.CallbackQuery):
    await RegistrationProcess.min_salary.set()
    await bot.send_message(chat_id=c.from_user.id,
                           text="Напиши минимальную зарплату в долларах для показа вакансии.")


@dp.message_handler(commands=["menu", "start"], state=None)
async def start(message: types.Message):
    user_status = await db.check_user(message.from_user.id)
    match user_status:
        case 0:
            return await message.answer(text=f"Привет, {message.from_user.full_name}! Что ты хочешь сделать?",
                                        reply_markup=menu_board)
        case 1:
            return await message.answer(
                text="Я помогу тебе найти вакансии в сфере IT. Ответь на несколько вопросов, чтобы начать получать подходящие для тебя вакансии.",
                reply_markup=register_board)
        case -1:
            return


@dp.callback_query_handler(lambda c: c.data == "check", state=None)
async def check_vacancies(c: types.CallbackQuery):
    parsed_vacancies = await db.get_vacancies(c.from_user.id)
    await c.answer()
    if not parsed_vacancies:
        await bot.send_message(c.from_user.id, text="К сожалению, новых вакансий пока что нет.",
                               reply_markup=delete_board)
    else:
        latest_time = datetime.datetime(2007, 1, 1, tzinfo=datetime.timezone.utc)
        for vacancy in parsed_vacancies:
            temp_link_board = InlineKeyboardMarkup()
            link_button = InlineKeyboardButton(text="Открыть в браузере", url=vacancy[2])
            temp_link_board.add(link_button)
            temp_link_board.add(delete_button)
            await bot.send_message(c.from_user.id,
                                   text=f"Найдена вакансия!\n\nКомпания:{vacancy[0]}\n\nОписание: {vacancy[1]}",
                                   reply_markup=temp_link_board)
            latest_time = max(latest_time, vacancy[3])
        await db.update_user_time(c.from_user.id, latest_time)


@dp.callback_query_handler(lambda c: c.data == "forget", state=None)
async def forget(c: types.CallbackQuery):
    if await db.delete_user(c.from_user.id):
        await c.answer()
        await bot.send_message(c.from_user.id, "Анкета удалена. Ты можешь создать новую.", reply_markup=register_board)
    else:
        await c.answer()
        await bot.send_message(c.from_user.id, "Произошла ошибка при удалении анкеты. Пожалуйста, попробуй снова.")


@dp.callback_query_handler(lambda c: c.data == "register", state=None)
async def ask_city(c: types.CallbackQuery, state: FSMContext):
    await c.message.delete()
    async with state.proxy() as data:
        data["grade"] = set()
        data["skills"] = set()
    await RegistrationProcess.city.set()
    await bot.send_message(c.from_user.id,
                           "Напиши через запятую, из каких городов тебе интересны вакансии. Если хочешь работать только удалённо, нажми на соответствующую кнопку.",
                           reply_markup=remote_board)


@dp.message_handler(state=RegistrationProcess.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=[word.strip() for word in message.text.split(",")])
    await RegistrationProcess.allow_remote.set()
    await message.reply("Выбери, хочешь ли ты видеть вакансии с удалённой работой, и нажми на кнопку.",
                        reply_markup=yesno_board)


@dp.callback_query_handler(lambda c: c.data == "remote_only", state=RegistrationProcess.city)
async def process_city_only_remote(c: types.CallbackQuery, state: FSMContext):
    await c.message.delete()
    await RegistrationProcess.grade.set()
    await state.update_data(city=None)
    await state.update_data(allow_remote=True)
    grades_chosen = (await state.get_data())["grade"]
    await bot.send_message(c.from_user.id, text="Я запомнил. Теперь выбери, на какой ты претендуешь грейд.",
                           reply_markup=await grade_board(grades_chosen))


@dp.callback_query_handler(state=RegistrationProcess.allow_remote)
async def process_remote(c: types.CallbackQuery, state: FSMContext):
    await c.message.delete()
    await state.update_data(allow_remote=(c.data == "yes"))
    await RegistrationProcess.grade.set()
    grades_chosen = (await state.get_data())["grade"]
    await bot.send_message(chat_id=c.from_user.id, text="Хорошо. Теперь выбери грейды для поиска.",
                           reply_markup=await grade_board(grades_chosen))


@dp.callback_query_handler(lambda c: c.data == "continue", state=RegistrationProcess.grade)
async def process_grade(c: types.CallbackQuery, state: FSMContext):
    # async with state.proxy() as data:
    #    if not data["grade"]:
    if not (await state.get_data())["grade"]:
        return await c.answer(text="Ты ничего не выбрал!")
    await c.message.delete()
    await RegistrationProcess.allow_no_grade.set()
    await bot.send_message(chat_id=c.from_user.id,
                           text="Выбери, показывать ли вакансии без указанного грейда - их немного, но они есть.",
                           reply_markup=yesno_board)


@dp.callback_query_handler(state=RegistrationProcess.grade)
async def process_one_grade(c: types.CallbackQuery, state: FSMContext):
    await c.answer()
    async with state.proxy() as data:
        if c.data in data["grade"]:
            data["grade"].discard(c.data)
        else:
            data["grade"].add(c.data)
        grades_chosen = data["grade"]
    await bot.edit_message_reply_markup(chat_id=c.from_user.id, message_id=c.message.message_id,
                                        reply_markup=await grade_board(grades_chosen))


@dp.callback_query_handler(lambda c: c.data == "yes" or c.data == "no",
                           state=RegistrationProcess.allow_no_grade)
async def process_allow_no_grade(c: types.CallbackQuery, state: FSMContext):
    await c.message.delete()
    await state.update_data(allow_no_grade=(c.data == "yes"))
    await RegistrationProcess.skills.set()
    skills_chosen = (await state.get_data())["skills"]
    await bot.send_message(chat_id=c.from_user.id,
                           text="Выбери интересующие тебя специализации. Ты можешь дополнительно написать свои через запятую.",
                           reply_markup=await skills_board(skills_chosen))


@dp.callback_query_handler(lambda c: c.data == "continue", state=RegistrationProcess.skills)
async def process_skills(c: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if not data["skills"]:
            return await c.answer(text="Ты ничего не выбрал!")
    await RegistrationProcess.min_salary.set()
    await c.message.delete()
    await bot.send_message(chat_id=c.from_user.id,
                           text="Навыки сохранены. Напиши минимальную зарплату в долларах для показа вакансии.",
                           reply_markup=back_board)


@dp.callback_query_handler(state=RegistrationProcess.skills)
async def collecting_skills(c: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if c.data in data["skills"]:
            data["skills"].discard(c.data)
        else:
            data["skills"].add(c.data)
        chosen_skills = data["skills"]
    await bot.edit_message_reply_markup(chat_id=c.from_user.id, message_id=c.message.message_id,
                                        reply_markup=await skills_board(chosen_skills))


@dp.message_handler(state=RegistrationProcess.skills)
async def process_additional_skills(message: types.Message, state: FSMContext):
    await state.update_data(additional_skills=[word.strip() for word in message.text.split(",")])
    await message.reply(text="Я запомнил их и буду использовать при поиске."
                             " Если хочешь изменить этот список, просто отправь новый.")


@dp.message_handler(lambda message: len(message.text) > 10 or not message.text.isdigit(),
                    state=RegistrationProcess.min_salary)
async def process_bad_salary(message: types.Message):
    return await message.reply(text="Напиши число еще раз ☹", protect_content=True)


@dp.message_handler(state=RegistrationProcess.min_salary)
async def process_salary(message: types.Message, state: FSMContext):
    await state.update_data(min_salary=int(message.text))
    await RegistrationProcess.allow_no_salary.set()
    await bot.send_message(message.chat.id,
                           text="Хорошо. Показывать вакансии, в которых не указана зарплата? Таких много.",
                           reply_markup=yesno_board)


@dp.callback_query_handler(lambda c: c.data in ["yes", "no"], state=RegistrationProcess.allow_no_salary)
async def process_allow_no_salary(c: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data["allow_no_salary"] = (c.data == "yes")
        data["skills"].discard("switch_board")
        if not await db.add_user(user_id=c.from_user.id,
                                 city=data["city"],
                                 allow_remote=data["allow_remote"],
                                 grade=data["grade"],
                                 allow_no_grade=data["allow_no_grade"],
                                 skills=data["skills"],
                                 additional_skills=data.get("additional_skills", []),
                                 min_salary=data["min_salary"],
                                 allow_no_salary=data["allow_no_salary"]):
            return await bot.send_message(chat_id=c.from_user.id,
                                          text="Возникла ошибка при сохранении анкеты. Пожалуйста, попробуй снова.")
    await c.message.delete()
    await state.finish()
    await bot.send_message(chat_id=c.from_user.id,
                           text="Все готово, теперь ты можешь искать вакансии!",
                           reply_markup=InlineKeyboardMarkup().add(check_button))


@dp.callback_query_handler(state="*")
async def process_foo_callback(c: types.CallbackQuery):
    await c.answer()
    # user нажал кнопку из устаревшего сообщения


@dp.errors_handler(exception=TelegramAPIError)
async def print_tg_exc(error):
    print("[INFO] Telegram error occurred:", error)
    # Сервера тг часто тупят при поллинге и кидают ошибки. У меня была 1 раз, бот не лег
    return True


if __name__ == "__main__":
    asyncio.get_event_loop_policy().get_event_loop().create_task(db.initialize())
    executor.start_polling(dispatcher=dp, skip_updates=True)
    
