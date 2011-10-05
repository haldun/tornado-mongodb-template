import copy
import datetime
import hashlib
import os

class Struct(dict):
  """Like dict but does not whine for non-existent attributes"""
  def __getattr__(self, name):
    if name == 'id':
      name = '_id'
    try:
      return self[name]
    except KeyError:
      return None

  def __setattr__(self, name, value):
    if name == 'id':
      name = '_id'
    self[name] = value

def md5(s):
  return hashlib.md5(s).hexdigest()

def generate_token(length=32):
  return os.urandom(length).encode('hex')

# Datetime utils
def daterange(start_date, end_date):
  for n in range((end_date - start_date).days + 1):
    yield start_date + datetime.timedelta(n)

def hours(date):
  for n in range(0, 24):
    yield date + datetime.timedelta(hours=n)

def start_of_day(date):
  return datetime.datetime(*date.timetuple()[0:3])

def start_of_tomorrow(date):
  return start_of_day(date + datetime.timedelta(days=1))

def start_of_hour(date):
  return datetime.datetime(*date.timetuple()[0:4])

def start_of_month(date):
  return datetime.datetime(*list(date.timetuple()[:2]) + [1])

def last_day_of_month(date):
  date = start_of_month(date)
  if date.month == 12:
    return date.replace(day=31)
  return date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)

def start_of_next_month(date):
  return last_day_of_month(date) + datetime.timedelta(days=1)


# Copied from django with some modifications
class MultiValueDict(dict):
  """
  A subclass of dictionary customized to handle multiple values for the
  same key.

  >>> d = MultiValueDict({'name': ['Adrian', 'Simon'], 'position': ['Developer']})
  >>> d['name']
  'Simon'
  >>> d.getlist('name')
  ['Adrian', 'Simon']
  >>> d.get('lastname', 'nonexistent')
  'nonexistent'
  >>> d.setlist('lastname', ['Holovaty', 'Willison'])

  This class exists to solve the irritating problem raised by cgi.parse_qs,
  which returns a list for every key, even though most Web forms submit
  single name-value pairs.
  """
  def __init__(self, key_to_list_mapping=()):
    super(MultiValueDict, self).__init__(key_to_list_mapping)

  def __repr__(self):
    return "<%s: %s>" % (self.__class__.__name__,
               super(MultiValueDict, self).__repr__())

  def __getitem__(self, key):
    """
    Returns the last data value for this key, or [] if it's an empty list;
    raises KeyError if not found.
    """
    try:
      list_ = super(MultiValueDict, self).__getitem__(key)
    except KeyError:
      raise MultiValueDictKeyError("Key %r not found in %r" % (key, self))
    try:
      return list_[-1]
    except IndexError:
      return []

  def __setitem__(self, key, value):
    super(MultiValueDict, self).__setitem__(key, [value])

  def __copy__(self):
    return self.__class__([
      (k, v[:])
      for k, v in self.lists()
    ])

  def __deepcopy__(self, memo=None):
    if memo is None:
      memo = {}
    result = self.__class__()
    memo[id(self)] = result
    for key, value in dict.items(self):
      dict.__setitem__(result, copy.deepcopy(key, memo),
               copy.deepcopy(value, memo))
    return result

  def __getstate__(self):
    obj_dict = self.__dict__.copy()
    obj_dict['_data'] = dict([(k, self.getlist(k)) for k in self])
    return obj_dict

  def __setstate__(self, obj_dict):
    data = obj_dict.pop('_data', {})
    for k, v in data.items():
      self.setlist(k, v)
    self.__dict__.update(obj_dict)

  def get(self, key, default=None):
    """
    Returns the last data value for the passed key. If key doesn't exist
    or value is an empty list, then default is returned.
    """
    try:
      val = self[key]
    except KeyError:
      return default
    if val == []:
      return default
    return val

  def getlist(self, key):
    """
    Returns the list of values for the passed key. If key doesn't exist,
    then an empty list is returned.
    """
    try:
      return super(MultiValueDict, self).__getitem__(key)
    except KeyError:
      return []

  def setlist(self, key, list_):
    super(MultiValueDict, self).__setitem__(key, list_)

  def setdefault(self, key, default=None):
    if key not in self:
      self[key] = default
    return self[key]

  def setlistdefault(self, key, default_list=()):
    if key not in self:
      self.setlist(key, default_list)
    return self.getlist(key)

  def appendlist(self, key, value):
    """Appends an item to the internal list associated with key."""
    self.setlistdefault(key, [])
    super(MultiValueDict, self).__setitem__(key, self.getlist(key) + [value])

  def items(self):
    """
    Returns a list of (key, value) pairs, where value is the last item in
    the list associated with the key.
    """
    return [(key, self[key]) for key in self.keys()]

  def iteritems(self):
    """
    Yields (key, value) pairs, where value is the last item in the list
    associated with the key.
    """
    for key in self.keys():
      yield (key, self[key])

  def lists(self):
    """Returns a list of (key, list) pairs."""
    return super(MultiValueDict, self).items()

  def iterlists(self):
    """Yields (key, list) pairs."""
    return super(MultiValueDict, self).iteritems()

  def values(self):
    """Returns a list of the last value on every key list."""
    return [self[key] for key in self.keys()]

  def itervalues(self):
    """Yield the last value on every key list."""
    for key in self.iterkeys():
      yield self[key]

  def copy(self):
    """Returns a shallow copy of this object."""
    return copy(self)

  def update(self, *args, **kwargs):
    """
    update() extends rather than replaces existing key lists.
    Also accepts keyword args.
    """
    if len(args) > 1:
      raise TypeError("update expected at most 1 arguments, got %d" % len(args))
    if args:
      other_dict = args[0]
      if isinstance(other_dict, MultiValueDict):
        for key, value_list in other_dict.lists():
          self.setlistdefault(key, []).extend(value_list)
      else:
        try:
          for key, value in other_dict.items():
            self.setlistdefault(key, []).append(value)
        except TypeError:
          raise ValueError("MultiValueDict.update() takes either a MultiValueDict or dictionary")
    for key, value in kwargs.iteritems():
      self.setlistdefault(key, []).append(value)

