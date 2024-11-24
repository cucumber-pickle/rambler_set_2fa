import asyncio
import tempfile

import aiohttp
import toml
import json

from random import sample
from better_proxy import Proxy

import pyotp
import inquirer
from rambler_change.paths import PATH_LIST, PATH_EXTENSION, PATH_NEW_LIST, PROXY_LIST
from playwright.async_api import Playwright, Page, BrowserContext
from inquirer.themes import load_theme_from_dict
from termcolor import colored
from loguru import logger
from pathlib import Path
from anycaptcha import Solver, Service
import httpx
from lxml import html  # type: ignore


ALPHNUM = (
        'abcdefghijklmnopqrstuvwxyz' +
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ' +
        '01234567890' +
        '@$!*'
)


def load_config(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        config = toml.load(file)
    return config

def update_api_key(new_api_key: str, file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        settings = json.load(file)

    settings['clientKey'] = new_api_key

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)


def check_and_create_files():
    files_to_check = [PATH_NEW_LIST, PATH_LIST, PROXY_LIST]

    for file_path in files_to_check:
        if not file_path.exists():
            file_path.touch()
            print(f"Создан файл: {file_path}")
        else:
            ...


def generate_password(count=1, length=15, chars=ALPHNUM) -> str | list[str]:
    if count == 1:
        return ''.join(sample(chars, length))
    return [''.join(sample(chars, length)) for _ in range(count)]


def read_data(path_list: str) -> list[tuple[str, ...]]:
    with open(path_list, 'r') as file:
        return [tuple(line.strip().split(':')) for line in file]


def is_valid_password(password: str) -> bool:
    return (
            8 <= len(password) <= 32 and
            any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password)
    )


def generate_valid_password() -> str:
    while True:
        password = generate_password()
        if is_valid_password(password):
            return password


async def is_frame_exist(page: Page) -> bool:
    img_selector = "//div[@aria-checked='true']"
    try:
        frame_locator = page.frame_locator('iframe[title="Widget containing checkbox for hCaptcha security challenge"]')
        await frame_locator.locator(img_selector).wait_for(state='visible', timeout=60000)
        return True
    except Exception as e:
        logger.warning(f"Ошибка при проверке капчи")
        return False


async def check_login_errors(login, page) -> bool:
    try:
        await page.locator("//div[@class='rui-FieldStatus-message']").wait_for(state='visible', timeout=1000)
        logger.error(f'{login}: Ошибка входа! Проверьтье логин или пароль')
        return False
    except Exception as e:
        return True


async def is_captcha_exist(page: Page) -> bool:
    captcha_selector = '//div[@id="anchor"]'
    try:
        frame_locator = page.frame_locator('iframe[title="Widget containing checkbox for hCaptcha security challenge"]')
        await frame_locator.locator(captcha_selector).wait_for(state='visible', timeout=2000)
        return True
    except Exception as e:
        return False


async def solve_captcha(page: Page):
    while True:
        solve_status = await is_frame_exist(page)
        if solve_status:
            logger.info('Нажимаю на кнопку войти')
            await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').wait_for(
                state='visible', timeout=5000)
            await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').click()
            return False
        else:
            return True


async def change_pass(page, context, login, password, new_password) -> bool:
    await page.locator('//a[@href="/account/change-password"][@class]').wait_for(state='visible', timeout=60000)
    await page.locator('//a[@href="/account/change-password"][@class]').click()
    attempts = 0
    max_attempts = 5  # Добавляем максимальное количество попыток
    try:
        while attempts < max_attempts:
            await page.locator('//*[@id="password"]').fill(password)
            await page.locator('//*[@id="newPassword"]').fill(new_password)
            # await captcha()
            captcha_result = await is_frame_exist(page)
            if captcha_result:
                await page.locator('//button[@data-cerber-id="profile::change_password::save_password_button"]').click()
                await asyncio.sleep(1)
                # Дополнительная проверка на успешное изменение пароля
                success = await notification_password_change(page)
                if success:
                    logger.success(f'{login}: пароль успешно изменён!')
                    return True  # Успешно завершить цикл и функцию
                else:
                    logger.error(f'{login}: ошибка при изменении пароля. Повторяю попытку.')
                    await page.reload()
                    await asyncio.sleep(2)
            else:
                logger.warning("Капча не была решена! Перезагружаю страницу и повторяю попытку.")
                await page.reload()
                await asyncio.sleep(2)
            attempts += 1  # Увеличиваем счётчик попыток
        logger.error(f"{login}: Превышено количество попыток смены пароля.")
        return False
    finally:
        return new_password

