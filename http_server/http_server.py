import json

from google.appengine.ext import ndb
import webapp2


class Resource(ndb.Model):
    """Contents of a single URL."""
    path = ndb.StringProperty()
    content = ndb.TextProperty()
    content_type = ndb.StringProperty()


class ContentJsonManager(webapp2.RequestHandler):
    def find_resource(self):
        # Strip the leading /content_manger_json from the path to get the path
        # of the resource being saved.
        resource_path = self.request.path[21:]
        results = Resource.query(Resource.path == resource_path).fetch(1)
        # TODO: could return a tuple of result, path to avoid recalculating
        # the path when creating a new resource.
        if len(results) > 0:
            return results[0]
        return None

    def get(self):
        resource = self.find_resource()
        resource_data = {
            'content': resource.content
        }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(resource_data))

    def post(self):
        resource = self.find_resource()
        if resource is None:
            resource = Resource()

        resource.path = self.request.path[21:]
        resource_data = json.loads(self.request.body)
        resource.content = resource_data['content']
        resource.put()

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write('creating resource %s with contents %s' % (
                 resource.path, resource.content));


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, HTTP')

app = webapp2.WSGIApplication([
    ('/content_manager_json.*', ContentJsonManager),
    ('/.*', MainPage),
], debug=True)
