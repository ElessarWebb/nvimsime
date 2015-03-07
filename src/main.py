from time import sleep

import os
import re
import subprocess
import threading
import neovim
from twisted.internet import reactor, protocol

def which(program):
  def is_exe(fpath):
      return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

  fpath, fname = os.path.split(program)
  if fpath:
      if is_exe(program):
          return program
  else:
      for path in os.environ["PATH"].split(os.pathsep):
          path = path.strip('"')
          exe_file = os.path.join(path, program)
          if is_exe(exe_file):
              return exe_file

  return None

class ScalaProject(object):

  def __init__(self, vim):
    self.vim = vim

  def compile(self):
    self.vim.error("Called compile on abstract ScalaProject")

class SbtProject(ScalaProject):

  def __init__(self, vim, path):
    super(SbtProject, self).__init__(vim)

    # check if sbt is installed
    self.sbt_path = which("sbt")
    if not self.sbt_path:
      self.vim.error("SBT executable not found")

    self.project = path
    self.sbt = Sbt(self.sbt_path, self.project)

  def compile(self):
    print("???")

    # self.sbt.communicate("compile")

class SbtProtocol(protocol.ProcessProtocol):

  def __init__(self, sbt):
    self.sbt = sbt

    # indicates if sbt is waiting for input
    self.lock = threading.Lock()

  def acquire(self):
    print("[INFO] SBT locking...")
    self.lock.acquire()

  def ready(self):
    print("[INFO] SBT ready...")
    self.lock.release()

  def connectionMade(self):
    print("Connection made!")

    # sbt starting up
    self.acquire()

  def outReceived(self, data):
    for line in data.split('\n'):

      # detect sbt ready
      if re.search(r'^\s*>\s*', line):
        self.ready()

  def errReceived(self, data):
    print("err >> %s" % data)

  def processEnded(self, reason):
    reactor.stop()
    self.release()

class Sbt(object):

  def __init__(self, sbt_path, project):
    self.sbt_path = sbt_path
    self.project = project
    self.errbuff = ""
    self.outbuff = {}
    self.buf_lock = threading.Lock()

    # start a background sbt thread
    self.thread = threading.Thread(target=self.run)
    self.thread.daemon = True
    self.thread.start()

    self.cmd_queue = []

  def queue(self, sbtcmd):
    self.cmd_queue.append(sbtcmd)

  def run(self):
    # open sbt subprocess
    reactor.spawnProcess(
      SbtProtocol(self),
      self.sbt_path,
      [self.sbt_path],
      { 'PATH': os.environ['PATH'] },
      self.project,
      usePTY=True
    )
    reactor.run()

class VimBase(object):

  def __init__(self): pass

  def error(self, msg):
    print("Error :: %s" % msg)

  def echo(self, msg):
    print("Echo :: %s" % msg)

  def command(self, cmd):
    print("Cmd :: %s" % cmd)

class Vim(VimBase):

  def __init__(self, vim):
    super(VimBase, self).__init__()

    self.vim = vim

  def error(self, msg):
    raise Exception(msg)

  def echo(self, msg):
    self.command("echo '%s'" % msg)

  def command(self, cmd):
    self.vim.command(cmd)

@neovim.plugin
class Scala(object):
  def __init__(self, vim):
    self.vim = Vim(vim)
    self.project = None

  @neovim.rpc_export('keypress')
  def keypress(self, key):
    self.vim.echo("pressed %s" % key)

  @neovim.command('SbtProject', sync=True, nargs=1)
  def sbt_project(self, args):
    project, = args

    # get an absolute path
    if not len(project) > 0: self.vim.error("Not a valid project directory")
    if project[0] != "/": self.vim.error("Need an absolute path")

    # check if it's a valid directory
    if not os.path.isdir(project): self.vim.error("No such file or directory: %s" % project)

    # check if we can start sbt in the background
    self.project = SbtProject(self.vim, project)
    self.vim.echo("Set scala project to %s" % project)

    return self.project

if __name__ == "__main__":
  scala = Scala(VimBase())
  project = scala.sbt_project(["/home/arjen/repositories/fortress"])

  while True:
    print("in")
    c = raw_input("> ")
    if c == "c":
      print(">> Start background compilation...")
      project.compile()
