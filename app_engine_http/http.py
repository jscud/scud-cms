#!/usr/bin/env python
#
#    Copyright (C) 2009 Google Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


__author__ = 'j.s@google.com (Jeff Scudder)'


"""Provides a simple HTTP client to use when testing an App Engine app.

The Client class can be used to make HTTP requests and by default will print
the request and response to the terminal for easy debugging. For example,
try making a request to google.com:

import http
client = http.Client()
resp = client.request('GET', 'http://www.google.com')

The request method will return a Response object which contains the data
returned by the server. 

Some App Engine apps chose to use the Users API and the Client class provides
a ae_google_login method to allow you to obtain an app-specific cookie which
is used by the Users API. 

I've posted a simple Users API demo here:
http://jscudtest.appspot.com/user
Try the above in your web browser.

To allow the Users API to recognize the request from this command line client,
use ae_google_login as follows:

import http
client = http.Client()
client.ae_google_login('jscudtest') # Change to the appID you are signing in to.
resp = client.request('GET', 'http://jscudtest.appspot.com/user')
print resp.body

Some App Engine apps also use HTML forms which are normally used from within
a browser. This simple client supports form posts as well. Try out the
shoutout app in your browser for a form example:
http://shoutout.appspot.com/

To post on the shotouts page using this command line client, use:
import http
client = http.Client()
client.ae_google_login('shoutout')
client.request('POST', 'http://shoutout.appspot.com/',
    form_data={'who': raw_input('From: '),
               'message': raw_input('Message: ')})
"""


import os
import StringIO
import urlparse
import urllib
import httplib
import getpass


class Error(Exception):
  pass


class UnknownSize(Error):
  pass


class ProxyError(Error):
  pass


class BadLogin(Error):
  pass


MIME_BOUNDARY = 'END_OF_PART'


