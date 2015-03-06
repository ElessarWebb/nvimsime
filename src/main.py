from threading import Thread, Lock
from time import sleep

import os
import subprocess

import neovim

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

    self.base = path

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

  def verify_sbt_installed(self):
    if not which("sbt"):
      self.vim.error("SBT executable not found")

  @neovim.command('SbtProject', sync=True, nargs=1)
  def sbt_project(self, args):
    project, = args

    # get an absolute path
    if not len(project) > 0: self.vim.error("Not a valid project directory")
    if project[0] != "/": self.vim.error("Need an absolute path")

    # check if it's a valid directory
    if not os.path.isdir(project): self.vim.error("No such file or directory: %s" % project)

    # check if sbt is installed
    self.verify_sbt_installed()

    # check if we can start sbt in the background
    self.project = SbtProject(self.vim, project)
    self.vim.echo("Set scala project to %s" % project)

if __name__ == "__main__":
  scala = Scala(VimBase())
  scala.sbt_project(["/home/arjen/repositories/fortress"])
