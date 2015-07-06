import datetime
import json

from google.appengine.ext import ndb
import webapp2


class Resource(ndb.Model):
    """Contents of a single URL."""
    path = ndb.StringProperty()
    content = ndb.TextProperty()
    content_type = ndb.StringProperty()
    include_last_modified = ndb.BooleanProperty()
    modified_time = ndb.DateTimeProperty()
    expires_seconds = ndb.IntegerProperty()


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
            'content': resource.content,
            'ctype': resource.content_type,
        }
        if resource.include_last_modified:
            resource_data['incdate'] = 'true'
        if resource.expires_seconds != -1:
            resource_data['expires'] = resource.expires_seconds

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(resource_data))

    def post(self):
        resource = self.find_resource()
        if resource is None:
            resource = Resource()

        resource.path = self.request.path[21:]
        resource_data = json.loads(self.request.body)
        resource.content = resource_data['content']
        resource.content_type = resource_data['ctype']
        resource.include_last_modified = resource_data['incdate'] == True
        resource.modified_time = datetime.datetime.now()
        if 'expires' in resource_data:
            resource.expires_seconds = int(resource_data['expires'])
        else:
            resource.expires_seconds = -1

        resource.put()

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write('creating resource %s with contents %s, include last modified? %i' % (
                 resource.path, resource.content, resource.include_last_modified));


class ResourceRenderer(webapp2.RequestHandler):
    def get(self):
        results = Resource.query(Resource.path == self.request.path).fetch(1)
        if len(results) < 1:
            # There was no resource with this path so return a 404.
            self.response.write(
                    '<html><head><title>Not Found</title></head>' +
                    '<body>Not Found</body></html>')
            self.response.headers['Content-Type'] = 'text/html'
            self.response.status = '404 Not Found'
        else:
            resource = results[0]
            self.response.write(resource.content)
            self.response.headers['Content-Type'] = \
                    resource.content_type.encode('ascii', 'ignore')
            self.response.status = '200 OK'
            if resource.include_last_modified:
                # Format the modified time as Mon, 06 Jul 2015 08:47:21 GMT
                self.response.headers['Last-Modified'] = \
                        resource.modified_time.strftime(
                                '%a, %d %b %Y %H:%M:%S GMT')

            if resource.expires_seconds != -1:
                self.response.headers['Expires'] = (datetime.datetime.now() +
                        datetime.timedelta(
                                seconds=resource.expires_seconds)).strftime(
                                        '%a, %d %b %Y %H:%M:%S GMT')


app = webapp2.WSGIApplication([
    ('/content_manager_json.*', ContentJsonManager),
    ('/.*', ResourceRenderer),
], debug=True)