class Client(object):

  def __init__(self, method=None, url=None, url_params=None, headers={},
               form_data=None, mime_type=None, print_traffic=True):
    """Creates a new HTTP client and allows default request values to be set.

    The HTTP request contains several fields and default values can be set
    in the client. The client's default will be used if the parameter is
    not provided in the call to the request method.

    If the print_traffic member is set to True, the data in the HTTP request
    and the server's response will be printed to the command line.
    """
    self.method = method
    self.url = url
    self.url_params = url_params or {}
    self.headers = headers or {}
    self.form_data = form_data or {}
    self.http_client = ProxiedHttpClient()
    self.print_traffic = print_traffic
    self.mime_type = mime_type    

  def request(self, method=None, url=None, url_params=None, headers={},
              form_data=None, mime_type=None):
    """Performs an HTTP request.

    If any of the parameters are left as the default, the value from
    the client object will be used.

    method: str The HTTP verb for this request. Usually one of 'GET', 'POST',
        'PUT' or 'DELETE'.
    url: str The web address being requested. For example, 
        'http://www.google.com/' or 
        'http://www.youtube.com/watch?v=Yu_moia-oVI'
    url_params: dict of strings The query portion of the URL which appears
        after the ?. It is often easier to specify parameters as a dict
        so that you do not need to worry about encoding/escaping special
        characters in the URL. For the YouTube example above, you could specify
        the video ID by setting the url to 'ttp://www.youtube.com/watch' and
        the url_params to {'v', 'Yu_moia-oVI'}.
    headers: dict of strings The HTTP headers to be sent in this request. The
        Content-Length header is calculated for you automatically.
    form_data: dict of strings if you are supplying data for an HTTP form or a
        str if you want to send raw data in the request. If you are sending
        just a str, you should specify a mime_type to tell the server the
        Content-Type of the data.
    mime_type: str The value which should be sent as the Content-Type header. If
        you are sending an HTTP form (using a dict in form_data) you do not
        need to set the mime_type as it defaults to
        'application/x-www-form-urlencoded'

    Returns:
      A Response object containing the full contents of the server's response
      to the HTTP request.
    """
    # For any of the request parameters which are not provided, use the
    # values from the Client object.
    if method is None:
      method = self.method

    if url is None:
      url = self.url

    if headers is None:
      headers = self.headers or {}
    else:
      combined_headers = self.headers.copy()
      combined_headers.update(headers or {})
      headers = combined_headers
    # Specify the accept encoding which is sent by default.
    if 'Accept-Encoding' not in self.headers:
      self.headers['Accept-Encoding'] = 'identity'

    if url_params is None:
      url_params = self.url_params
    else:
      combined_params = self.url_params.copy()
      combined_params.update(url_params or {})
      url_params = combined_params

    if form_data is None:
      form_data = self.form_data
    # Allow a raw str or file to be sent as the data.
    elif not isinstance(form_data, dict):
      form_data = form_data
    # The form_data is a dictionary, treat it as an HTML form post.
    else:
      combined_data = self.form_data.copy()
      combined_data.update(form_data or {})
      form_data = combined_data
    
    if mime_type is None:
      mime_type = self.mime_type

    # Construct the full request URL.
    uri = Uri.parse_uri(url)
    uri.query.update(url_params)

    # Construct the request.
    request = HttpRequest(uri, method, headers)
    if isinstance(form_data, dict):
      # Add form data to the request.
      if mime_type is not None:
        request.add_form_inputs(form_data, mime_type=mime_type)
      else:
        request.add_form_inputs(form_data)
    else:
      request.add_body_part(form_data, mime_type=mime_type)

    if self.print_traffic:
      print '*** Sending request:'
      print '%s %s HTTP/1.1' % (request.method,
                                request.uri._get_relative_path())
      if request.uri.port:
        print 'Host: %s:%s' % (request.uri.host, request.uri.port)
      else:
        print 'Host: %s' % request.uri.host
      for key, value in request.headers.iteritems():
        print '%s: %s' % (key, value)
      print ''
      for part in request._body_parts:
        print part,
      print ''
      print '*** Request end'

    # Perform the request and return the response object.
    resp = self.http_client.request(request)

    response_headers = {}
    for pair in resp.getheaders():
      response_headers[pair[0]] = pair[1]

    response = Response(status=str(resp.status), reason=resp.reason,
                        headers=response_headers, body=resp.read())

    if self.print_traffic:
      print '*** Received response:'
      print 'HTTP/1.1 %s %s' % (response.status, response.reason)
      for key, value in response.headers.iteritems():
        print '%s: %s' % (key, value)
      print ''
      print response.body
      print '*** Response end'

    return response

  def ae_google_login(self, app_id):
    """Used to set the cookie for App Engine's Users API."""
    # Two steps:
    # 1. Get Client Login token
    # 2. Make a request to get a cookie
    # Turn off request printing since the password would be shown on the
    # terminal.
    starting_print_taffic_setting = self.print_traffic
    self.print_traffic = False
    # Step 1, get the client login token using the username and password.
    email = raw_input('Please enter your gmail account: ')
    password = getpass.getpass()
    request_fields = {'Email': email,
                      'Passwd': password,
                      'accountType': 'GOOGLE',
                      'service': 'ah',
                      'source': 'CSSI test client'}
    token_response = self.request(
        'POST', 'https://www.google.com/accounts/ClientLogin',
        form_data=request_fields)
    token = None
    if token_response.status == '200':
      for token_line in token_response.body.split('\n'):
        if token_line.startswith('Auth='):
          token = token_line.split('=')[1]
      if token is None:
        self.print_traffic = starting_print_taffic_setting
        raise BadLogin(
            'Unable to find token in response: %s' % token_response.body)
    else:
      self.print_traffic = starting_print_taffic_setting
      raise BadLogin('%s %s %s' % (
          token_response.status, token_response.reason, token_response.body))

    # Step 2, get the cookie.
    cookie_response = self.request(
        'GET', 'http://%s.appspot.com/_ah/login?auth=%s' % (app_id, token))
    if 'set-cookie' not in cookie_response.headers:
      self.print_traffic = starting_print_taffic_setting
      raise BadLogin('Did not receive Cookie when logging in to %s' % app_id)
    cookie = cookie_response.headers['set-cookie']
    # Set the cookie header to be used in all subsequent requests.
    self.headers['Cookie'] = cookie
    self.print_traffic = starting_print_taffic_setting


