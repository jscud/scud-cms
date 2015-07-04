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
        resource = Resource()
        # Strip the leading /content_manger_json from the path to get the path
        # of the resource being saved.
        resource.path = self.request.path[21:]
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write('creating resource %s' % resource.path);


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, HTTP')

app = webapp2.WSGIApplication([
    ('/content_manager_json.*', ContentJsonManager),
    ('/.*', MainPage),
], debug=True)
