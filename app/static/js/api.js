const API_PATH = location.href.replaceAll(new RegExp('/+$', 'g'), '') + '/api';
// const API_PATH = 'http://localhost:25000/api'; // to point to other/local running container

class APIError extends Error {
  constructor(response) {
    super();
    this.response = response;
  }
}

const apiGet = (path) => fetch(API_PATH + path)
  .then(response => {
    if (response.ok) return response;
    throw new APIError(response);
  });

const apiPost = (path, body) => fetch(
  API_PATH + path,
  { method: 'POST',
    body: body ? JSON.stringify(body) : body,
    headers: body ? { 'Content-Type': 'application/json' } : {}
  })
  .then(response => {
    if (response.ok) return response;
    throw new APIError(response);
  });

const deepEqual = (x, y) => {
  if (x === y) return true;
  else if ((typeof x == 'object' && x != null) && (typeof y == 'object' && y != null)) {
    if (Object.keys(x).length != Object.keys(y).length) return false;
    for (var prop in x) {
      return y.hasOwnProperty(prop) && deepEqual(x[prop], y[prop]);
   	}
    return true;
  }
  return false;
}

const state = new Proxy(
  {
    current: {},
    servers: {},
    preferences: {},
    version: '',
    ips: {},
  },
  {
    set: function (target, key, value) {
      target[key] = value;
      if (deepEqual(target[key], value)) {
        if (key === 'current') onStatusChange();
        else if (key === 'preferences') onPreferencesChange();
        else if (key === 'servers') onServersChange();
        else if (key === 'version') onVersionChange();
        else if (key === 'ips') onIpsChange();
      }
      return true;
    },
  }
);

const isConnected = () => state.current.status === 'CONNECTED';

const onStatusChange = () => {
  if (state.current.server) {
    document.getElementById('status').replaceChildren(document.createTextNode('server: ' + state.current.server));
  } else {
    document.getElementById('status').replaceChildren(document.createTextNode(state.current.status));
  }
  document.getElementById('disconnect').disabled = !isConnected();
	updateServersIndex();
};

const onIpsChange = () => {
  document.getElementById('ips').replaceChildren(document.createTextNode(`VPN IP: ${state.ips.vpn} - Public IP: ${state.ips.public}` ));
};

const onPreferencesChange = () => {
  const prefs = document.getElementById('preferences');

  const existingDivs = document.getElementsByClassName('preference');
  for (var i = 0; i < existingDivs.length; i++) {
    if (!state.preferences[existingDivs[i].id.slice(11)]) existingDivs[i].remove();
  }

  console.info(state.preferences);
  Object.entries(state.preferences).sort((a, b) => a[0].localeCompare(b[0])).forEach(([key, value]) => {
    const existing = document.getElementById(key);
    if (existing) {
      existing.value = value;
      document.getElementById('save-' + key).disabled = true;
    } else {
      const pref = document.createElement('div');
      pref.id = 'preference-' + key;
      pref.classList.add('preference', 'row', 'justify-content-md-center', 'p-1');

      const labelDiv = document.createElement('div');
      labelDiv.classList.add('col-sm-2', 'text-start');
      const label = document.createElement('label');
      label.classList.add('col-form-label', 'form-control-sm');
      label.appendChild(document.createTextNode(key));
      labelDiv.appendChild(label);

      const valueDiv = document.createElement('div');
      valueDiv.classList.add('col-md-3');
      valueDiv.style.width = '25rem'
      const input = document.createElement(key == 'split-app' ? 'textarea' : 'input');
      if (key == 'split-app') {
        input.rows = 4
      } else {
        input.type = 'text';
      }
      input.classList.add('form-control', 'form-control-sm');
      input.id = key;
      input.value = value;
      input.addEventListener('input', e => document.getElementById('save-' + input.id).disabled = state.preferences[input.id] === e.target.value);
      valueDiv.appendChild(input);

      const buttonDiv = document.createElement('div');
      buttonDiv.classList.add('w-auto');
      const save = document.createElement('button');
      save.id = 'save-' + key;
      save.classList.add('btn', 'btn-info', 'btn-sm');
      save.type = 'button'; 
      save.disabled = true;
      save.onclick = () => savePreference(key);

      const img = document.createElement('img');
      img.alt = 'Save preference ' + key;
      img.src = 'static/img/floppy.svg'
      save.appendChild(img);
      buttonDiv.appendChild(save);

      pref.appendChild(labelDiv);
      pref.appendChild(valueDiv);
      pref.appendChild(buttonDiv);
      prefs.appendChild(pref);
    }
  });
};

const onServersChange = () => {
  const dropdown = document.getElementById('servers-list');
  dropdown.replaceChildren();

  const option_auto = document.createElement('option');
  option_auto.text = "auto";
  option_auto.value = "auto";
  dropdown.appendChild(option_auto)

  Object.entries(state.servers).forEach(([key, value]) => {
    const group = document.createElement('optgroup');
    group.label = key;
    value.forEach(server => {
      const option = document.createElement('option');
      option.text = server;
      option.value = server;
      group.appendChild(option);
    });
    dropdown.appendChild(group);
  });
};

