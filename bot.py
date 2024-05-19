import logging
import os
import re
import paramiko
import psycopg2
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

token = os.getenv('TOKEN')
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
database = os.getenv('DB_DATABASE')


# Настройка логирования
logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Словарь для хранения состояния пользователей
user_state = {}
emails = 0

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(f'Привет, {user.full_name}!. Узнать список всех команд - /help')

def help_command(update: Update, context: CallbackContext) -> None:
    """Отправляет список всех доступных команд."""
    commands_list = [
        "/start - Начать работу с ботом",
        "/find_email - Найти email адреса в тексте",
        "/find_phone_number - Найти номера телефонов в тексте",
        "/verify_password - Проверить надежность пароля",
        "/get_release - Получить информацию о версии операционной системы",
        "/get_uname - Получить информацию о ядре операционной системы",
        "/get_uptime - Получить информацию о времени работы системы",
        "/get_df - Получить информацию о состоянии файловой системы",
        "/get_free - Получить информацию о состоянии оперативной памяти",
        "/get_mpstat - Получить информацию о производительности системы",
        "/get_w - Получить информацию о работающих пользователях",
        "/get_auths - Получить последние 10 входов в систему",
        "/get_critical - Получить последние 5 критических событий",
        "/get_ps - Получить информацию о запущенных процессах",
        "/get_ss - Получить информацию об используемых портах",
        "/get_apt_list - Получить информацию об установленных пакетах",
        "/get_services - Получить информацию о запущенных сервисах",
        "/help - Получить список всех доступных команд",
        "/get_repl_logs - Получить логи о реплакации",
        "/get_emails - Вывести почтовые адреса из БД",
        "/get_phone_numbers - Вывести номера телефонов из БД"
    ]
    help_text = "\n".join(commands_list)
    update.message.reply_text(help_text)

