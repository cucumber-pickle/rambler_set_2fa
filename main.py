import asyncio
from tqdm.asyncio import tqdm
from rambler_change.paths import PATH_LIST, PATH_NEW_LIST, PROXY_LIST, PATH_CONFIG
from rambler_change.class_account import AccountManager
from playwright.async_api import async_playwright
from loguru import logger

from data.conf import use_proxy, change_answer, change_password, same_answer, same_password, answer, password, two_FA
from rambler_change.logger import set_logger
from rambler_change.scripts import check_and_create_files, read_data, change_pass, update_api_key, change_ans, two_fa
from rambler_change.scripts import login_rambler, create_context, generate_valid_password, load_config



async def main():

    # Инициализация
    config = load_config(PATH_CONFIG)
    # api_key = config['API_KEY']
    # update_api_key(api_key, API_FILE)
    set_logger()
    check_and_create_files()

    all_accounts = AccountManager(PATH_LIST, PROXY_LIST, use_proxy)
    async with async_playwright() as playwright:
        data = read_data(PATH_LIST)
        with tqdm(total=len(data), desc="Изменение паролей", unit="пользователь", dynamic_ncols=True, leave=True) as pbar:
            with open(PATH_NEW_LIST, 'a') as new_file:
                for account in all_accounts.accounts:
                    context, page = await create_context(playwright, use_proxy, account.proxy)

                    #Генерируем новый пароль или используем статический
                    if same_password:
                        new_password = password
                    else:
                        new_password = generate_valid_password()

                    # Генерируем новый ответ или используем статический
                    if same_answer:
                        new_answer = answer
                    else:
                        new_answer = generate_valid_password()


                    await login_rambler(account.email, account.password, account.proxy, page)

                    #меняем ответ
                    if change_answer:
                        answer = await change_ans(page, context, account.email, account.password, new_answer)
                    else:
                        answer = ""

                    #устанавливаем 2FA
                    if two_FA:
                        secret = await two_fa(page, context, account.email, account.password)
                    else:
                        secret = ""

                    # меняем пароль
                    if change_password:
                        new_password = await change_pass(page, context, account.email, account.password, new_password)
                    else:
                        new_password = account.password

                    with open(PATH_NEW_LIST, 'a') as new_file:
                        new_file.write(f"{account.email}:{new_password}:{secret}\n")
                    if context:  # Проверяем, что контекст не был закрыт ранее
                        await context.close()

                    pbar.update(1)


if __name__ == "__main__":
    asyncio.run(main())


