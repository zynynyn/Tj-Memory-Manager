# README

## 环境配置

​	本项目所需依赖为：`` Flask``、`` PyQt5==5.15.4``以及`` gunicorn``，python版本为`` 3.9 ``若已经有了可以跳过创建虚拟环境。

1. 创建虚拟环境并激活

   ```bash
   conda create -n memmanager python=3.9
   conda activate memmanager
   ```

2. 配置依赖项

   ```bash
   pip install -r 'your/path/to/requirements.txt'



## 本地运行

​	在Visual Studio Code中打开并运行`` app.py``，在显示的网页(一般为``localhost:5000``)查看即可，成功后显示：

```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
```



