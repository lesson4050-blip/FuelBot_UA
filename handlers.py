from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.filters import CommandStart, Command
from config import NETWORKS, FUEL_TYPES, PAYMENT_METHODS, USDT_RATE
import database as db
import keyboards as kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await db.add_or_update_user(user.id, user.username or "", user.full_name)
    await db.add_demo_coupons(user.id)
    
    welcome_text = (
        f"👋 Вітаємо, {user.first_name}!\n\n"
        "⛽ **Aurex Fuel Bot** — офіційний сервіс замовлення електронних талонів на пальне.\n\n"
        "🔹 **Партнерські мережі:** WOG, OKKO, Ukrnafta\n"
        "🔹 **3 рівні цін:** Юр. особи (ТОВ з ПДВ), ФОП, USDT (TRC20)\n"
        "🔹 **Безпека:** миттєвий облік талонів та пряма генерація QR на колонку.\n\n"
        "Оберіть потрібний розділ у меню нижче 👇"
    )
    await message.answer(welcome_text, reply_markup=kb.main_menu_keyboard(), parse_mode="Markdown")

@router.message(F.text == "⛽ Купити пальне")
async def handle_buy_fuel(message: Message):
    await message.answer(
        "⛽ **Крок 1/4: Оберіть мережу АЗС:**\n\n"
        "Кожна мережа має власні сценарії видачі талонів та актуальний прайс.",
        reply_markup=kb.networks_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back:networks")
async def cb_back_networks(call: CallbackQuery):
    await call.message.edit_text(
        "⛽ **Крок 1/4: Оберіть мережу АЗС:**",
        reply_markup=kb.networks_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("net:"))
async def cb_select_network(call: CallbackQuery):
    network = call.data.split(":")[1]
    net_data = NETWORKS.get(network, {})
    await call.message.edit_text(
        f"{net_data.get('icon', '⛽')} **Мережа: {net_data.get('name')}**\n\n"
        "👉 **Крок 2/4: Оберіть вид пального:**",
        reply_markup=kb.fuel_types_keyboard(network),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("fuel:"))
async def cb_select_fuel(call: CallbackQuery):
    _, network, fuel_code = call.data.split(":")
    net_name = NETWORKS.get(network, {}).get("name", network)
    fuel_name = FUEL_TYPES.get(fuel_code, fuel_code)
    
    base_price = await db.get_price(network, fuel_code)
    
    await call.message.edit_text(
        f"⛽ **Мережа:** {net_name}\n"
        f"💧 **Пальне:** {fuel_name}\n"
        f"🏷 **Базова ціна:** {base_price:.2f} грн/л\n\n"
        "👉 **Крок 3/4: Оберіть об'єм (літри):**",
        reply_markup=kb.nominals_keyboard(network, fuel_code),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("vol:"))
async def cb_select_volume(call: CallbackQuery):
    _, network, fuel_code, liters = call.data.split(":")
    liters = int(liters)
    base_price = await db.get_price(network, fuel_code)
    
    net_name = NETWORKS.get(network, {}).get("name")
    fuel_name = FUEL_TYPES.get(fuel_code)
    
    calc_text = (
        f"📋 **Розрахунок замовлення:**\n"
        f"• АЗС: **{net_name}**\n"
        f"• Пальне: **{fuel_name}**\n"
        f"• Об'єм: **{liters} л**\n\n"
        "💰 **Варіанти вартості за 3 рівнями цін:**\n"
    )
    
    for p_code, p_data in PAYMENT_METHODS.items():
        price_per_l = base_price * p_data["rate_mod"]
        total_uah = price_per_l * liters
        total_usdt = total_uah / USDT_RATE
        calc_text += f"— **{p_data['title']}** ({p_data['badge']}): `{total_uah:.2f} грн` (`{total_usdt:.2f} USDT`)\n"
        
    calc_text += "\n👉 **Крок 4/4: Оберіть спосіб оплати для формування рахунку:**"
    
    await call.message.edit_text(
        calc_text,
        reply_markup=kb.payment_methods_keyboard(network, fuel_code, liters),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("pay:"))
async def cb_select_payment(call: CallbackQuery):
    _, network, fuel_code, liters, p_method = call.data.split(":")
    liters = int(liters)
    base_price = await db.get_price(network, fuel_code)
    
    p_data = PAYMENT_METHODS.get(p_method, {})
    price_per_l = base_price * p_data.get("rate_mod", 1.0)
    total_uah = price_per_l * liters
    total_usdt = total_uah / USDT_RATE
    
    order_id = await db.create_order(
        call.from_user.id, network, fuel_code, liters, p_method, total_uah, total_usdt
    )
    
    net_name = NETWORKS.get(network, {}).get("name")
    fuel_name = FUEL_TYPES.get(fuel_code)
    
    summary_text = (
        f"🧾 **Замовлення #{order_id} сформовано!**\n\n"
        f"• АЗС: **{net_name}**\n"
        f"• Пальне: **{fuel_name}**\n"
        f"• Кількість: **{liters} л** ({liters // 10} талонів по 10 л)\n"
        f"• Спосіб оплати: **{p_data['title']}**\n"
        f"• До сплати: **{total_uah:.2f} UAH** / **{total_usdt:.2f} USDT**\n\n"
        "⚠️ *Ціна зафіксована на 60 хвилин.*\n"
        "Натисніть кнопку нижче, щоб отримати платіжні реквізити."
    )
    
    await call.message.edit_text(
        summary_text,
        reply_markup=kb.confirm_order_keyboard(order_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("confirm_order:"))
async def cb_confirm_order(call: CallbackQuery):
    order_id = call.data.split(":")[1]
    
    requisites_text = (
        f"🏦 **Реквізити для оплати замовлення #{order_id}:**\n\n"
        "🔹 **Оплата на ФОП / IBAN:**\n"
        "`UA893052990000026001234567890`\n"
        "Отримувач: ФОП Волошин І. О.\n"
        f"Призначення: `Оплата замовлення #{order_id}`\n\n"
        "🔹 **Оплата USDT (TRC20):**\n"
        "`TXaBcDeFgHiJkLmNoPqRsTuVwXyZ123456`\n\n"
        "⏳ Після переказу коштів натисніть кнопку **«Я оплатив»** та надішліть квитанцію (PDF, фото чи хеш транзакції) для ручної перевірки адміністратором."
    )
    
    await call.message.edit_text(
        requisites_text,
        reply_markup=kb.payment_action_keyboard(order_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("paid:"))
async def cb_paid(call: CallbackQuery):
    order_id = call.data.split(":")[1]
    await call.message.answer(
        f"📎 **Очікуємо квитанцію для замовлення #{order_id}**\n\n"
        "Будь ласка, надішліть сюди фото чека, скріншот квитанції або PDF-документ."
    )

@router.message(F.photo | F.document)
async def handle_payment_receipt(message: Message):
    await message.reply(
        "✅ **Квитанцію прийнято в обробку!**\n\n"
        "Дані передано черговому адміністратору. Після перевірки зарахування коштів "
        "талони автоматично з'являться у вашому розділі **«🎟 Мої талони»**.\n"
        "Середній час обробки: 3–5 хвилин.",
        parse_mode="Markdown"
    )

@router.message(F.text == "🎟 Мої талони")
async def handle_my_coupons(message: Message):
    coupons = await db.get_user_coupons(message.from_user.id)
    if not coupons:
        await message.answer(
            "📭 У вас поки немає активних талонів.\n"
            "Натисніть **«⛽ Купити пальне»**, щоб створити перше замовлення.",
            parse_mode="Markdown"
        )
        return
        
    text = "🎟 **Ваші доступні талони:**\n\n"
    for c in coupons:
        net_name = NETWORKS.get(c["network"], {}).get("name", c["network"]).upper()
        f_name = FUEL_TYPES.get(c["fuel_type"], c["fuel_type"])
        text += (
            f"🔹 **Талон #{c['id']}**\n"
            f"   • АЗС: {net_name}\n"
            f"   • Пальне: {f_name}\n"
            f"   • Номінал: **{c['liters']} л**\n"
            f"   • Статус: ✅ Доступний\n\n"
        )
    text += "Щоб використати талон на АЗС, натисніть кнопку **«🚗 Заправитися»**."
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🚗 Заправитися")
async def handle_refuel(message: Message):
    coupons = await db.get_user_coupons(message.from_user.id)
    if not coupons:
        await message.answer("⚠️ У вас немає активних талонів для заправки. Спочатку купіть пальне.")
        return
        
    text = (
        "🚗 **Сценарій заправки на АЗС:**\n\n"
        "1️⃣ **WOG / Ukrnafta:** Ви обираєте талон -> Натискаєте запит -> Бот видає вам персональний QR-код, який ви показуєте оператору на касі.\n"
        "2️⃣ **OKKO:** Ви під'їжджаєте до колонки -> Фотографуєте QR-код з колонки -> Надсилаєте в бот -> Адміністратор активує заправку віддалено.\n\n"
        "👉 Оберіть активний талон зі списку в **«🎟 Мої талони»**."
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "ℹ️ Ціни та довідка")
async def handle_prices_info(message: Message):
    text = (
        "📊 **Актуальні ціни на пальне (базовий тариф ФОП):**\n\n"
        "🟢 **WOG:**\n"
        "• А-95: 58.50 грн | ДП: 55.00 грн | Газ: 29.50 грн\n\n"
        "🟡 **OKKO:**\n"
        "• А-95: 58.50 грн | ДП: 55.00 грн | Газ: 29.50 грн\n\n"
        "🔵 **Ukrnafta:**\n"
        "• А-95: 54.00 грн | ДП: 51.00 грн | Газ: 27.50 грн\n\n"
        "💡 *При оплаті USDT діє додаткова знижка до 4%!*"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "📞 Підтримка")
async def handle_support(message: Message):
    await message.answer(
        "💬 **Служба підтримки клієнтів:**\n\n"
        "Оператор на зв'язку щодня з 08:00 до 22:00.\n"
        "З питань замовлень та заправок: @fuel_support_bot"
    )