const onVersionChange = () => document.getElementById('version').replaceChildren(document.createTextNode('v' + state.version));

const updateServersIndex = () => {
  const dropdown = document.getElementById('servers-list');
  const server = state.current.server || 'auto';
  const groups = dropdown.children;
  for (var i = 0; i < groups.length; i++) {
    const options = groups[i].children;
    for (var j = 0; j < options.length; j++) {
      if (options[j].label === server || options[j].value === server) {
        options[j].selected = true;
        return;
      }
    }
  }
};

const savePreference = async (key) => {
  value = document.getElementById(key).value
  if (/\n/.exec(value)) value = value.split('\n')
  return apiPost('/preferences', { key, value })
    .then(loadPreferences)
    .catch(function(err) {
      err.response.json()
        .then(json => addMessage(json.error))
        .finally(() => console.error(`Failed to save preference: ${key}`));
    });
};

const loadVersion = async () => {
  return apiGet('/version').then(function(response) {
    return response.json();
  }).then(function(data) {
    console.info('Version', data);
    state.version = data.version;
  }).catch(function(err) {
    console.error('Failed to load version', err);
  });
};

const loadStatus = async () => {
  return apiGet('/status').then(function(response) {
    return response.json();
  }).then(function(data) {
    console.info('Status', data);
    state.current = data;
  }).catch(function(err) {
    console.error('Failed to load status', err);
  });
};

const loadServers = async () => {
  return apiGet('/servers').then(function(response) {
    return response.json();
  }).then(function(data) {
    console.info('Servers', data);
    state.servers = data.servers;
  }).catch(function(err) {
    addMessage(err, 'danger');
    console.error('Failed to load servers', err);
  });
};

const loadPreferences = async () => {
  return apiGet('/preferences').then(function(response) {
    return response.json();
  }).then(function(data) {
    console.info('Preferences', data);
    state.preferences = data;
  }).catch(function(err) {
    console.error('Failed to load preferences', err);
  });
};

const connect = async () => {
  const dropdown = document.getElementById('servers-list');
  const server = dropdown.options[dropdown.selectedIndex];

  console.info('Connecting to:', server.label);

  return disableControls('connect')
    .then(() => apiPost('/connect/' + server.value))
    .then(loadStatus)
    .then(loadIps)
    .catch(function(err) {
      console.error('Failed to connect to: ' + server, err);
    }).finally(enableControls);
};

const disconnect = async () => {
  console.info('Disconnecting');

  return disableControls('disconnect')
    .then(() => apiPost('/disconnect'))
    .then(loadStatus)
    .then(loadIps)
    .catch(function(err) {
      console.error('Failed to disconnect', err);
    }).finally(enableControls);
};

const loadIps = async () => {
  return apiGet('/ips').then(function(response) {
    return response.json();
  }).then(function(data) {
    console.info('IPs', data);
    state.ips = {
      vpn: data.vpn_ip,
      public: data.public_ip
    };
  }).catch(function(err) {
    console.error('Failed to load Ips', err);
  });
}

const enableControls = () => {
  ['connect', 'disconnect'].forEach(id => {
    const btn = document.getElementById(id);
    btn.disabled = false;
    btn.children[0].classList.add('visually-hidden');
  });

  document.getElementById('disconnect').disabled = !isConnected();
};

const disableControls = async (id) => {
  ['connect', 'disconnect'].forEach(btnId => document.getElementById(btnId).disabled = true);
  if (id) document.getElementById(id).children[0].classList.remove('visually-hidden');
};

const addMessage = (value, kind = 'danger') => {
  const id = Date.now();
  const message = document.createElement('div');
  message.setAttribute('id', id);
  message.classList.add('alert', 'alert-' + kind, 'alert-dismissible', 'fade', 'show');
  message.setAttribute('role', 'alert');
  message.appendChild(document.createTextNode(value));
  const closeButton = document.createElement('button');
  closeButton.classList.add('btn-close');
  closeButton.setAttribute('data-bs-dismiss', 'alert');
  closeButton.setAttribute('type', 'button');
  closeButton.setAttribute('aria-label', 'Close');
  message.appendChild(closeButton);
  document.getElementById('messages').appendChild(message);
  const bootstrapMessage = new bootstrap.Alert(message);
  setTimeout(() => {
    if (document.getElementById(id)) bootstrapMessage.close();
  }, 5000);
};

const loadAll = () => {
  disableControls()
    .then(loadVersion)
    .then(loadServers)
    .then(loadStatus)
    .then(loadIps)
    .then(loadPreferences)
    .finally(enableControls);

  setInterval(loadStatus, 10000)
};

window.addEventListener('load', loadAll);
