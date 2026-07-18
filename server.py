# -*- coding: utf-8 -*-
"""
我的导航 - Flask 后端
提供 REST API + 静态文件服务 + 密码认证
部署前请修改 APP_PASSWORD 为你自己的密码
"""
import json
import sqlite3
import os
from functools import wraps
from flask import Flask, request, session, jsonify, g, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'data.db')

app = Flask(__name__)
app.secret_key = 'my-nav-change-this-secret-key-2024'
APP_PASSWORD = 'admin123'  # ← 部署前务必改成你自己的密码！


def get_db():
   if 'db' not in g:
       g.db = sqlite3.connect(DATABASE)
       g.db.row_factory = sqlite3.Row
       g.db.execute("PRAGMA foreign_keys = ON")
   return g.db


@app.teardown_appcontext
def close_db(exception):
   db = g.pop('db', None)
   if db is not None:
       db.close()


def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT NOT NULL,
            site_url TEXT DEFAULT '',
            username TEXT DEFAULT '',
            password TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    ''')
    db.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
    # 初次启动时写入默认密码到配置表
    if not db.execute("SELECT value FROM config WHERE key='password'").fetchone():
        db.execute("INSERT INTO config (key, value) VALUES ('password', ?)", (APP_PASSWORD,))
    count = db.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
    if count == 0:
        defaults = ['AI学习', 'AI工具', '工作', '追剧', '邮箱']
        for i, name in enumerate(defaults):
            db.execute('INSERT INTO categories (name, sort_order) VALUES (?, ?)', (name, i))
    db.commit()


def login_required(f):
   @wraps(f)
   def decorated(*args, **kwargs):
       if not session.get('logged_in'):
           return jsonify({'error': '请先登录'}), 401
       return f(*args, **kwargs)
   return decorated


@app.route('/api/login', methods=['POST'])
def api_login():
   data = request.get_json()
   if data and data.get('password'):
       db = get_db()
       row = db.execute("SELECT value FROM config WHERE key='password'").fetchone()
       stored_pwd = row['value'] if row else APP_PASSWORD
       if data['password'] == stored_pwd:
           session['logged_in'] = True
           return jsonify({'ok': True})
   return jsonify({'error': '密码错误'}), 401


@app.route('/api/logout', methods=['POST'])
def api_logout():
   session.pop('logged_in', None)
   return jsonify({'ok': True})


@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
   data = request.get_json()
   if not data:
       return jsonify({'error': '参数不完整'}), 400
   old_pwd = data.get('old_password', '')
   new_pwd = data.get('new_password', '')
   if not old_pwd or not new_pwd:
       return jsonify({'error': '参数不完整'}), 400
   if len(new_pwd) < 4:
       return jsonify({'error': '新密码至少4位'}), 400
   db = get_db()
   row = db.execute("SELECT value FROM config WHERE key='password'").fetchone()
   stored_pwd = row['value'] if row else APP_PASSWORD
   if old_pwd != stored_pwd:
       return jsonify({'error': '旧密码错误'}), 403
   db.execute("UPDATE config SET value = ? WHERE key = 'password'", (new_pwd,))
   db.commit()
   session.pop('logged_in', None)
   return jsonify({'ok': True, 'message': '密码已修改，请重新登录'})


@app.route('/api/check')
def api_check():
   return jsonify({'logged_in': session.get('logged_in', False)})


@app.route('/api/categories')
def api_get_categories():
   db = get_db()
   rows = db.execute('SELECT * FROM categories ORDER BY sort_order').fetchall()
   result = []
   for row in rows:
       bms = db.execute('SELECT * FROM bookmarks WHERE category_id = ? ORDER BY sort_order', (row['id'],)).fetchall()
       result.append({
           'id': row['id'],
           'name': row['name'],
           'bookmarks': [dict(b) for b in bms]
       })
   return jsonify(result)


@app.route('/api/categories', methods=['POST'])
@login_required
def api_add_category():
   data = request.get_json()
   name = (data or {}).get('name', '').strip()
   if not name:
       return jsonify({'error': '分类名称不能为空'}), 400
   db = get_db()
   cur = db.execute('INSERT INTO categories (name) VALUES (?)', (name,))
   db.commit()
   return jsonify({'id': cur.lastrowid, 'name': name})


@app.route('/api/categories/<int:cat_id>', methods=['PUT'])
@login_required
def api_update_category(cat_id):
   data = request.get_json()
   name = (data or {}).get('name', '').strip()
   if not name:
       return jsonify({'error': '分类名称不能为空'}), 400
   db = get_db()
   db.execute('UPDATE categories SET name = ? WHERE id = ?', (name, cat_id))
   db.commit()
   return jsonify({'ok': True})


@app.route('/api/categories/<int:cat_id>', methods=['DELETE'])
@login_required
def api_delete_category(cat_id):
   db = get_db()
   db.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
   db.commit()
   return jsonify({'ok': True})


@app.route('/api/bookmarks', methods=['POST'])
@login_required
def api_add_bookmark():
   data = request.get_json() or {}
   name = data.get('name', '').strip()
   url = data.get('url', '').strip()
   if not name or not url:
       return jsonify({'error': '名称和链接不能为空'}), 400
   db = get_db()
   cur = db.execute('INSERT INTO bookmarks (category_id, name, url) VALUES (?, ?, ?)',
                    (data['category_id'], name, url))
   db.commit()
   return jsonify({'id': cur.lastrowid, 'name': name, 'url': url})


@app.route('/api/bookmarks/<int:bm_id>', methods=['PUT'])
@login_required
def api_update_bookmark(bm_id):
   data = request.get_json() or {}
   db = get_db()
   db.execute('UPDATE bookmarks SET name = ?, url = ? WHERE id = ?',
              (data.get('name', ''), data.get('url', ''), bm_id))
   db.commit()
   return jsonify({'ok': True})


@app.route('/api/bookmarks/<int:bm_id>', methods=['DELETE'])
@login_required
def api_delete_bookmark(bm_id):
   db = get_db()
   db.execute('DELETE FROM bookmarks WHERE id = ?', (bm_id,))
   db.commit()
   return jsonify({'ok': True})


@app.route('/api/credentials')
def api_get_credentials():
   db = get_db()
   rows = db.execute('SELECT * FROM credentials ORDER BY created_at DESC').fetchall()
   is_logged_in = session.get('logged_in', False)
   result = []
   for row in rows:
       item = dict(row)
       if not is_logged_in:
           pwd = item.get('password', '')
           item['password'] = '\u25cf' * len(pwd) if pwd else ''
       result.append(item)
   return jsonify(result)


@app.route('/api/credentials', methods=['POST'])
@login_required
def api_add_credential():
   data = request.get_json() or {}
   site_name = data.get('site_name', '').strip()
   if not site_name:
       return jsonify({'error': '网站名称不能为空'}), 400
   db = get_db()
   cur = db.execute(
       'INSERT INTO credentials (site_name, site_url, username, password, notes) VALUES (?, ?, ?, ?, ?)',
       (site_name, data.get('site_url', ''), data.get('username', ''),
        data.get('password', ''), data.get('notes', ''))
   )
   db.commit()
   return jsonify({'id': cur.lastrowid})


@app.route('/api/credentials/<int:cred_id>', methods=['PUT'])
@login_required
def api_update_credential(cred_id):
   data = request.get_json() or {}
   db = get_db()
   db.execute(
       'UPDATE credentials SET site_name=?, site_url=?, username=?, password=?, notes=? WHERE id=?',
       (data.get('site_name', ''), data.get('site_url', ''),
        data.get('username', ''), data.get('password', ''),
        data.get('notes', ''), cred_id)
   )
   db.commit()
   return jsonify({'ok': True})


@app.route('/api/credentials/<int:cred_id>', methods=['DELETE'])
@login_required
def api_delete_credential(cred_id):
   db = get_db()
   db.execute('DELETE FROM credentials WHERE id = ?', (cred_id,))
   db.commit()
   return jsonify({'ok': True})


@app.route('/api/export')
@login_required
def api_export():
   db = get_db()
   data = {
       'categories': [dict(r) for r in db.execute('SELECT * FROM categories ORDER BY sort_order').fetchall()],
       'bookmarks': [dict(r) for r in db.execute('SELECT * FROM bookmarks ORDER BY sort_order').fetchall()],
       'credentials': [dict(r) for r in db.execute('SELECT * FROM credentials ORDER BY created_at').fetchall()],
   }
   return jsonify(data)


@app.route('/api/import', methods=['POST'])
@login_required
def api_import():
   data = request.get_json()
   if not data:
       return jsonify({'error': '数据无效'}), 400
   db = get_db()
   db.execute('DELETE FROM bookmarks')
   db.execute('DELETE FROM categories')
   db.execute('DELETE FROM credentials')
   for cat in data.get('categories', []):
       db.execute('INSERT INTO categories (id, name, sort_order) VALUES (?, ?, ?)',
                  (cat['id'], cat['name'], cat.get('sort_order', 0)))
   for bm in data.get('bookmarks', []):
       db.execute('INSERT INTO bookmarks (id, category_id, name, url, sort_order) VALUES (?, ?, ?, ?, ?)',
                  (bm['id'], bm['category_id'], bm['name'], bm['url'], bm.get('sort_order', 0)))
   for cr in data.get('credentials', []):
       db.execute(
           'INSERT INTO credentials (id, site_name, site_url, username, password, notes) VALUES (?, ?, ?, ?, ?, ?)',
           (cr['id'], cr['site_name'], cr.get('site_url', ''),
            cr.get('username', ''), cr.get('password', ''), cr.get('notes', ''))
       )
   db.commit()
   return jsonify({'ok': True})


@app.route('/')
def index():
   return send_from_directory(BASE_DIR, 'index.html')


if __name__ == '__main__':
   with app.app_context():
       init_db()
   print('启动成功！访问 http://localhost:5000')
   app.run(debug=True, host='0.0.0.0', port=5000)
