# Copyright (C) 2008-2009 Jeffrey William Scudder
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
import urllib
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache


__author__ = 'Jeff Scudder (me@jeffscudder.com)'


class Page(db.Model):
  content = db.TextProperty()
  mime_type = db.TextProperty()
  last_updated = db.TextProperty()
  cache_settings = db.TextProperty()


def load_with_cache(request_path):
  """Loads the desired URL from cache, or from the datastore if not in cache.
  
  Args:
    request_path: str The URL under this domain where the content should live. 
  
  Returns:
    A tuple of strings containing 
    (content, mime_type, last_updated, cache_settings) or, None if the desired
    URL does not have an entry in the datastore.
  """
  page = memcache.get(request_path)
  if not page:
    page = Page.get_by_key_name(request_path)
    if page:
      return (page.content, page.mime_type, page.last_updated, 
              page.cache_settings)
  return page


def store_and_cache(resource_path, page_parts):
  """Sets the URL to the desired values and stores in both cache and datastore.
  
  Args:
    resource_path: str The URL under this domain where the content should live.
    page_parts: tuple of strings which contains 
        (content, mime_type, last_updated, cache_settings)
  """
  memcache.set(resource_path, page_parts)
  page = Page.get_by_key_name(resource_path)
  if not page:
    page = Page.get_or_insert(resource_path)
  page.content = page_parts[0]
  page.mime_type = page_parts[1]
  page.last_updated = page_parts[2]
  page.cache_settings = page_parts[3]
  page.put()


class MainPage(webapp.RequestHandler):
  def get(self):
    page_parts = load_with_cache(self.request.path)
    if page_parts:
      self.response.headers['Content-Type'] = page_parts[1] or 'text/html'
      if page_parts[2]:
        self.response.headers['Last-Modified'] = page_parts[2]
      if page_parts[3]:
        self.response.headers['Cache-Control'] = page_parts[3]
      self.response.out.write(page_parts[0])
    else:
      self.error(404)
      self.response.out.write('not found')
      
    
class ContentManager(webapp.RequestHandler):
  def get(self):
    resource_path = self.request.path[len('/content_manager'):]
    path = ''
    content = ''
    mime_type = 'text/html'
    updated = 'Sat, 30 Aug 2008 17:32:55 GMT'
    cache = 'max-age=3600, must-revalidate'
    if resource_path:
      page_parts = load_with_cache(resource_path)
      if page_parts:
        path = resource_path
        content = page_parts[0]
        mime_type = page_parts[1]
        updated = page_parts[2]
        cache = page_parts[3]
    self.response.out.write('<html><body>'
        '<form action="/content_manager" method="post">'
          '<table><tr><td>'
          'Path:</td><td><input type="text" name="path" size="70" value="%s">'
          '</td></tr><tr><td>'
          'Type:</td><td><input type="text" name="type" size="70" value="%s">'
          '</td></tr><tr><td>'
          'Updated:</td><td><input type="text" name="updated" size="70"'
          ' value="%s">'
          '</td></tr><tr><td>'
          'Cache:</td><td><input type="text" name="cache" size="70" '
          'value="%s">'
          '</td></tr></table>'
          'Content:<br/>'
          '<textarea name="content" rows="50" cols="80">%s</textarea><br/>'
          '<input type="submit" value="Set">'
        '</form></body></html>' % (path, mime_type, updated, cache, content))
    
  def post(self):
    resource_path = self.request.get('path')
    if resource_path:
      page_parts = (self.request.get('content'), self.request.get('type'),
                    self.request.get('updated'), self.request.get('cache'))
      store_and_cache(resource_path, page_parts)
      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write(
          'Done, view your updated content at it\'s URL: '
          '<a href="%s">%s</a>' % (resource_path, resource_path))
    else:
      self.response.out.write('bad path')


class ContentLister(webapp.RequestHandler):
  FETCH_LIMIT = 30

  def get(self):
    next = self.request.get('next')
    if next:
      page_keys = db.GqlQuery(
          'SELECT __key__ from Page WHERE __key__ >= :key'
          ' ORDER BY __key__ ASC',
          key=db.Key.from_path('Page', next)).fetch(self.FETCH_LIMIT + 1)

    else:
      page_keys = db.GqlQuery(
          'SELECT __key__ from Page ORDER BY __key__ ASC').fetch(
              self.FETCH_LIMIT + 1)

    count = len(page_keys)
    for i in xrange(count):
      if i < self.FETCH_LIMIT:
        self.response.out.write('page name %s <br/>' % page_keys[i].name())

    if count > self.FETCH_LIMIT:
      self.response.out.write('<a href="/content_lister?next=%s">Next</a>' % (
          urllib.quote(page_keys[self.FETCH_LIMIT].name())))
      
    
application = webapp.WSGIApplication([('/content_manager.*', ContentManager),
                                      ('/content_lister.*', ContentLister), 
                                      ('/.*', MainPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