class Response(object):

  def __init__(self, status=None, reason=None, headers=None, body=None):
    self.status = status
    self.reason = reason
    self.headers = headers or {}
    self.body = body


class HttpRequest(object):
  """Contains all of the parameters for an HTTP 1.1 request.
 
  The HTTP headers are represented by a dictionary, and it is the
  responsibility of the user to ensure that duplicate field names are combined
  into one header value according to the rules in section 4.2 of RFC 2616.
  """
  method = None
  uri = None
 
  def __init__(self, uri=None, method=None, headers=None):
    """Construct an HTTP request.

    Args:
      uri: The full path or partial path as a Uri object or a string.
      method: The HTTP method for the request, examples include 'GET', 'POST',
              etc.
      headers: dict of strings The HTTP headers to include in the request.
    """
    self.headers = headers or {}
    self._body_parts = []
    if method is not None:
      self.method = method
    if isinstance(uri, (str, unicode)):
      uri = Uri.parse_uri(uri)
    self.uri = uri or Uri()


  def add_body_part(self, data, mime_type, size=None):
    """Adds data to the HTTP request body.
   
    If more than one part is added, this is assumed to be a mime-multipart
    request. This method is designed to create MIME 1.0 requests as specified
    in RFC 1341.

    Args:
      data: str or a file-like object containing a part of the request body.
      mime_type: str The MIME type describing the data
      size: int Required if the data is a file like object. If the data is a
            string, the size is calculated so this parameter is ignored.
    """
    if isinstance(data, str):
      size = len(data)
    if size is None:
      # TODO: support chunked transfer if some of the body is of unknown size.
      raise UnknownSize('Each part of the body must have a known size.')
    if 'Content-Length' in self.headers:
      content_length = int(self.headers['Content-Length'])
    else:
      content_length = 0
    # If this is the first part added to the body, then this is not a multipart
    # request.
    if len(self._body_parts) == 0:
      self.headers['Content-Type'] = mime_type
      content_length = size
      self._body_parts.append(data)
    elif len(self._body_parts) == 1:
      # This is the first member in a mime-multipart request, so change the
      # _body_parts list to indicate a multipart payload.
      self._body_parts.insert(0, 'Media multipart posting')
      boundary_string = '\r\n--%s\r\n' % (MIME_BOUNDARY,)
      content_length += len(boundary_string) + size
      self._body_parts.insert(1, boundary_string)
      content_length += len('Media multipart posting')
      # Put the content type of the first part of the body into the multipart
      # payload.
      original_type_string = 'Content-Type: %s\r\n\r\n' % (
          self.headers['Content-Type'],)
      self._body_parts.insert(2, original_type_string)
      content_length += len(original_type_string)
      boundary_string = '\r\n--%s\r\n' % (MIME_BOUNDARY,)
      self._body_parts.append(boundary_string)
      content_length += len(boundary_string)
      # Change the headers to indicate this is now a mime multipart request.
      self.headers['Content-Type'] = 'multipart/related; boundary="%s"' % (
          MIME_BOUNDARY,)
      self.headers['MIME-version'] = '1.0'
      # Include the mime type of this part.
      type_string = 'Content-Type: %s\r\n\r\n' % (mime_type)
      self._body_parts.append(type_string)
      content_length += len(type_string)
      self._body_parts.append(data)
      ending_boundary_string = '\r\n--%s--' % (MIME_BOUNDARY,)
      self._body_parts.append(ending_boundary_string)
      content_length += len(ending_boundary_string)
    else:
      # This is a mime multipart request.
      boundary_string = '\r\n--%s\r\n' % (MIME_BOUNDARY,)
      self._body_parts.insert(-1, boundary_string)
      content_length += len(boundary_string) + size
      # Include the mime type of this part.
      type_string = 'Content-Type: %s\r\n\r\n' % (mime_type)
      self._body_parts.insert(-1, type_string)
      content_length += len(type_string)
      self._body_parts.insert(-1, data)
    self.headers['Content-Length'] = str(content_length)
  # I could add an "append_to_body_part" method as well.

  AddBodyPart = add_body_part

  def add_form_inputs(self, form_data,
                      mime_type='application/x-www-form-urlencoded'):
    """Form-encodes and adds data to the request body.
    
    Args:
      form_data: dict or sequnce or two member tuples which contains the
                 form keys and values.
      mime_type: str The MIME type of the form data being sent. Defaults
                 to 'application/x-www-form-urlencoded'.
    """
    body = urllib.urlencode(form_data)
    self.add_body_part(body, mime_type)

  AddFormInputs = add_form_inputs

  def _copy(self):
    """Creates a deep copy of this request."""
    copied_uri = Uri(self.uri.scheme, self.uri.host, self.uri.port,
                     self.uri.path, self.uri.query.copy())
    new_request = HttpRequest(uri=copied_uri, method=self.method,
                              headers=self.headers.copy())
    new_request._body_parts = self._body_parts[:]
    return new_request


