from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from waitress import serve
from datetime import datetime
import logging
import sqlite3

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(),logging.FileHandler('app.log', encoding='utf-8', mode='a+')])


app = Flask(__name__)
app.secret_key = 'your-secret-key'

# 比对的二维码数据
# VALID_CODES = {"8000814487", "QWE456"} 8000814487|24|4005352645|3010144585||||

def init_db():
    conn = sqlite3.connect('CheckResult.db')
    c = conn.cursor()
    c.execute(''' CREATE TABLE IF NOT EXISTS Users (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT NOT NULL UNIQUE,
                     password TEXT NOT NULL,
                     login_time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS CheckResults
                 (   id INTEGER PRIMARY KEY AUTOINCREMENT,
                     code1 TEXT, 
                     code2 TEXT,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                     result TEXT)''')
    try:
        c.execute("ALTER TABLE CheckResults ADD COLUMN username TEXT")
        conn.commit()
        print("已添加 username 列")
    except sqlite3.OperationalError:  
        # 列已存在
        pass

    # 插入一些测试账户
    c.execute("INSERT OR IGNORE INTO Users (username, password) VALUES ('admin', 'admin')")
    c.execute("INSERT OR IGNORE INTO Users (username, password) VALUES ('1', '1')")
    c.execute("INSERT OR IGNORE INTO Users (username, password) VALUES ('2', '2')")
    c.execute("INSERT OR IGNORE INTO Users (username, password) VALUES ('3', '3')")
    c.execute("INSERT OR IGNORE INTO Users (username, password) VALUES ('4', '4')")
    c.execute("INSERT OR IGNORE INTO Users (username, password) VALUES ('5', '5')")

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# 登录逻辑
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect('CheckResult.db')
    c = conn.cursor()
    c.execute("SELECT password FROM Users WHERE username = ?", (username,))
    result = c.fetchone()
    c.execute("SELECT username, password FROM Users")
    print("查询账号密码:", c.fetchall())
    conn.close()
    
    if result and result[0] == password:
        session['username'] = username
        session['password'] = password
        session['login_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return redirect(url_for('check_page'))
    else:
        flash('用户名或密码错误！', 'error')
        return redirect(url_for('login_page'))


@app.route('/check', methods=['GET'])
def check_page():
    return render_template('check.html')


# 二维码比对逻辑
@app.route('/check', methods=['POST'])
def check():
    try:
        qr_list1 = request.json.get("qr_list1", [])
        qr_list2 = request.json.get("qr_list2", [])
        # code1 = request.json.get("code1", "")
        # code2 = request.json.get("code2", "")
        if qr_list1 == qr_list2:
            ok = True and qr_list1 != [] and qr_list2 != []
        else:
            ok = False

        log_check_result(qr_list1, qr_list2, "有效" if ok else "无效", username=session.get('username'))
        return jsonify({"ok": ok, "msg": "✅ 有效" if ok else "❌ 无效"})
    except Exception as e:
        logging.error(f"比对出错：{str(e)}", exc_info=True)
        return jsonify({"ok": False, "msg": f"❌ 错误： {str(e)}"})

# 查询历史比对记录
@app.route('/history')
def history():
    conn = sqlite3.connect('CheckResult.db')
    c = conn.cursor()
    c.execute("SELECT id, code1, code2, timestamp, username, result FROM CheckResults ORDER BY timestamp DESC")
    records = c.fetchall()
    conn.close()
    # print("查询历史记录:", records)
    return render_template('history.html', records=records)

# 记录比对结果到数据库
def log_check_result(code1, code2, result, username):
    conn = sqlite3.connect('CheckResult.db')
    c = conn.cursor()
    beijing_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print("记录比对结果:", code1, code2, result)
    if isinstance(code1, list):
        code1 = ','.join(code1)
    if isinstance(code2, list):
        code2 = ','.join(code2)
    c.execute("INSERT INTO CheckResults (code1, code2, result, timestamp, username) VALUES (?, ?, ?, ?, ?)", (code1, code2, result, beijing_time, username))
    conn.commit()
    conn.close()

# 获取用户登录状态API
@app.route('/api/user_status', methods=['GET'])
def user_status():
    username = session.get('username')
    if username:
        return jsonify({"status": True, "username": username})
    else:
        return jsonify({"status": False})
# 退出登录
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    session.pop('password', None)
    session.pop('login_time', None)
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    # serve(app, host='0.0.0.0', port=8888)
    app.run(debug=True, host='0.0.0.0', port=8888)
