from pyrogram import filters, Client, errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyromod import listen

import asyncio

from psm import psm
from psm.strings import strings


async def client_session(message, api_id, api_hash):
    return Client(":memory:", api_id=int(api_id), api_hash=str(api_hash))


@psm.on_message(filters.command("proceed") | ~filters.command("start"))
async def sessions_make(client, message):
    apid = await client.ask(message.chat.id, strings.APIID)
    if apid.text.startswith('/'):
        await message.reply(strings.CANCEL)
        return
    aphash = await client.ask(message.chat.id, strings.APIHASH)
    if aphash.text.startswith('/'):
        await message.reply(strings.CANCEL)
        return
    phone_token = await client.ask(message.chat.id, strings.PHONETOKEN)
    if phone_token.text.startswith('/'):
        await message.reply(strings.CANCEL)
        return
    if str(phone_token.text).startswith("+"):
        try:
            app = await client_session(message, api_id=apid.text, api_hash=aphash.text)
        except Exception as err:
            await message.reply(strings.ERROR.format(err=err))
            return
        try:
            await app.connect()
        except ConnectionError:
            await app.disconnect()
            await app.connect()
        try:
            sent_code = await app.send_code(phone_token.text)
        except errors.FloodWait as e:
            await message.reply(
                f"I cannot create session for you.\nYou have a floodwait of: `{e.x} seconds`"
            )
            return
        except errors.exceptions.bad_request_400.PhoneNumberInvalid:
            await message.reply(strings.INVALIDNUMBER)
            return
        except errors.exceptions.bad_request_400.ApiIdInvalid:
            await message.reply(strings.APIINVALID)
            return
        ans = await client.ask(message.chat.id, strings.PHONECODE)
        if ans.text.startswith('/'):
            await message.reply(strings.CANCEL)
            return
        try:
            await app.sign_in(phone_token.text, sent_code.phone_code_hash, ans.text)
        except errors.SessionPasswordNeeded:
            pas = await client.ask(message.chat.id, strings.PASSWORD)
            if pas.text.startswith('/'):
                await message.reply(strings.CANCEL)
                return
            try:
                await app.check_password(pas.text)
            except Exception as err:
                await message.reply(strings.ERROR.format(err=err))
                return
        except errors.PhoneCodeInvalid:
            await message.reply(strings.PHONECODEINVALID)
            return
        except errors.PhoneCodeExpired:
            await message.reply(strings.PHONECODEINVALID)
            return
        await app.send_message("me", f"```{(await app.export_session_string())}```")
        button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ : Go To Saved Messages",
                        url=f"tg://user?id={message.from_user.id}",
                    )
                ]
            ]
        )
        await message.reply(
            strings.DONEPHONE,
            reply_markup=button,
        )
    else:
        try:
            app = await client_session(message, api_id=apid.text, api_hash=aphash.text)
        except Exception as err:
            await message.reply(strings.ERROR.format(err=err))
            return
        try:
            await app.connect()
        except ConnectionError:
            await app.disconnect()
            await app.connect()
        try:
            await app.sign_in_bot(phone_token.text)
        except errors.exceptions.bad_request_400.AccessTokenInvalid:
            await message.reply(strings.BOTTOKENINVALID)
            return
        await message.reply(
            f"**✅ Here is Your Bot Session:**\n```{(await app.export_session_string())}```\n\n©️ @DamienSoukara"
        )