def _apply_defaults(http_request):
  if http_request.uri.scheme is None:
    if http_request.uri.port == 443:
      http_request.uri.scheme = 'https'
    else:
      http_request.uri.scheme = 'http'


class Uri(object):
  """A URI as used in HTTP 1.1"""
  scheme = None
  host = None
  port = None
  path = None
 
  def __init__(self, scheme=None, host=None, port=None, path=None, query=None):
    """Constructor for a URI.

    Args:
      scheme: str This is usually 'http' or 'https'.
      host: str The host name or IP address of the desired server.
      post: int The server's port number.
      path: str The path of the resource following the host. This begins with
            a /, example: '/calendar/feeds/default/allcalendars/full'
      query: dict of strings The URL query parameters. The keys and values are
             both escaped so this dict should contain the unescaped values.
             For example {'my key': 'val', 'second': '!!!'} will become
             '?my+key=val&second=%21%21%21' which is appended to the path.
    """
    self.query = query or {}
    if scheme is not None:
      self.scheme = scheme
    if host is not None:
      self.host = host
    if port is not None:
      self.port = port
    if path:
      self.path = path
     
  def _get_query_string(self):
    param_pairs = []
    for key, value in self.query.iteritems():
      param_pairs.append('='.join((urllib.quote_plus(key),
          urllib.quote_plus(str(value)))))
    return '&'.join(param_pairs)

  def _get_relative_path(self):
    """Returns the path with the query parameters escaped and appended."""
    param_string = self._get_query_string()
    if self.path is None:
      path = '/'
    else:
      path = self.path
    if param_string:
      return '?'.join([path, param_string])
    else:
      return path
     
  def _to_string(self):
    if self.scheme is None and self.port == 443:
      scheme = 'https'
    elif self.scheme is None:
      scheme = 'http'
    else:
      scheme = self.scheme
    if self.path is None:
      path = '/'
    else:
      path = self.path
    if self.port is None:
      return '%s://%s%s' % (scheme, self.host, self._get_relative_path())
    else:
      return '%s://%s:%s%s' % (scheme, self.host, str(self.port),
                               self._get_relative_path())

  def __str__(self):
    return self._to_string()
     
  def modify_request(self, http_request=None):
    """Sets HTTP request components based on the URI."""
    if http_request is None:
      http_request = HttpRequest()
    if http_request.uri is None:
      http_request.uri = Uri()
    # Determine the correct scheme.
    if self.scheme:
      http_request.uri.scheme = self.scheme
    if self.port:
      http_request.uri.port = self.port
    if self.host:
      http_request.uri.host = self.host
    # Set the relative uri path
    if self.path:
      http_request.uri.path = self.path
    if self.query:
      http_request.uri.query = self.query.copy()
    return http_request

  ModifyRequest = modify_request

  def parse_uri(uri_string):
    """Creates a Uri object which corresponds to the URI string.
 
    This method can accept partial URIs, but it will leave missing
    members of the Uri unset.
    """
    parts = urlparse.urlparse(uri_string)
    uri = Uri()
    if parts[0]:
      uri.scheme = parts[0]
    if parts[1]:
      host_parts = parts[1].split(':')
      if host_parts[0]:
        uri.host = host_parts[0]
      if len(host_parts) > 1:
        uri.port = int(host_parts[1])
    if parts[2]:
      uri.path = parts[2]
    if parts[4]:
      param_pairs = parts[4].split('&')
      for pair in param_pairs:
        pair_parts = pair.split('=')
        if len(pair_parts) > 1:
          uri.query[urllib.unquote_plus(pair_parts[0])] = (
              urllib.unquote_plus(pair_parts[1]))
        elif len(pair_parts) == 1:
          uri.query[urllib.unquote_plus(pair_parts[0])] = None
    return uri

  parse_uri = staticmethod(parse_uri)

  ParseUri = parse_uri


