#! /usr/bin/env python3
import os
import sys
import inspect
import datetime

class debugger_class:
    '''Creates a log folder in present dir, Takes 1st argument as verbose = True/ False , 2nd filename'''
    verbose_control = False
    use_debugger=False
    read = ""
    filename=""
    cmd="Generated_By_Debugger_own : RishabhDubey "
    bad_chars = [ '~' , '`' , '!' , '@' , '#' , '$' , '%' , '^' , '&' ,
                  '*' , '(' , ')' , '_' , '+' , '-' , '=' , '{' , '}' ,
                  '[' , ']' , '|' , ":" , ';' , "'" , ',' , '<' ,
                  '>' , ',' , '.' , '?' , '/']
    
    def __init__(self , use_debugger = True,verbose_control = False , create_dir = True , filename = "log_file"):
        self.use_debugger = use_debugger
        self.verbose_control = verbose_control
        if (self.verbose_control):
            print("\n\n VERBOSE MODE ON \n\n")
        self.filename=filename
        if (create_dir):
            self.run_cmd("rm -rf logs")
            self.run_cmd("mkdir logs")
        self.run_cmd("touch ./logs/"+str(self.filename))
        init_cmd = "echo " + "'This is a log file '" + self.filename + "> ./logs/" + self.filename
        self.run_cmd( init_cmd )
        init_cmd = "echo " + "'Path '" + sys.argv[0] + ">> ./logs/" + self.filename
        self.run_cmd( init_cmd )
        init_cmd = "echo " + "'    '" + ">> ./logs/" + self.filename
        self.run_cmd( init_cmd )
        init_cmd = "echo " + "'__FucntionName__  LOGS  '"  + ">> ./logs/" + self.filename
        self.run_cmd( init_cmd )
        init_cmd = "echo " + "'    '" + ">> ./logs/" + self.filename
        self.run_cmd( init_cmd )
        self.log( "debuggerClass init " , self.cmd)
        init_cmd = "echo " + "'    '" + ">> ./logs/" + self.filename
        self.run_cmd( init_cmd )

    def run_cmd (self ,string):
        if (self.use_debugger == False):
            return
        try: 
            stream = os.popen(string)
            self.read = stream.read()
        except OSError as error:
            print(error)
            
    def verbose(self , string):
        if (self.verbose_control):
            print(string)

    def log (self , function , string ):
        # ct stores current time 
        if (self.use_debugger == False):
            return
        current_time = datetime.datetime.now()
        self.cmd = " __ " + str(function) + " __  : " +string 
        self.verbose(self.cmd)
        self.cmd = self.cmd + str(current_time)
        self.cmd +=  " >> ./logs/"+self.filename
        self.cmd = "echo " + self.cmd
        self.cmd = self.remove_slash_n(self.cmd)
        self.run_cmd(self.cmd)
    
    def function_name(self):
        function_name = inspect.stack()[1][3]
        function_name = self.remove_bad_chars(function_name)
        return str(function_name)

    def remove_bad_chars(self , string):
        string = ''.join((filter(lambda i: i not in self.bad_chars, string)))
        return str(string)
    
    def remove_slash_n(self , string):
        string = ''.join((filter(lambda i: i not in '\n', string)))
        return str(string)
