import requests
import time
import json
import random
from datetime import datetime, timedelta
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import ssl

# Настройки
TOKEN = "8466725404:AAFsxikWr8541rgTZcpxZdBXqdO-1qra4Mo"
ADMIN_CHAT_ID = "6319679398"
BOT_USERNAME = "Raketa_oxide_bot"
STATS_CHANNEL_ID = "-1003002379769"
STATS_MESSAGE_ID = 832
MAIN_GROUP_ID = "-1003117157578"
GROUP_INVITE_LINK = "https://t.me/+bjAMAhtua9xmNzgy"

# Права доступа
ADMIN_IDS = ["6319679398", "6999365345"]

# Web App URL (Vercel)
WEB_APP_URL = "https://ваш-проект.vercel.app"  # Замените на ваш Vercel URL
API_SECRET_KEY = "raketa_secret_key_2024"  # Секретный ключ для API

# Глобальные переменные
users_data = {}
treasury = 25
last_treasury_update = time.time()
withdraw_codes = {}
withdraw_requests = {}
last_update_id = 0
groups_data = {}
active_games = {}

print("🚀 Инициализация бота Ракета 3.0...")
print(f"🌐 Web App URL: {WEB_APP_URL}")

# === ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ===
def save_data():
    """Сохранение данных в файл"""
    try:
        data = {
            'users_data': users_data,
            'treasury': treasury,
            'last_treasury_update': last_treasury_update,
            'withdraw_codes': withdraw_codes,
            'withdraw_requests': withdraw_requests,
            'groups_data': groups_data
        }
        with open('bot_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("💾 Данные сохранены")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")
        return False

def load_data():
    """Загрузка данных из файла"""
    global users_data, treasury, last_treasury_update, withdraw_codes, withdraw_requests, groups_data
    try:
        with open('bot_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            users_data = data.get('users_data', {})
            treasury = data.get('treasury', 25)
            last_treasury_update = data.get('last_treasury_update', time.time())
            withdraw_codes = data.get('withdraw_codes', {})
            withdraw_requests = data.get('withdraw_requests', {})
            groups_data = data.get('groups_data', {})
        active_games.clear()
        print("📂 Данные загружены")
        print(f"👥 Пользователей: {len(users_data)}")
        print(f"💰 Казна: {treasury}₽")
        print(f"👥 Групп: {len(groups_data)}")
        return True
    except FileNotFoundError:
        print("❌ Файл данных не найден, создаем новый...")
        users_data = {}
        treasury = 25
        last_treasury_update = time.time()
        withdraw_codes = {}
        withdraw_requests = {}
        groups_data = {}
        return True
    except Exception as e:
        print(f"❌ Ошибка при загрузке данных: {e}")
        users_data = {}
        treasury = 25
        last_treasury_update = time.time()
        withdraw_codes = {}
        withdraw_requests = {}
        groups_data = {}
        return False

def is_group_allowed(chat_id):
    """Проверяет, разрешена ли группа для использования бота"""
    return str(chat_id) in groups_data and groups_data[str(chat_id)].get('enabled', False)

def has_admin_rights(user_id):
    """Проверяет права администратора"""
    return str(user_id) in ADMIN_IDS

# === ПРОСТОЙ HTTP СЕРВЕР ДЛЯ API ===
class APIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Обработка CORS preflight запросов"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Обработка GET запросов"""
        try:
            # Парсим путь и параметры
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            print(f"🌐 GET запрос: {path}")
            
            # Устанавливаем заголовки CORS
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if path == '/api/get_user_data':
                user_id = query_params.get('user_id', [''])[0]
                if not user_id:
                    self.wfile.write(json.dumps({'success': False, 'error': 'No user_id'}).encode())
                    return
                
                if user_id in users_data:
                    user_data = users_data[user_id]
                    response = {
                        'success': True,
                        'balance': user_data.get('balance', 0),
                        'business_level': user_data.get('business_level', 0),
                        'treasury': treasury,
                        'last_robbery_time': user_data.get('last_robbery_time', 0),
                        'last_casino_time': user_data.get('last_casino_time', 0),
                        'robbery_count': user_data.get('robbery_count', 0),
                        'daily_robbery_earnings': user_data.get('daily_robbery_earnings', 0),
                        'last_daily_bonus': user_data.get('last_daily_bonus', ''),
                        'last_robbery_date': user_data.get('last_robbery_date', ''),
                        'username': user_data.get('username', f'user_{user_id}')
                    }
                else:
                    # Создаем нового пользователя
                    users_data[user_id] = {
                        'username': f'user_{user_id}',
                        'balance': 0,
                        'business_level': 0,
                        'last_robbery_time': 0,
                        'last_casino_time': 0,
                        'robbery_count': 0,
                        'daily_robbery_earnings': 0,
                        'last_daily_bonus': None,
                        'last_robbery_date': datetime.now().strftime("%Y-%m-%d")
                    }
                    save_data()
                    
                    response = {
                        'success': True,
                        'balance': 0,
                        'business_level': 0,
                        'treasury': treasury,
                        'last_robbery_time': 0,
                        'last_casino_time': 0,
                        'robbery_count': 0,
                        'daily_robbery_earnings': 0,
                        'last_daily_bonus': '',
                        'last_robbery_date': datetime.now().strftime("%Y-%m-%d"),
                        'username': f'user_{user_id}'
                    }
                
                self.wfile.write(json.dumps(response).encode())
                
            elif path == '/api/get_bot_stats':
                user_id = query_params.get('user_id', [''])[0]
                
                # Рейтинг пользователя
                user_rank = None
                if user_id and user_id in users_data:
                    sorted_users = sorted(
                        [(uid, ud.get('balance', 0)) for uid, ud in users_data.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    for rank, (uid, _) in enumerate(sorted_users, 1):
                        if uid == user_id:
                            user_rank = rank
                            break
                
                response = {
                    'success': True,
                    'total_users': len(users_data),
                    'treasury': treasury,
                    'active_games': len(active_games),
                    'user_rank': user_rank
                }
                
                self.wfile.write(json.dumps(response).encode())
                
            elif path == '/api/full_stats':
                user_id = query_params.get('user_id', [''])[0]
                
                total_balance = sum(user.get('balance', 0) for user in users_data.values())
                business_users = len([user for user in users_data.values() if user.get('business_level', 0) > 0])
                
                # Топ 5 пользователей
                top_users = sorted(
                    [(user.get('username', 'user'), user.get('balance', 0)) 
                     for user in users_data.values()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                # Рейтинг пользователя
                user_rank = None
                user_stats = {}
                
                if user_id and user_id in users_data:
                    sorted_users = sorted(
                        [(uid, ud.get('balance', 0)) for uid, ud in users_data.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    for rank, (uid, _) in enumerate(sorted_users, 1):
                        if uid == user_id:
                            user_rank = rank
                            break
                    
                    user_data = users_data[user_id]
                    user_stats = {
                        'balance': user_data.get('balance', 0),
                        'robbery_count': user_data.get('robbery_count', 0),
                        'business_level': user_data.get('business_level', 0)
                    }
                
                response = {
                    'success': True,
                    'total_users': len(users_data),
                    'total_balance': total_balance,
                    'business_users': business_users,
                    'treasury': treasury,
                    'active_games': len(active_games),
                    'top_users': [{'username': u[0], 'balance': u[1]} for u in top_users],
                    'user_rank': user_rank,
                    'user_stats': user_stats
                }
                
                self.wfile.write(json.dumps(response).encode())
                
            else:
                self.send_response(404)
                self.wfile.write(json.dumps({'success': False, 'error': 'Not found'}).encode())
                
        except Exception as e:
            print(f"❌ Ошибка обработки GET запроса: {e}")
            self.send_response(500)
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def do_POST(self):
        """Обработка POST запросов"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            print(f"🌐 POST запрос: {self.path}")
            
            # Проверка секретного ключа (опционально)
            secret_key = self.headers.get('Authorization', '').replace('Bearer ', '')
            if secret_key != API_SECRET_KEY:
                # Для теста разрешаем без ключа
                pass
            
            # Устанавливаем заголовки CORS
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if self.path == '/api/rob_treasury':
                user_id = str(data.get('user_id'))
                username = data.get('username', f'user_{user_id}')
                
                # Создаем пользователя если не существует
                if user_id not in users_data:
                    users_data[user_id] = {
                        'username': username,
                        'balance': 0,
                        'business_level': 0,
                        'last_income': 0,
                        'robbery_count': 0,
                        'last_robbery_date': datetime.now().strftime("%Y-%m-%d"),
                        'last_robbery_time': 0,
                        'last_daily_bonus': None,
                        'last_casino_time': 0,
                        'daily_robbery_earnings': 0
                    }
                
                user_data = users_data[user_id]
                current_time = time.time()
                
                # Проверяем кулдаун (30 минут)
                if current_time - user_data.get('last_robbery_time', 0) < 1800:
                    response = {
                        'success': False,
                        'message': 'Подождите 30 минут до следующего ограбления'
                    }
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                # Проверяем дневной лимит (3 ограбления в день)
                today = datetime.now().strftime("%Y-%m-%d")
                if user_data.get('last_robbery_date') != today:
                    user_data['robbery_count'] = 0
                    user_data['daily_robbery_earnings'] = 0
                    user_data['last_robbery_date'] = today
                
                if user_data.get('robbery_count', 0) >= 3:
                    response = {
                        'success': False,
                        'message': 'Достигнут дневной лимит ограблений (3/день)'
                    }
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                # Обновляем казну (каждые 2 часа)
                global treasury, last_treasury_update
                if current_time - last_treasury_update > 7200:
                    treasury = random.randint(25, 100)
                    last_treasury_update = current_time
                
                # Шанс успеха 90%
                success = random.random() <= 0.9
                
                if success:
                    stolen_amount = random.randint(1, min(20, treasury))
                    treasury -= stolen_amount
                    if treasury < 0:
                        treasury = 0
                    
                    user_data['balance'] = user_data.get('balance', 0) + stolen_amount
                    user_data['robbery_count'] = user_data.get('robbery_count', 0) + 1
                    user_data['daily_robbery_earnings'] = user_data.get('daily_robbery_earnings', 0) + stolen_amount
                    user_data['last_robbery_time'] = current_time
                    
                    result = {
                        'success': True,
                        'stolen_amount': stolen_amount,
                        'new_balance': user_data['balance'],
                        'new_treasury': treasury,
                        'message': f'Успех! Украдено {stolen_amount}₽'
                    }
                else:
                    user_data['robbery_count'] = user_data.get('robbery_count', 0) + 1
                    user_data['last_robbery_time'] = current_time
                    
                    result = {
                        'success': True,
                        'stolen_amount': 0,
                        'new_balance': user_data['balance'],
                        'new_treasury': treasury,
                        'message': 'Ограбление провалилось! Охрана поймала вас!'
                    }
                
                save_data()
                update_stats_message()
                
                self.wfile.write(json.dumps(result).encode())
                
            elif self.path == '/api/play_casino':
                user_id = str(data.get('user_id'))
                username = data.get('username', f'user_{user_id}')
                amount = int(data.get('amount', 0))
                
                if user_id not in users_data:
                    users_data[user_id] = {
                        'username': username,
                        'balance': 0,
                        'business_level': 0,
                        'last_income': 0,
                        'robbery_count': 0,
                        'last_robbery_date': datetime.now().strftime("%Y-%m-%d"),
                        'last_robbery_time': 0,
                        'last_daily_bonus': None,
                        'last_casino_time': 0,
                        'daily_robbery_earnings': 0
                    }
                
                user_data = users_data[user_id]
                balance = user_data.get('balance', 0)
                
                if amount <= 0:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Ставка должна быть положительной'}).encode())
                    return
                
                if balance < amount:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Недостаточно средств'}).encode())
                    return
                
                # Проверяем кулдаун (10 секунд)
                current_time = time.time()
                if current_time - user_data.get('last_casino_time', 0) < 10:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Подождите 10 секунд'}).encode())
                    return
                
                # Шанс выигрыша 30%
                win = random.randint(1, 100) <= 30
                
                if win:
                    win_amount = amount * 2
                    user_data['balance'] = balance + win_amount
                    result = {
                        'success': True,
                        'win': True,
                        'win_amount': win_amount,
                        'new_balance': user_data['balance'],
                        'message': f'ДЖЕКПОТ! Вы выиграли {win_amount}₽'
                    }
                else:
                    user_data['balance'] = balance - amount
                    result = {
                        'success': True,
                        'win': False,
                        'new_balance': user_data['balance'],
                        'message': f'Вы проиграли {amount}₽'
                    }
                
                user_data['last_casino_time'] = current_time
                save_data()
                update_stats_message()
                
                self.wfile.write(json.dumps(result).encode())
                
            elif self.path == '/api/daily_bonus':
                user_id = str(data.get('user_id'))
                username = data.get('username', f'user_{user_id}')
                
                if user_id not in users_data:
                    users_data[user_id] = {
                        'username': username,
                        'balance': 0,
                        'business_level': 0,
                        'last_income': 0,
                        'robbery_count': 0,
                        'last_robbery_date': datetime.now().strftime("%Y-%m-%d"),
                        'last_robbery_time': 0,
                        'last_daily_bonus': None,
                        'last_casino_time': 0,
                        'daily_robbery_earnings': 0
                    }
                
                user_data = users_data[user_id]
                today = datetime.now().strftime("%Y-%m-%d")
                
                if user_data.get('last_daily_bonus') == today:
                    self.wfile.write(json.dumps({
                        'success': False,
                        'message': 'Бонус уже получен сегодня'
                    }).encode())
                    return
                
                bonus_amount = 5
                user_data['balance'] = user_data.get('balance', 0) + bonus_amount
                user_data['last_daily_bonus'] = today
                
                save_data()
                update_stats_message()
                
                self.wfile.write(json.dumps({
                    'success': True,
                    'bonus_amount': bonus_amount,
                    'new_balance': user_data['balance'],
                    'message': f'Бонус получен: +{bonus_amount}₽'
                }).encode())
                
            elif self.path == '/api/transfer_money':
                from_user_id = str(data.get('from_user_id'))
                to_user_id = str(data.get('to_user_id'))
                amount = int(data.get('amount', 0))
                
                if from_user_id not in users_data:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Отправитель не найден'}).encode())
                    return
                
                if to_user_id not in users_data:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Получатель не найден'}).encode())
                    return
                
                if from_user_id == to_user_id:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Нельзя переводить себе'}).encode())
                    return
                
                if amount <= 0:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Сумма должна быть положительной'}).encode())
                    return
                
                from_user = users_data[from_user_id]
                to_user = users_data[to_user_id]
                
                if from_user.get('balance', 0) < amount:
                    self.wfile.write(json.dumps({'success': False, 'error': 'Недостаточно средств'}).encode())
                    return
                
                from_user['balance'] = from_user.get('balance', 0) - amount
                to_user['balance'] = to_user.get('balance', 0) + amount
                
                save_data()
                update_stats_message()
                
                self.wfile.write(json.dumps({
                    'success': True,
                    'from_balance': from_user['balance'],
                    'to_balance': to_user['balance'],
                    'message': f'Перевод {amount}₽ выполнен успешно'
                }).encode())
                
            else:
                self.send_response(404)
                self.wfile.write(json.dumps({'success': False, 'error': 'Not found'}).encode())
                
        except Exception as e:
            print(f"❌ Ошибка обработки POST запроса: {e}")
            self.send_response(500)
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

def start_api_server(port=8080):
    """Запуск API сервера в отдельном потоке"""
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    
    def run_server():
        print(f"🌐 API сервер запущен на порту {port}")
        print(f"📡 API доступен по адресу: http://localhost:{port}")
        server.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return server, thread

# === ФУНКЦИИ ДЛЯ РАБОТЫ С TELEGRAM API ===
def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup

        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Ошибка отправки в {chat_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return False

def edit_message(chat_id, message_id, text, reply_markup=None):
    """Редактирование сообщения"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup

        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка редактирования сообщения: {e}")
        return False

def update_stats_message():
    """Обновление сообщения со статистикой"""
    try:
        stats_text = generate_stats_text()
        success = edit_message(STATS_CHANNEL_ID, STATS_MESSAGE_ID, stats_text)
        if success:
            print("✅ Статистика обновлена")
        else:
            print("❌ Не удалось обновить статистику")
        return success
    except Exception as e:
        print(f"❌ Ошибка обновления статистики: {e}")
        return False

def generate_stats_text():
    """Генерирует текст статистики"""
    total_users = len(users_data)
    total_balance = sum(user_data.get('balance', 0) for user_data in users_data.values())
    business_users = len([user_data for user_data in users_data.values() if user_data.get('business_level', 0) > 0])
    
    top_users = []
    for user_id, user_data in users_data.items():
        if str(user_id) not in ADMIN_IDS:
            top_users.append({
                'username': user_data.get('username', 'user'),
                'balance': user_data.get('balance', 0),
                'business_level': user_data.get('business_level', 0)
            })
    
    top_users.sort(key=lambda x: x['balance'], reverse=True)
    top_5_users = top_users[:5]
    
    stats_text = (
        f"📊 <b>СТАТИСТИКА БОТА РАКЕТА 3.0</b>\n\n"
        f"👥 <b>Общая статистика:</b>\n"
        f"• Пользователей: {total_users}\n"
        f"• Общий баланс: {total_balance}₽\n"
        f"• Владельцев бизнеса: {business_users}\n"
        f"• Казна: {treasury}₽\n"
        f"• Групп: {len(groups_data)}\n"
        f"• Активных игр: {len(active_games)}\n\n"
        f"🌐 <b>Web App:</b> /webapp\n\n"
        f"🏆 <b>ТОП-5 ПОЛЬЗОВАТЕЛЕЙ:</b>\n"
    )
    
    if top_5_users:
        for i, user in enumerate(top_5_users, 1):
            medal = ""
            if i == 1: medal = "🥇"
            elif i == 2: medal = "🥈"
            elif i == 3: medal = "🥉"
            else: medal = f"{i}."
            
            business_info = ""
            if user['business_level'] > 0:
                business_info = f" | 🏢 Ур.{user['business_level']}"
            
            stats_text += f"{medal} @{user['username']} - {user['balance']}₽{business_info}\n"
    else:
        stats_text += "Пока нет активных пользователей\n"
    
    stats_text += f"\n🕒 <i>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
    
    return stats_text

# === ОСНОВНЫЕ КОМАНДЫ БОТА ===
def handle_start(chat_id, user_id, username):
    """Обработка команды /start"""
    print(f"👋 Обработка /start от @{username}")
    
    if str(chat_id) == str(ADMIN_CHAT_ID) and has_admin_rights(user_id):
        # Админское меню
        send_message(chat_id,
            f"🛠️ <b>АДМИН ПАНЕЛЬ</b>\n\n"
            f"🌐 <b>Web App:</b>\n"
            f"• URL: {WEB_APP_URL}\n"
            f"• API ключ: {API_SECRET_KEY}\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Пользователей: {len(users_data)}\n"
            f"• Общий баланс: {sum(u.get('balance', 0) for u in users_data.values())}₽\n"
            f"• Групп: {len(groups_data)}\n\n"
            f"💡 <b>Команды:</b>\n"
            f"• /webapp - открыть Web App\n"
            f"• /stats - статистика\n"
            f"• /groups - управление группами"
        )
    else:
        # Обычное меню
        send_message(chat_id,
            f"👋 <b>Добро пожаловать, {username}!</b>\n\n"
            f"💼 <b>Бизнес-бот Ракета 3.0</b>\n\n"
            f"🌐 <b>НОВЫЙ WEB APP!</b>\n"
            f"Откройте через команду /webapp\n\n"
            f"🎮 <b>Доступные команды:</b>\n"
            f"• /balance - ваш баланс\n"
            f"• /bonus - ежедневный бонус\n"
            f"• /webapp - открыть Web App\n"
            f"• /help - помощь\n\n"
            f"💎 <b>Присоединяйтесь к нашей группе:</b>\n"
            f"👉 {GROUP_INVITE_LINK}\n\n"
            f"⚡ <b>Начните зарабатывать прямо сейчас!</b>"
        )

def handle_webapp_command(chat_id, user_id, username):
    """Команда для открытия Web App"""
    keyboard = {
        "inline_keyboard": [[
            {"text": "🚀 Открыть Web App", "web_app": {"url": WEB_APP_URL}}
        ]]
    }
    
    send_message(chat_id,
        f"🌐 <b>Web App Ракета 3.0</b>\n\n"
        f"👤 <b>Для:</b> @{username}\n"
        f"📱 <b>Доступно:</b> На любом устройстве\n"
        f"🔗 <b>Ссылка:</b> {WEB_APP_URL}\n\n"
        f"🎮 <b>В Web App доступно:</b>\n"
        f"• Полная статистика бота\n"
        f"• Ограбление казны\n"
        f"• Казино 30%\n"
        f"• Перевод денег\n"
        f"• Ежедневный бонус\n\n"
        f"👇 <b>Нажмите кнопку ниже чтобы открыть:</b>",
        keyboard)

def handle_balance(chat_id, user_id, username):
    """Показывает баланс пользователя"""
    # Создаем пользователя если не существует
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {
            'username': username,
            'balance': 0,
            'business_level': 0,
            'last_income': 0,
            'robbery_count': 0,
            'last_robbery_date': datetime.now().strftime("%Y-%m-%d"),
            'last_robbery_time': 0,
            'last_daily_bonus': None,
            'last_casino_time': 0,
            'daily_robbery_earnings': 0
        }
        save_data()
    
    user_data = users_data[str(user_id)]
    balance = user_data.get('balance', 0)
    business_level = user_data.get('business_level', 0)
    
    business_info = ""
    if business_level > 0:
        business_info = f"\n🏢 <b>Бизнес:</b> Ур.{business_level}"
    
    send_message(chat_id,
        f"💼 <b>БАЛАНС</b>\n\n"
        f"👤 <b>Игрок:</b> @{username}\n"
        f"💰 <b>Баланс:</b> {balance}₽"
        f"{business_info}\n\n"
        f"🌐 <b>Web App:</b> /webapp")

def handle_daily_bonus(chat_id, user_id, username):
    """Выдача ежедневного бонуса"""
    # Создаем пользователя если не существует
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {
            'username': username,
            'balance': 0,
            'business_level': 0,
            'last_income': 0,
            'robbery_count': 0,
            'last_robbery_date': datetime.now().strftime("%Y-%m-%d"),
            'last_robbery_time': 0,
            'last_daily_bonus': None,
            'last_casino_time': 0,
            'daily_robbery_earnings': 0
        }
    
    user_data = users_data[str(user_id)]
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user_data.get('last_daily_bonus') == today:
        send_message(chat_id,
            f"🎁 <b>Бонус уже получен!</b>\n\n"
            f"💡 <b>Следующий бонус будет доступен завтра</b>")
        return
    
    bonus_amount = 5
    user_data['balance'] = user_data.get('balance', 0) + bonus_amount
    user_data['last_daily_bonus'] = today
    save_data()
    
    send_message(chat_id,
        f"🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n"
        f"👤 <b>Пользователь:</b> @{username}\n"
        f"💰 <b>Получено:</b> {bonus_amount}₽\n"
        f"💎 <b>Ваш баланс:</b> {user_data['balance']}₽\n\n"
        f"💡 <b>Возвращайтесь за новым бонусом завтра!</b>")
    
    update_stats_message()

def send_bot_started_message():
    """Отправляет сообщение о запуске бота"""
    console_message = f"""
╔══════════════════════════════╗
║         🤖 БОТ ЗАПУЩЕН!      ║
╠══════════════════════════════╣
║ 🌐 Web App: {WEB_APP_URL}
║ 🔑 API ключ: {API_SECRET_KEY}
║ 📍 Основная группа: {MAIN_GROUP_ID}
║ 👑 Админы: {ADMIN_IDS}
║ 🕒 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}
║ 👥 Пользователей: {len(users_data)}
║ 💰 Казна: {treasury}₽
║ 👥 Групп: {len(groups_data)}
╚══════════════════════════════╝
⚡ Бот готов к работе!

🌐 Web App доступен по команде /webapp
📡 API сервер запущен на порту 8080
    """
    print(console_message)
    
    # Сообщение в основную группу
    group_message = (
        f"🤖 <b>БОТ РАКЕТА 3.0 ЗАПУЩЕН!</b>\n\n"
        f"✅ <b>Система активирована и готова к работе!</b>\n\n"
        f"🌐 <b>НОВЫЙ WEB APP!</b>\n"
        f"• Откройте через команду /webapp\n"
        f"• Работает на любом устройстве\n"
        f"• Все функции бота в одном месте\n\n"
        f"📊 <b>Текущая статистика:</b>\n"
        f"• 👥 Пользователей: {len(users_data)}\n"
        f"• 💰 Казна: {treasury}₽\n"
        f"• 👥 Групп: {len(groups_data)}\n"
        f"• 🕒 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"🎮 <b>Доступные команды:</b>\n"
        f"• /balance - ваш баланс\n"
        f"• /bonus - ежедневный бонус\n"
        f"• ограбить казну - ограбление\n"
        f"• казино [сумма] - игра в казино\n"
        f"• /webapp - открыть Web App\n\n"
        f"⚡ <b>Удачи в заработке!</b>"
    )
    
    send_message(MAIN_GROUP_ID, group_message)

# === ОСНОВНОЙ ЦИКЛ БОТА ===
def main():
    global last_update_id
    
    # Загрузка данных
    load_data()
    
    # Автоматически включаем основную группу если ее нет
    if MAIN_GROUP_ID not in groups_data:
        groups_data[MAIN_GROUP_ID] = {
            'title': "Основная группа",
            'enabled': True,
            'admin_actions_enabled': False,
            'added_by': "system",
            'added_date': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_data()
    
    # Запуск API сервера
    api_server, api_thread = start_api_server(8080)
    
    # Отправка сообщения о запуске
    send_bot_started_message()
    
    # Обновление статистики
    update_stats_message()
    
    print("⚡ Бот готов к работе! Ожидание сообщений...")
    print("🌐 Web App доступен по адресу:", WEB_APP_URL)
    
    # Основной цикл обработки сообщений
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            payload = {
                'offset': last_update_id + 1,
                'timeout': 30
            }
            
            response = requests.post(url, json=payload, timeout=35)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'result' in data:
                    for update in data['result']:
                        last_update_id = update['update_id']
                        
                        # Обработка сообщений
                        if 'message' in update and 'text' in update['message']:
                            message = update['message']
                            chat_id = message['chat']['id']
                            text = message['text'].strip()
                            user_id = message['from']['id']
                            username = message['from'].get('username', 'user')
                            text_lower = text.lower()
                            
                            print(f"📨 Сообщение от @{username} в {chat_id}: {text}")
                            
                            # Проверяем, разрешен ли чат
                            if str(chat_id) != str(ADMIN_CHAT_ID) and not is_group_allowed(chat_id):
                                send_message(chat_id,
                                    f"🚫 <b>Бот работает только в разрешенных группах!</b>\n\n"
                                    f"💎 <b>Присоединяйтесь к нашей основной группе:</b>\n"
                                    f"👉 {GROUP_INVITE_LINK}")
                                continue
                            
                            # Обработка команд
                            if text_lower == '/start' or text_lower.startswith('/start@'):
                                handle_start(chat_id, user_id, username)
                            
                            elif text_lower == '/balance' or text_lower == 'б' or text_lower == 'баланс':
                                handle_balance(chat_id, user_id, username)
                            
                            elif text_lower == '/bonus':
                                handle_daily_bonus(chat_id, user_id, username)
                            
                            elif text_lower == '/webapp':
                                handle_webapp_command(chat_id, user_id, username)
                            
                            elif text_lower in ['ограбить казну', 'ограбить', 'грабить казну', 'ограбление']:
                                # Обработка ограбления в чате
                                handle_robbery_in_chat(chat_id, user_id, username)
                            
                            elif text_lower.startswith('казино '):
                                try:
                                    amount_text = text_lower.split()[1]
                                    handle_casino_in_chat(chat_id, user_id, username, amount_text)
                                except IndexError:
                                    send_message(chat_id, "❌ <b>Укажите сумму! Используйте: казино [сумма]</b>")
                            
                            elif text_lower == 'казино':
                                send_message(chat_id,
                                    f"🎰 <b>КАЗИНО 30%</b>\n\n"
                                    f"📊 <b>Правила игры:</b>\n"
                                    f"• Шанс выигрыша: 30%\n"
                                    f"• При выигрыше: x2 от ставки\n"
                                    f"• При проигрыше: теряете ставку\n"
                                    f"• Кулдаун: 10 секунд\n\n"
                                    f"🎯 <b>Как играть:</b>\n"
                                    f"<code>казино [сумма]</code>\n\n"
                                    f"💡 <b>Пример:</b> <code>казино 100</code>\n\n"
                                    f"🌐 <b>Web App:</b> /webapp")
                            
                            elif text_lower == '/help' or text_lower == '/помощь':
                                send_message(chat_id,
                                    f"🆘 <b>ПОМОЩЬ ПО БОТУ</b>\n\n"
                                    f"🎮 <b>Основные команды:</b>\n"
                                    f"• /start - начать работу\n"
                                    f"• /balance - ваш баланс\n"
                                    f"• /bonus - ежедневный бонус\n"
                                    f"• /webapp - открыть Web App\n\n"
                                    f"🎯 <b>Игры:</b>\n"
                                    f"• ограбить казну - ограбление казны\n"
                                    f"• казино [сумма] - игра в казино\n\n"
                                    f"📊 <b>Статистика:</b>\n"
                                    f"• /stats - статистика бота\n\n"
                                    f"🌐 <b>Web App доступен по команде /webapp</b>")
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n🛑 Бот остановлен пользователем")
            save_data()
            api_server.shutdown()
            break
        except Exception as e:
            print(f"❌ Критическая ошибка в основном цикле: {e}")
            time.sleep(5)

# Функции для обработки игр в чате (оставьте свои существующие)
def handle_robbery_in_chat(chat_id, user_id, username):
    """Обработка ограбления в чате"""
    global treasury, last_treasury_update
    
    # Создаем пользователя если не существует
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {
            'username': username,
            'balance': 0,
            'business_level': 0,
            'last_income': 0,
            'robbery_count': 0,
            'last_robbery_date': datetime.now().strftime("%Y-%m-%d"),
            'last_robbery_time': 0,
            'last_daily_bonus': None,
            'last_casino_time': 0,
            'daily_robbery_earnings': 0
        }
        save_data()
    
    user_data = users_data[str(user_id)]
    current_time = time.time()
    
    # Проверяем кулдаун (30 минут)
    if current_time - user_data.get('last_robbery_time', 0) < 1800:
        remaining_time = 1800 - (current_time - user_data['last_robbery_time'])
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        
        send_message(chat_id,
            f"⏰ <b>Ограбление пока невозможно!</b>\n\n"
            f"🕒 <b>До следующей попытки:</b> {minutes} мин {seconds} сек\n"
            f"💡 <b>Попробуйте позже</b>")
        return
    
    # Проверяем дневной лимит (3 ограбления в день)
    today = datetime.now().strftime("%Y-%m-%d")
    if user_data.get('last_robbery_date') != today:
        user_data['robbery_count'] = 0
        user_data['daily_robbery_earnings'] = 0
        user_data['last_robbery_date'] = today
    
    if user_data.get('robbery_count', 0) >= 3:
        send_message(chat_id,
            f"🚫 <b>Достигнут дневной лимит ограблений!</b>\n\n"
            f"📊 <b>Лимит:</b> 3 ограбления в день\n"
            f"💡 <b>Попробуйте завтра</b>")
        return
    
    # Обновляем казну (каждые 2 часа)
    if current_time - last_treasury_update > 7200:
        treasury = random.randint(25, 100)
        last_treasury_update = current_time
        save_data()
    
    # Шанс успеха 90%
    success = random.random() <= 0.9
    
    if success:
        stolen_amount = random.randint(1, min(20, treasury))
        treasury -= stolen_amount
        if treasury < 0:
            treasury = 0
        
        user_data['balance'] = user_data.get('balance', 0) + stolen_amount
        user_data['robbery_count'] = user_data.get('robbery_count', 0) + 1
        user_data['daily_robbery_earnings'] = user_data.get('daily_robbery_earnings', 0) + stolen_amount
        user_data['last_robbery_time'] = current_time
        
        save_data()
        
        send_message(chat_id,
            f"🎯 <b>Ограбление успешно!</b>\n\n"
            f"👤 <b>Грабитель:</b> @{username}\n"
            f"💰 <b>Украдено:</b> {stolen_amount}₽\n"
            f"🏦 <b>Остаток в казне:</b> {treasury}₽\n"
            f"📊 <b>Ограблений сегодня:</b> {user_data['robbery_count']}/3\n"
            f"💎 <b>Ваш баланс:</b> {user_data['balance']}₽")
    else:
        user_data['robbery_count'] = user_data.get('robbery_count', 0) + 1
        user_data['last_robbery_time'] = current_time
        save_data()
        
        send_message(chat_id,
            f"🚨 <b>Ограбление провалилось!</b>\n\n"
            f"👤 <b>Грабитель:</b> @{username}\n"
            f"💂 <b>Охрана поймала вас!</b>\n"
            f"🏦 <b>Казна осталась нетронутой:</b> {treasury}₽\n"
            f"📊 <b>Ограблений сегодня:</b> {user_data['robbery_count']}/3\n\n"
            f"💡 <b>Попробуйте снова через 30 минут</b>")
    
    update_stats_message()

def handle_casino_in_chat(chat_id, user_id, username, amount_text):
    """Игра в казино в чате"""
    try:
        amount = int(amount_text)
        if amount <= 0:
            send_message(chat_id, "❌ <b>Сумма должна быть положительной!</b>")
            return
    except ValueError:
        send_message(chat_id, "❌ <b>Неверная сумма! Используйте: казино [число]</b>")
        return
    
    # Создаем пользователя если не существует
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {
            'username': username,
            'balance': 0,
            'business_level': 0,
            'last_income': 0,
            'robbery_count': 0,
            'last_robbery_date': datetime.now().strftime("%Y-%m-%d"),
            'last_robbery_time': 0,
            'last_daily_bonus': None,
            'last_casino_time': 0,
            'daily_robbery_earnings': 0
        }
        save_data()
    
    user_data = users_data[str(user_id)]
    balance = user_data.get('balance', 0)
    
    if balance < amount:
        send_message(chat_id,
            f"❌ <b>Недостаточно средств!</b>\n\n"
            f"💰 <b>Нужно:</b> {amount}₽\n"
            f"💎 <b>Ваш баланс:</b> {balance}₽")
        return
    
    # Проверяем кулдаун (10 секунд)
    current_time = time.time()
    if current_time - user_data.get('last_casino_time', 0) < 10:
        remaining_time = 10 - (current_time - user_data['last_casino_time'])
        send_message(chat_id,
            f"⏰ <b>Казино пока недоступно!</b>\n\n"
            f"🕒 <b>До следующей попытки:</b> {int(remaining_time)} сек\n"
            f"💡 <b>Подождите немного</b>")
        return
    
    # Обновляем время последней игры
    user_data['last_casino_time'] = current_time
    
    # Шанс выигрыша 30%
    win = random.randint(1, 100) <= 30
    
    if win:
        win_amount = amount * 2
        user_data['balance'] = balance + win_amount
        save_data()
        
        send_message(chat_id,
            f"🎰 <b>ДЖЕКПОТ! ВЫ ВЫИГРАЛИ!</b>\n\n"
            f"👤 <b>Игрок:</b> @{username}\n"
            f"💰 <b>Ставка:</b> {amount}₽\n"
            f"🎯 <b>Выигрыш:</b> {win_amount}₽ (x2)\n"
            f"💎 <b>Ваш баланс:</b> {user_data['balance']}₽\n\n"
            f"🍀 <b>Повезло! Поздравляем с выигрышем!</b>")
    else:
        user_data['balance'] = balance - amount
        save_data()
        
        send_message(chat_id,
            f"🎰 <b>ВЫ ПРОИГРАЛИ!</b>\n\n"
            f"👤 <b>Игрок:</b> @{username}\n"
            f"💰 <b>Ставка:</b> {amount}₽\n"
            f"💸 <b>Потеряно:</b> {amount}₽\n"
            f"💎 <b>Ваш баланс:</b> {user_data['balance']}₽\n\n"
            f"💡 <b>Попробуйте еще раз! Удачи!</b>")
    
    update_stats_message()

if __name__ == '__main__':
    main()