parse_uri = Uri.parse_uri


ParseUri = Uri.parse_uri


class HttpResponse(object):
  status = None
  reason = None
  _body = None
 
  def __init__(self, status=None, reason=None, headers=None, body=None):
    self._headers = headers or {}
    if status is not None:
      self.status = status
    if reason is not None:
      self.reason = reason
    if body is not None:
      if hasattr(body, 'read'):
        self._body = body
      else:
        self._body = StringIO.StringIO(body)
         
  def getheader(self, name, default=None):
    if name in self._headers:
      return self._headers[name]
    else:
      return default

  def getheaders(self):
    return self._headers
   
  def read(self, amt=None):
    if self._body is None:
      return None
    if not amt:
      return self._body.read()
    else:
      return self._body.read(amt)


class HttpClient(object):
  """Performs HTTP requests using httplib."""
  debug = None
 
  def request(self, http_request):
    return self._http_request(http_request.method, http_request.uri, 
                              http_request.headers, http_request._body_parts)

  Request = request

  def _get_connection(self, uri, headers=None):
    """Opens a socket connection to the server to set up an HTTP request.
    
    Args:
      uri: The full URL for the request as a Uri object.
      headers: A dict of string pairs containing the HTTP headers for the
          request.
    """
    connection = None
    if uri.scheme == 'https':
      if not uri.port:
        connection = httplib.HTTPSConnection(uri.host)
      else:
        connection = httplib.HTTPSConnection(uri.host, int(uri.port))
    else:
      if not uri.port:
        connection = httplib.HTTPConnection(uri.host)
      else:
        connection = httplib.HTTPConnection(uri.host, int(uri.port))
    return connection

  def _http_request(self, method, uri, headers=None, body_parts=None):
    """Makes an HTTP request using httplib.
   
    Args:
      method: str example: 'GET', 'POST', 'PUT', 'DELETE', etc.
      uri: str or atom.http_core.Uri
      headers: dict of strings mapping to strings which will be sent as HTTP 
               headers in the request.
      body_parts: list of strings, objects with a read method, or objects
                  which can be converted to strings using str. Each of these
                  will be sent in order as the body of the HTTP request.
    """
    if isinstance(uri, (str, unicode)):
      uri = Uri.parse_uri(uri)
    connection = self._get_connection(uri, headers=headers)
 
    if self.debug:
      connection.debuglevel = 1

    connection.putrequest(method, uri._get_relative_path())

    # Overcome a bug in Python 2.4 and 2.5
    # httplib.HTTPConnection.putrequest adding
    # HTTP request header 'Host: www.google.com:443' instead of
    # 'Host: www.google.com', and thus resulting the error message
    # 'Token invalid - AuthSub token has wrong scope' in the HTTP response.
    if (uri.scheme == 'https' and int(uri.port or 443) == 443 and
        hasattr(connection, '_buffer') and
        isinstance(connection._buffer, list)):
      header_line = 'Host: %s:443' % uri.host
      replacement_header_line = 'Host: %s' % uri.host
      try:
        connection._buffer[connection._buffer.index(header_line)] = (
            replacement_header_line)
      except ValueError:  # header_line missing from connection._buffer
        pass

    # Send the HTTP headers.
    for header_name, value in headers.iteritems():
      connection.putheader(header_name, value)
    connection.endheaders()

    # If there is data, send it in the request.
    if body_parts:
      for part in body_parts:
        _send_data_part(part, connection)

    # Return the HTTP Response from the server.
    return connection.getresponse()


