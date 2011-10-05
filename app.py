# Python imports
import os

# Tornado imports
import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options
from tornado.web import url

# Third-party imports
import pymongo
import yaml

from pymongo.objectid import ObjectId

# App imports
import forms
import uimodules
import util

define("port", default=8888, type=int)
define("config_file", default="app_config.yml", help="app_config file")

# Application class
class Application(tornado.web.Application):
  def __init__(self):
    self.config = self._get_config()
    handlers = [
      url(r'/', IndexHandler, name='index'),
      url(r'/auth/google', GoogleAuthHandler, name='google_auth'),
      url(r'/logout', LogoutHandler, name='logout'),
    ]
    settings = {
      'cookie_secret': self.config.cookie_secret,
      'debug': self.config.debug,
      'login_url': '/auth/login',
      'static_path': os.path.join(os.path.dirname(__file__), 'static'),
      'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
      'ui_modules': uimodules,
      'xsrf_cookies': True,
    }
    tornado.web.Application.__init__(self, handlers, **settings)
    # Connect to mongodb
    self.connection = pymongo.Connection(document_class=util.Struct)
    self.db = self.connection[self.config.mongodb_database]

  def _get_config(self):
    f = file(options.config_file, 'r')
    config = util.Struct(yaml.load(f))
    f.close()
    return config


class BaseHandler(tornado.web.RequestHandler):
  @property
  def db(self):
    return self.application.db

  def get_current_user(self):
    user_id = self.get_secure_cookie('user_id')
    if not user_id:
      return None
    return self.db.users.find_one({'_id': ObjectId(user_id)})


# Handlers

class IndexHandler(BaseHandler):
  def get(self):
    self.write('hello!')


class GoogleAuthHandler(BaseHandler, tornado.auth.GoogleMixin):
  @tornado.web.asynchronous
  def get(self):
    if self.get_argument('openid.mode', None):
      self.get_authenticated_user(self.async_callback(self._on_auth))
      return
    self.authenticate_redirect()

  def _on_auth(self, guser):
    if not guser:
      raise tornado.web.HTTPError(500, "Google auth failed")
    user = self.db.users.find_one({'email': guser['email']})
    if user is None:
      user = {
        'email': guser['email'],
        'name': guser['name'],
      }
      self.db.users.insert(user)
    self.set_secure_cookie('user_id', str(user['_id']))
    # TODO You would probably want to change the reverse url here
    self.redirect(self.get_argument('next', self.reverse_url('index')))


class LogoutHandler(BaseHandler):
  def get(self):
    self.clear_cookie('user_id')
    self.redirect(self.reverse_url('index'))


def main():
  tornado.options.parse_command_line()
  http_server = tornado.httpserver.HTTPServer(Application())
  http_server.listen(options.port)
  tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
  main()
