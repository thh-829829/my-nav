 # 我的导航 — 部署指南
 
 ## 1. 本地运行
 
 ```bash
 pip install flask
 python server.py
 ```
 
 浏览器打开 http://localhost:5000
 
 默认管理密码：`admin123`
 
 ## 2. 部署到 PythonAnywhere（免费，获得公网链接）
 
 ### 第一步：注册账号
 
 打开 https://www.pythonanywhere.com/ ，点击 "Pricing & signup"，选免费的 "Beginner" 方案注册。
 
 ### 第二步：上传代码
 
 登录后进入 Dashboard → Files 选项卡，在根目录下依次上传三个文件：
 - `server.py`
 - `index.html`
 - `requirements.txt`
 
 也可以点 "Upload a file" 逐个上传。
 
 ### 第三步：安装依赖
 
 打开 Dashboard → Consoles → Bash，运行：
 
 ```bash
 pip install flask
 ```
 
 ### 第四步：配置 Web 应用
 
 1. 进入 Dashboard → Web 选项卡
 2. 点击 "Add a new web app"
 3. 选择 "Manual configuration" → Python 3.10（或你看到的版本）
 4. 在 "Code" 部分：
    - Source code: `/home/你的用户名/`
    - Working directory: `/home/你的用户名/`
 5. 在 "WSGI configuration file" 点击链接编辑，内容替换为：
 
 ```python
 import sys
 path = '/home/你的用户名'
 if path not in sys.path:
     sys.path.append(path)
 from server import app as application
 ```
 
 保存后回到 Web 页面顶部，点击 **Reload**。
 
 ### 第五步：修改密码
 
 在 Files 选项卡打开 `server.py`，找到这一行：
 
 ```python
 APP_PASSWORD = 'admin123'
 ```
 
 改成你自己想用的密码，保存。回到 Web 页面点 **Reload**。
 
 ## 3. 访问地址
 
 部署成功后，你的网站地址是：
 ```
 https://你的用户名.pythonanywhere.com
 ```
 
 手机、平板、任何电脑打开这个链接都能访问。
 
 ## 4. 数据管理
 
 - 所有数据存储在 `data.db` 文件中（跟代码在一个目录）
 - 登录后可使用「导出」功能备份为 JSON 文件
 - 也可用「导入」功能恢复之前备份的数据
 - 如需重置数据，直接删除 `data.db` 文件并 Reload 即可重建
 
 ## 5. 注意事项
 
 - 免费版 PythonAnywhere 如果半小时没人访问会自动休眠，再次访问时会慢几秒（唤醒时间）
 - 请不要把 `data.db` 公开分享，里面存了你的密码
 - `APP_PASSWORD` 是登录网站的管理密码，务必改成自己的，不要用默认的 `admin123`
