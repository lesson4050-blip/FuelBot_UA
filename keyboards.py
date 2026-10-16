from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import NETWORKS, FUEL_TYPES, PAYMENT_METHODS, DEFAULT_NOMINALS

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⛽ Купити пальне"), KeyboardButton(text="🎟 Мої талони")],
            [KeyboardButton(text="🚗 Заправитися"), KeyboardButton(text="📊 Мої замовлення")],
            [KeyboardButton(text="ℹ️ Ціни та довідка"), KeyboardButton(text="📞 Підтримка")]
        ],
        resize_keyboard=True
    )

def networks_keyboard():
    buttons = []
    for code, data in NETWORKS.items():
        buttons.append([InlineKeyboardButton(text=f"{data['icon']} {data['name']}", callback_data=f"net:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def fuel_types_keyboard(network: str):
    buttons = []
    for f_code, f_name in FUEL_TYPES.items():
        buttons.append([InlineKeyboardButton(text=f_name, callback_data=f"fuel:{network}:{f_code}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад до мереж", callback_data="back:networks")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def nominals_keyboard(network: str, fuel_type: str):
    buttons = []
    row = []
    for l in DEFAULT_NOMINALS:
        row.append(InlineKeyboardButton(text=f"{l} л", callback_data=f"vol:{network}:{fuel_type}:{l}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад до вибору пального", callback_data=f"net:{network}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_methods_keyboard(network: str, fuel_type: str, liters: int):
    buttons = []
    for p_code, p_data in PAYMENT_METHODS.items():
        btn_text = f"{p_data['title']} ({p_data['badge']})"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"pay:{network}:{fuel_type}:{liters}:{p_code}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Змінити літраж", callback_data=f"fuel:{network}:{fuel_type}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_order_keyboard(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити та отримати реквізити", callback_data=f"confirm_order:{order_id}")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_order")]
    ])

def payment_action_keyboard(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Я оплатив (надіслати квитанцію)", callback_data=f"paid:{order_id}")],
        [InlineKeyboardButton(text="⬅️ В головне меню", callback_data="to_main")]
    ])
