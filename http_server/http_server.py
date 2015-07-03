from google.appengine.ext import ndb
import webapp2

class Resource(ndb.Model):
    """Contents of a single URL."""
    path = ndb.StringProperty()
    content = ndb.TextProperty()
    content_type = ndb.StringProperty()


class ResourceRenderer(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, HTTP')

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, HTTP')

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
