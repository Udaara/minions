from fabric.api import run, env

def taskA():
   run('ls')

def taskB():
   run('whoami')
