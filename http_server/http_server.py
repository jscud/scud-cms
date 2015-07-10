import datetime
import json

from google.appengine.ext import ndb
import webapp2


class Header(ndb.Model):
    """Contains a single HTTP header for a resource."""
    name = ndb.StringProperty()
    value = ndb.StringProperty()


class Resource(ndb.Model):
    """Contents of a single URL."""
    path = ndb.StringProperty()
    content = ndb.TextProperty()
    content_type = ndb.StringProperty()
    include_last_modified = ndb.BooleanProperty()
    modified_time = ndb.DateTimeProperty()
    expires_seconds = ndb.IntegerProperty()
    headers = ndb.StructuredProperty(Header, repeated=True)


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
        if resource is not None:
            resource_data = {
                'content': resource.content,
                'ctype': resource.content_type,
                'headers': [],
            }
            if resource.include_last_modified:
                resource_data['incdate'] = 'true'
            if resource.expires_seconds != -1:
                resource_data['expires'] = resource.expires_seconds
            for header in resource.headers:
                resource_data['headers'].append('%s:%s' % (
                        header.name, header.value))
        else:
            resource_data = {}

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
        resource.include_last_modified = 'incdate' in resource_data
        resource.modified_time = datetime.datetime.now()
        if 'expires' in resource_data:
            resource.expires_seconds = int(resource_data['expires'])
        else:
            resource.expires_seconds = -1

        resource.headers = []
        for header_name_value in resource_data['headers']:
            # Headers are sent from the client JS in the form name:value.
            resource.headers.append(Header(
                    name=header_name_value[:header_name_value.index(':')],
                    value=header_name_value[header_name_value.index(':') + 1:]))

        resource.put()

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write('saved resource %s' % (resource.path,))


class ContentLister(webapp2.RequestHandler):
    def get(self):
        """Lists a few resources with pagination."""
        resources = []
        starting_path = self.request.get('start')
        if starting_path:
            resources = Resource.query(Resource.path >= starting_path).order(
                    Resource.path).fetch(11)
        else:
            resources = Resource.query().order(Resource.path).fetch(11)

        self.response.headers['Content-Type'] = 'text/html'

        self.response.write('<!doctype><html><head>' +
                '<title>Content Lister</title></head><body>Resources:<br>')
        for i in xrange(10):
            if i < len(resources):
                self.response.write('%s ' % (resources[i].path,) +
                        '<a href="/content_manager%s">' % (
                                resources[i].path,) +
                        'Edit</a> <a href="%s">View</a><br>' % (
                                resources[i].path,))

        if len(resources) > 10:
            self.response.write(
                    '<a href="/content_lister?start=%s">Next</a>' % (
                            resources[10].path,))
        
        self.response.write('</body></html>')

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

            for header in resource.headers:
                self.response.headers[
                        header.name.encode('ascii', 'ignore')] = \
                                header.value.encode('ascii', 'ignore')


app = webapp2.WSGIApplication([
    ('/content_manager_json.*', ContentJsonManager),
    ('/content_lister.*', ContentLister),
    ('/.*', ResourceRenderer),
], debug=True)
