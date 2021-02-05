from src.manage import Manage

if __name__=='__main__':
    manage = Manage()
    app_path = 'Python_env/gui_process.py'
    update_path = 'src/update.py'
    manage.startApp(app_path, update_path)