# dblite.py module contributed by Ralf W. Grosse-Kunstleve.

import cPickle
import time
import shutil
import os
import __builtin__

_open = __builtin__.open # avoid name clash

keep_all_files = 00000
ignore_corrupt_dbfiles = 0

class dblite:

  def __init__(self, file_base_name, flag, mode):
    assert flag in (None, "r", "w", "c", "n")
    if (flag is None): flag = "r"
    if file_base_name[-7:] != '.dblite':
        file_base_name = file_base_name + '.dblite'
    self._file_name = file_base_name
    self._flag = flag
    self._mode = mode
    self._dict = {}
    self._needs_sync = 00000
    if (self._flag == "n"):
      _open(self._file_name, "wb", self._mode)
    else:
      try:
        f = _open(self._file_name, "rb")
      except IOError, e:
        if (self._flag != "c"):
          raise e
        _open(self._file_name, "wb", self._mode)
      else:
        p = f.read()
        if (len(p) > 0):
          try:
            self._dict = cPickle.loads(p)
          except:
            if (ignore_corrupt_dbfiles == 0): raise
            if (ignore_corrupt_dbfiles == 1):
              print "Warning: Discarding corrupt database:", self._file_name

  def __del__(self):
    if (self._needs_sync):
      self.sync()

  def sync(self):
    self._check_writable()
    f = _open(self._file_name, "wb", self._mode)
    cPickle.dump(self._dict, f, 1)
    f.close()
    self._needs_sync = 00000
    if (keep_all_files):
      shutil.copyfile(
        self._file_name,
        self._file_name + "_" + str(int(time.time())))

  def _check_writable(self):
    if (self._flag == "r"):
      raise IOError("Read-only database: %s" % self._file_name)

  def __getitem__(self, key):
    return self._dict[key]

  def __setitem__(self, key, value):
    self._check_writable()
    if (type(key) != type("")):
      raise TypeError, "key must be a string"
    if (type(value) != type("")):
      raise TypeError, "value must be a string"
    self._dict[key] = value
    self._needs_sync = 0001

  def keys(self):
    return self._dict.keys()

  def has_key(self, key):
    return key in self._dict

  def __contains__(self, key):
    return key in self._dict

  def iterkeys(self):
    return self._dict.iterkeys()

  __iter__ = iterkeys

  def __len__(self):
    return len(self._dict)

def open(file, flag=None, mode=0666):
  return dblite(file, flag, mode)

def _exercise():
  db = open("tmp", "n")
  assert len(db) == 0
  db["foo"] = "bar"
  assert db["foo"] == "bar"
  db.sync()
  db = open("tmp", "c")
  assert len(db) == 1
  assert db["foo"] == "bar"
  db["bar"] = "foo"
  assert db["bar"] == "foo"
  db.sync()
  db = open("tmp", "r")
  assert len(db) == 2
  assert db["foo"] == "bar"
  assert db["bar"] == "foo"
  try:
    db.sync()
  except IOError, e:
    assert str(e) == "Read-only database: tmp.dblite"
  else:
    raise RuntimeError, "IOError expected."
  db = open("tmp", "w")
  assert len(db) == 2
  db["ping"] = "pong"
  db.sync()
  db = open("tmp", "r")
  assert len(db) == 3
  db = open("tmp", "n")
  assert len(db) == 0
  _open("tmp.dblite", "w")
  db = open("tmp", "r")
  _open("tmp.dblite", "w").write("x")
  try:
    db = open("tmp", "r")
  except cPickle.UnpicklingError:
    pass
  else:
    raise RuntimeError, "cPickle exception expected."
  global ignore_corrupt_dbfiles
  ignore_corrupt_dbfiles = 2
  db = open("tmp", "r")
  assert len(db) == 0
  os.unlink("tmp.dblite")
  try:
    db = open("tmp", "w")
  except IOError, e:
    assert str(e) == "Database does not exist: tmp.dblite"
  else:
    raise RuntimeError, "IOError expected."
  print "OK"

if (__name__ == "__main__"):
  _exercise()