async def change_ans(page, context, login, password, answer) -> bool:
    await page.locator('//a[@href="/account/change-question"][@class]').wait_for(state='visible', timeout=60000)
    await page.locator('//a[@href="/account/change-question"][@class]').click()
    attempts = 0
    max_attempts = 5  # Добавляем максимальное количество попыток
    try:
        while attempts < max_attempts:
            await page.locator('//*[@id="answer"]').fill(answer)
            await page.locator('//*[@id="password"]').fill(password)
            site_key = "322e5e22-3542-4638-b621-fa06db098460"
            url = 'https://id.rambler.ru/account/change-question'
            await asyncio.sleep(2)
            captcha_result = await is_frame_exist(page)
            if captcha_result:
                await page.locator('//button[@data-cerber-id="profile::change_question::save_question_button"]').click()
                await asyncio.sleep(1)
                # Дополнительная проверка на успешное изменение пароля
                success = await notification_password_change(page)
                if success:
                    logger.success(f'{login}: ответ успешно изменён!')
                    return True  # Успешно завершить цикл и функцию
                else:
                    logger.error(f'{login}: ошибка при изменении ответа. Повторяю попытку.')
                    await page.reload()
                    await asyncio.sleep(2)
            else:
                logger.warning("Капча не была решена! Перезагружаю страницу и повторяю попытку.")
                await page.reload()
                await asyncio.sleep(2)
            attempts += 1  # Увеличиваем счётчик попыток
        logger.error(f"{login}: Превышено количество попыток смены ответа.")
        return False
    except Exception as e:
        print(e)
    finally:
        await asyncio.sleep(1000)
        await page.goto('https://id.rambler.ru/account/profile')
        return answer

async def two_fa(page, context, login, password) -> bool:
    await page.locator('//a[@href="/account/two-factor-authn"][@class]').wait_for(state='visible', timeout=60000)
    await page.locator('//a[@href="/account/two-factor-authn"][@class]').click()

    await page.locator('//button[@type="button"][@class="rui-Button-button rui-Button-type-primary rui-Button-size-medium rui-Button-iconPosition-left src-containers-TwoFactorAuthn-Promo-styles--button--W24Wm"]').click()

    try:
        await page.locator('//*[@id="password"]').fill(password)

        await page.locator('//button[@type="button"][@class="src-containers-TwoFactorAuthn-Setup-styles--inlineButton--dmVJu"]').click()

        # Получение значения атрибута value
        secret = await page.locator('input.rui-Input-input.rui-Input-filled[readonly]').nth(1).get_attribute('value')

        code = pyotp.TOTP(secret).now()
        # Вывод значения
        print('Secret:', secret)

        await page.locator('//*[@id="code2fa"]').fill(code)
        await page.locator('//button[@type="submit"][@class="rui-Button-button rui-Button-type-primary rui-Button-size-medium rui-Button-iconPosition-left src-containers-TwoFactorAuthn-Setup-styles--button--MNn2z"]').click()

    finally:
        await asyncio.sleep(1)
        await page.goto('https://id.rambler.ru/account/profile')
        return secret

async def notification_password_change(page: Page) -> bool:
    try:
        await page.wait_for_selector(
            "//div[@class='rui-Snackbar-snackbar rui-Snackbar-center rui-Snackbar-top rui-Snackbar-success rui-Snackbar-isVisible']",
            state="visible", timeout=6000)
        return True
    except Exception as e:
        logger.error(f"Пароль не изменён, неизвестная ошибка")
        return False


async def login_rambler(login: str, password: str, proxy: Proxy, page):
    try:
        await page.goto('https://id.rambler.ru/login-20/login?rname')
    except Exception as e:
        if "net::ERR_HTTP_RESPONSE_CODE_FAILURE" in str(e):
            logger.error(f'Ошибка с прокси: {proxy.host} проверьте соеденение.')
    status_login = True
    while status_login:
        await page.locator('//*[@id="login"]').fill(login)
        await page.locator('//*[@id="password"]').fill(password)
        await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').click()
        exist_captcha = await is_captcha_exist(page)
        if exist_captcha:
            status_login = await solve_captcha(page)
            success = await check_login_errors(login, page)
            if success:
                break
        else:
            success = await check_login_errors(login, page)
            if success:
                break


async def create_context(playwright: Playwright, use_proxy: bool, proxy) -> tuple[BrowserContext, Page]:
    temp_dir = tempfile.mkdtemp()  # Создаем временную директорию, которая не удалится автоматически
    try:
        if use_proxy:
            context = await playwright.chromium.launch_persistent_context(
                proxy=proxy.as_playwright_proxy,
                user_data_dir=temp_dir,
                headless=False,

            )
            page = await context.new_page()
            return context, page
        else:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                headless=False,
            )

        page = await context.new_page()
        return context, page  # Возвращаем контекст и страницу для дальнейшего использования

    except Exception as e:
        logger.error(f"Ошибка при создании контекста браузера: {str(e)}")
    finally:
        # Не удаляем временную директорию сразу, т.к. браузер ещё может ею пользоваться
        pass  # Или если нужно уд
