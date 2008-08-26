# Copyright (C) 2008 Jeffrey William Scudder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache


__author__ = 'Jeff Scudder (me@jeffscudder.com)'


class Page(db.Model):
  content = db.TextProperty()
  mime_type = db.TextProperty()
  last_updated = db.TextProperty()
  cache_settings = db.TextProperty()


def load_with_cache(request_path):
  pass


def store_and_cache(request_path, values):
  pass


class MainPage(webapp.RequestHandler):
  def get(self):
    path = self.request.path
    page = Page.get_by_key_name(path)
    if page:
      self.response.headers['Content-Type'] = page.mime_type or 'text/html'
      if page.last_updated:
        self.response.headers['Last-Modified'] = page.last_updated
      if page.cache_settings:
        self.response.headers['Cache-Control'] = page.cache_settings
      self.response.out.write(page.content)
    else:
      self.error(404)
      self.response.out.write('not found')
      
    
class ContentManager(webapp.RequestHandler):
  def get(self):
    resource_path = self.request.path[len('/content_manager'):]
    path = ''
    content = ''
    mime_type = 'text/html'
    updated = 'Mon, 25 Aug 2008 19:32:55 GMT'
    cache = 'max-age=3600, must-revalidate'
    if resource_path:
      page = Page.get_by_key_name(resource_path)
      if page:
        path = resource_path
        content = page.content
        mime_type = page.mime_type
        updated = page.last_updated
        cache = page.cache_settings
    self.response.out.write('<html><body>'
        '<form action="/content_manager" method="post">'
          'Path: <input type="text" name="path" size="100" value="%s"><br/>'
          'Type: <input type="text" name="type" value="%s"><br/>'
          'Updated: <input type="text" name="updated" value="%s"><br/>'
          'Cache: <input type="text" name="cache" value="%s"><br/>'
          'Content:<br/>'
          '<textarea name="content" rows="50" cols="80">%s</textarea><br/>'
          '<input type="submit" value="Set">'
        '</form></body></html>' % (path, mime_type, updated, cache, content))
    
  def post(self):
    resource_path = self.request.get('path')
    if resource_path:
      edited_page = Page.get_or_insert(resource_path)
      edited_page.content = self.request.get('content')
      if self.request.get('type'):
        edited_page.mime_type = self.request.get('type')
      if self.request.get('updated'):
        edited_page.last_updated = self.request.get('updated')
      if self.request.get('cache'):
        edited_page.cache_settings = self.request.get('cache')
      edited_page.put()
      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write(
          'Done, view your <a href="%s">updated content</a>' % resource_path)
    else:
      self.response.out.write('bad path')
      
    
application = webapp.WSGIApplication([('/content_manager.*', ContentManager),
                                      ('/.*', MainPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
