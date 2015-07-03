import json

from google.appengine.ext import ndb
import webapp2


class Resource(ndb.Model):
    """Contents of a single URL."""
    path = ndb.StringProperty()
    content = ndb.TextProperty()
    content_type = ndb.StringProperty()


class ContentJsonManager(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps({'exmaple': 'value'}))

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(self.request.body)


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, HTTP')

app = webapp2.WSGIApplication([
    ('/content_manager_json', ContentJsonManager),
    ('/.*', MainPage),
], debug=True)