# Функция для команды /find_email
def find_email(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Введите текст, в котором нужно найти email-адреса:')

    # Устанавливаем состояние пользователя в ожидание текста для поиска email
    user_state[update.effective_user.id] = 'email'

# Функция для команды /find_phone_number
def find_phone_number(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Введите текст, в котором нужно найти номера телефонов:')

    # Устанавливаем состояние пользователя в ожидание текста для поиска номеров телефонов
    user_state[update.effective_user.id] = 'phone'

def verify_password(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Введите пароль для проверки его сложности:')

    # Устанавливаем состояние пользователя в ожидание пароля для проверки
    user_state[update.effective_user.id] = 'password'

def get_release(update: Update, context: CallbackContext) -> None:
    release_info = execute_ssh_command('cat /etc/*release*')
    update.message.reply_text(release_info)

def get_uname(update: Update, context: CallbackContext) -> None:
    uname_info = execute_ssh_command('uname -a')
    update.message.reply_text(uname_info)

def get_uptime(update: Update, context: CallbackContext) -> None:
    uptime_info = execute_ssh_command('uptime')
    update.message.reply_text(uptime_info)

# Функция для обработки текстовых сообщений
def text_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in user_state:
        text = update.message.text
        if user_state[user_id] == 'email':
            emails = re.findall(r'\b[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+)*' \
                r'@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b', text)
            if emails:
                context.user_data['emails'] = emails
                update.message.reply_text('Найденные email-адреса:\n' + '\n'.join(
                    emails) + "\nЖелаете записать их в бд?(Введите 'Да' или 'Нет')")
                user_state[update.effective_user.id] = 'email_conv'
            else:
                update.message.reply_text('Email-адреса не найдены.')
        elif user_state[user_id] == 'password':
            if re.match(r'(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}', text):
                update.message.reply_text('Пароль сложный.')
            else:
                update.message.reply_text('Пароль простой.')
        elif user_state[user_id] == 'phone':
            phone_numbers = re.findall(r"\+?7[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|\+?7[ -]?\d{10}|8[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|8[ -]?\d{10}", text)
            if phone_numbers:
                context.user_data['phone_numbers'] = phone_numbers
                update.message.reply_text('Найденные номера телефонов:\n' + '\n'.join(phone_numbers) + "\nЖелаете записать их в бд?(Введите 'Да' или 'Нет')")
                user_state[update.effective_user.id] = 'phone_conv'
            else:
                update.message.reply_text('Номера телефонов не найдены.')
        elif user_state[user_id] == 'email_conv':
            emails = context.user_data.get('emails', [])
            if text.lower() == 'да':
                connection = None
                try:
                    connection = psycopg2.connect(user=db_user,
                                                  password=db_password,
                                                  host=db_host,
                                                  port=db_port,
                                                  database=database)
                    cursor = connection.cursor()
                    for email in emails:
                        cursor.execute("INSERT INTO emails (email) VALUES (%s)", (email,))
                    connection.commit()
                    update.message.reply_text('Email-адреса успешно записаны в базу данных.')
                    logging.info("Информация успешно записана")
                except (Exception, psycopg2.Error) as error:
                    logging.error("Ошибка при работе с PostgreSQL: %s", error)
                    update.message.reply_text("Произошла ошибка при выполнении команды /get_emails")
                finally:
                    if connection is not None:
                        cursor.close()
                        connection.close()
            else:
                update.message.reply_text("Информация записана не будет")
            del user_state[user_id]
        elif user_state[user_id] == 'phone_conv':
            phone_numbers = context.user_data.get('phone_numbers', [])
            if text.lower() == 'да':
                connection = None
                try:
                    connection = psycopg2.connect(user=db_user,
                                                  password=db_password,
                                                  host=db_host,
                                                  port=db_port,
                                                  database=database)
                    cursor = connection.cursor()
                    for number in phone_numbers:
                        cursor.execute("INSERT INTO phone_numbers (phone_number) VALUES (%s)", (number,))
                    connection.commit()
                    update.message.reply_text('Номера успешно записаны в базу данных.')
                    logging.info("Информация успешно записана")
                except (Exception, psycopg2.Error) as error:
                    logging.error("Ошибка при работе с PostgreSQL: %s", error)
                    update.message.reply_text("Произошла ошибка при выполнении команды")
                finally:
                    if connection is not None:
                        cursor.close()
                        connection.close()
            else:
                update.message.reply_text("Информация записана не будет")
            del user_state[user_id]
def get_df(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('df -h')
    df_output = stdout.read().decode('utf-8')
    update.message.reply_text(df_output)
    ssh_client.close()

def get_free(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('free -m')
    free_output = stdout.read().decode('utf-8')
    update.message.reply_text(free_output)
    ssh_client.close()

def get_mpstat(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('mpstat')
    mpstat_output = stdout.read().decode('utf-8')
    if mpstat_output.strip():  # Проверяем, что вывод не пустой
        update.message.reply_text(mpstat_output)
    else:
        update.message.reply_text("Нет данных о производительности системы.")
    ssh_client.close()


def get_w(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('w')
    w_output = stdout.read().decode('utf-8')
    update.message.reply_text(w_output)
    ssh_client.close()
def get_auths(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('last -n 10')
    auths_output = stdout.read().decode('utf-8')
    update.message.reply_text(auths_output)
    ssh_client.close()

def get_critical(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('tail -n 5 /var/log/syslog | grep "CRITICAL"')
    critical_output = stdout.read().decode('utf-8')
    if critical_output.strip():  # Проверяем, что вывод не пустой
        update.message.reply_text(critical_output)
    else:
        update.message.reply_text("Нет критических событий.")
    ssh_client.close()

def get_ps(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('ps aux')
    ps_output = stdout.read().decode('utf-8')
    if len(ps_output) > 1000:
        ps_output = ps_output[:1000]
    update.message.reply_text(ps_output)
    ssh_client.close()

def get_ss(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('ss -tuln')
    ss_output = stdout.read().decode('utf-8')
    update.message.reply_text(ss_output)
    ssh_client.close()


def get_apt_list(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    if context.args:  # Если пользователь ввел аргументы, то ищем информацию о пакете
        package_name = ' '.join(context.args)
        command = f'dpkg-query -l | grep ^ii | grep {package_name}'
    else:
        command = 'dpkg-query -l | grep ^ii'
    stdin, stdout, stderr = ssh_client.exec_command(command)
    apt_list_output = stdout.read().decode('utf-8')
    if len(apt_list_output) > 1000:
        apt_list_output = apt_list_output[:1000] + '...'
    update.message.reply_text(apt_list_output)
    ssh_client.close()

def get_services(update: Update, context: CallbackContext) -> None:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=username, password=password)
    stdin, stdout, stderr = ssh_client.exec_command('systemctl list-units --type=service --all')
    services_output = stdout.read().decode('utf-8')
    if len(services_output) > 1000:
        services_output = services_output[:1000] + '...'
    update.message.reply_text(services_output)
    ssh_client.close()

def get_emails(update: Update, context: CallbackContext) -> None:
    connection = None
    try:
        connection = psycopg2.connect(user=db_user,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=database)
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()

        response = "\n".join([", ".join(map(str, row)) for row in data])

        update.message.reply_text(response)

        logging.info("Команда успешно выполнена")
    except (Exception, psycopg2.Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        update.message.reply_text("Произошла ошибка при выполнении команды /get_emails")
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def get_phone_numbers(update: Update, context: CallbackContext) -> None:
    connection = None
    try:
        connection = psycopg2.connect(user=db_user,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=database)
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM phone_numbers;")
        data = cursor.fetchall()

        response = "\n".join([", ".join(map(str, row)) for row in data])

        update.message.reply_text(response)

        logging.info("Команда успешно выполнена")
    except (Exception, psycopg2.Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        update.message.reply_text("Произошла ошибка при выполнении команды /get_emails")
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def execute_ssh_command(command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        if error:
            return f'Error: {error}'
        else:
            return output
    except Exception as e:
        return f'Error: {e}'
    finally:
        client.close()

def get_repl_logs(update: Update, context: CallbackContext) -> None:
    try:
        logs = execute_ssh_command("cat /var/log/postgresql/postgresql-14-main.log | grep replica | tail -n 20")
        update.message.reply_text("Logs:" +  logs)
        ssh_client.close()
    except Exception as e:
        logger.error("Произошла ошибка при выполнении команды /get_repl_logs: %s", str(e))
        update.message.reply_text("Произошла ошибка при выполнении команды /get_repl_logs")

def main():
    # Токен вашего бота
    updater = Updater(token, use_context=True)

    # Получение диспетчера обработчиков команд
    dispatcher = updater.dispatcher

    # Регистрация обработчиков команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("find_email", find_email))
    dispatcher.add_handler(CommandHandler("find_phone_number", find_phone_number))
    dispatcher.add_handler(CommandHandler("verify_password", verify_password))
    dispatcher.add_handler(CommandHandler("get_release", get_release))
    dispatcher.add_handler(CommandHandler("get_uname", get_uname))
    dispatcher.add_handler(CommandHandler("get_uptime", get_uptime))
    dispatcher.add_handler(CommandHandler("get_df", get_df))
    dispatcher.add_handler(CommandHandler("get_free", get_free))
    dispatcher.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dispatcher.add_handler(CommandHandler("get_w", get_w))
    dispatcher.add_handler(CommandHandler("get_auths", get_auths))
    dispatcher.add_handler(CommandHandler("get_critical", get_critical))
    dispatcher.add_handler(CommandHandler("get_ps", get_ps))
    dispatcher.add_handler(CommandHandler("get_ss", get_ss))
    dispatcher.add_handler(CommandHandler("get_apt_list", get_apt_list))
    dispatcher.add_handler(CommandHandler("get_services", get_services))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dispatcher.add_handler(CommandHandler("get_emails", get_emails))
    dispatcher.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))

    # Регистрация обработчика текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_message))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
