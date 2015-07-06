
function httpRequest(httpVerb, data, url, headers, handler) {
  var http = null;
  if (window.XMLHttpRequest) {
    http = new XMLHttpRequest();
  } else if (window.ActiveXObject) {
    http = new ActiveXObject('Microsoft.XMLHTTP');
  }
  if (http) {
    http.open(httpVerb, url, true);
    http.onreadystatechange = function() {
      if (http.readyState == 4) {
        handler(http);
      }
    };
    var propery = null;
    for (property in headers) {
      http.setRequestHeader(property, headers[property]);
    }
    http.send(data);
  } else {
    throw new Error('Unable to create the HTTP request object.');
  }
}

function toggleExpires() {
  if (document.getElementById('expires-check').checked) {
    document.getElementById('expires-box').style.display = '';
  } else {
    document.getElementById('expires-box').style.display = 'none';
  }
}

function saveResource() {
  var path = document.getElementById('path').value;

  var payload = {
    content: document.getElementById('content').value,
    ctype: document.getElementById('content-type').value
  };

  if (document.getElementById('date').checked) {
    payload['incdate'] = true;
  }

  if (document.getElementById('expires-check').checked) {
    payload['expires'] = document.getElementById('expires').value;
  }

  httpRequest('POST', JSON.stringify(payload), '/content_manager_json' + path,
              {}, function() {
  });
}