def _send_data_part(data, connection):
  if isinstance(data, (str, unicode)):
    # I might want to just allow str, not unicode.
    connection.send(data)
    return
  # Check to see if data is a file-like object that has a read method.
  elif hasattr(data, 'read'):
    # Read the file and send it a chunk at a time.
    while 1:
      binarydata = data.read(100000)
      if binarydata == '': break
      connection.send(binarydata)
    return
  else:
    # The data object was not a file.
    # Try to convert to a string and send the data.
    connection.send(str(data))
    return


class ProxiedHttpClient(HttpClient):

  def _get_connection(self, uri, headers=None):
    # Check to see if there are proxy settings required for this request.
    proxy = None
    if uri.scheme == 'https':
      proxy = os.environ.get('https_proxy')
    elif uri.scheme == 'http':
      proxy = os.environ.get('http_proxy')
    if not proxy:
      return HttpClient._get_connection(self, uri, headers=headers)
    # Now we have the URL of the appropriate proxy server.
    # Get a username and password for the proxy if required.
    proxy_auth = _get_proxy_auth()
    if uri.scheme == 'https':
      import socket
      if proxy_auth:
        proxy_auth = 'Proxy-authorization: %s' % proxy_auth
      # Construct the proxy connect command.
      port = uri.port
      if not port:
        port = 443
      proxy_connect = 'CONNECT %s:%s HTTP/1.0\r\n' % (uri.host, port)
      # Set the user agent to send to the proxy
      user_agent = ''
      if headers and 'User-Agent' in headers:
        user_agent = 'User-Agent: %s\r\n' % (headers['User-Agent'])
      proxy_pieces = '%s%s%s\r\n' % (proxy_connect, proxy_auth, user_agent)
      # Find the proxy host and port.
      proxy_uri = Uri.parse_uri(proxy)
      if not proxy_uri.port:
        proxy_uri.port = '80'
      # Connect to the proxy server, very simple recv and error checking
      p_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
      p_sock.connect((proxy_url.host, int(proxy_url.port)))
      p_sock.sendall(proxy_pieces)
      response = ''
      # Wait for the full response.
      while response.find("\r\n\r\n") == -1:
        response += p_sock.recv(8192)
      p_status = response.split()[1]
      if p_status != str(200):
        raise ProxyError('Error status=%s' % str(p_status))
      # Trivial setup for ssl socket.
      ssl = socket.ssl(p_sock, None, None)
      fake_sock = httplib.FakeSocket(p_sock, ssl)
      # Initalize httplib and replace with the proxy socket.
      connection = httplib.HTTPConnection(proxy_url.host)
      connection.sock=fake_sock
      return connection
    elif uri.scheme == 'http':
      proxy_url = Uri.parse_uri(proxy)
      if not proxy_url.port:
        proxy_uri.port = '80'
      if proxy_auth:
        headers['Proxy-Authorization'] = proxy_auth.strip()
      return httplib.HTTPConnection(proxy_uri.host, int(proxy_uri.port))
    return None


def _get_proxy_auth():
  import base64
  proxy_username = os.environ.get('proxy-username')
  if not proxy_username:
    proxy_username = os.environ.get('proxy_username')
  proxy_password = os.environ.get('proxy-password')
  if not proxy_password:
    proxy_password = os.environ.get('proxy_password')
  if proxy_username:
    user_auth = base64.b64encode('%s:%s' % (proxy_username,
                                            proxy_password))
    return 'Basic %s\r\n' % (user_auth.strip())
  else:
    return ''
