# rambler_set_2fa

[![Join our Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/cucumber_scripts)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/cucumber-pickle/Cucumber)
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@cucumber_scripts)


Python script for automatic rambler set 2FA


- [Запуск под Windows](#запуск-под-windows)
- [data / config](#Data-/-config)

## Запуск под Windows
- Установите [Python 3.11](https://www.python.org/downloads/windows/). Не забудьте поставить галочку напротив "Add Python to PATH".
- Установите [git](https://git-scm.com/download/win). Это позволит с легкостью получать обновления скрипта командой `git pull`
- Откройте консоль в удобном месте...
  - Склонируйте (или [скачайте](https://github.com/AromatUspexa/rambler_password_changer/archive/refs/heads/main.zip)) этот репозиторий:
    ```bash
    git clone https://github.com/AromatUspexa/rambler_set_2fa
    ```
  - Перейдите в папку проекта:
    ```bash
    cd rambler_set_2fa
    ```
  - Установите требуемые зависимости следующей командой или запуском файла `INSTALL.bat`:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
  - Запустите скрипт следующей командой или запуском файла `START.bat`:
    ```bash
    python main.py
    ```

## Data / config

- В файл `old_password.txt`, вставьте почты в формате:
    ```bash
    login:password
    login:password
    login:password
    ...
    ```

- В файлe `new_password.txt` будут сохранены данные в формате:
    ```bash
    login:password:secret
    login:password:secret
    login:password:secret
    ...
    ```

