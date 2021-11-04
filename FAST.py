import sys, os
from subprocess import call, check_output

try:
    if sys.version[0] == '2':
        try:
            print('Python 2 is default interpreter...going to try Python 3')
            py_check = check_output('where python').split('\r\n')
            py3_intepreter = ''.join([i for i in py_check if 'miniforge' in i])
            the_call = py3_intepreter + ' ' + sys.argv[0]
            call(the_call)
        except Exception as e:
            print(e)
    else:
        from src.manage import Manage
    
        if __name__=='__main__':
            manage = Manage()
            app_path = 'gui_program.py'
            try:
                manage.checkForUpdates()
                manage.startApp(app_path)
            except Exception as e:
                print(e)

except Exception as e:
    print(e)