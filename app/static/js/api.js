const API_PATH = location.href.replaceAll(new RegExp('/+$', 'g'), '') + '/api';
// const API_PATH = 'http://localhost:25000/api'; // to point to other/local running container

const apiGet = (path) => fetch(API_PATH + path);
const apiPost = (path) => fetch(API_PATH + path, { method: 'POST' });
const deepEqual = (x, y) => {
  if (x === y) return true;
  else if ((typeof x == "object" && x != null) && (typeof y == "object" && y != null)) {
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
    version: ''
  },
  {
    set: function (target, key, value) {
      target[key] = value;
      if (deepEqual(target[key], value)) {
        if (key === 'current') onStatusChange();
        else if (key === 'preferences') onPreferencesChange();
        else if (key === 'servers') onServersChange();
        else if (key === 'version') onVersionChange();
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

const onPreferencesChange = () => {
  const prefs = document.getElementById('preferences');

  const existingDivs = document.getElementsByClassName('preference');
  for (var i = 0; i < existingDivs.length; i++) {
    if (!state.preferences[existingDivs[i].id.slice(11)]) existingDivs[i].remove();
  }

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
      labelDiv.classList.add('col-sm-6', 'text-start');
      const label = document.createElement('label');
      label.classList.add('col-form-label', 'form-control-sm');
      label.appendChild(document.createTextNode(key));
      labelDiv.appendChild(label);

      const valueDiv = document.createElement('div');
      valueDiv.classList.add('col-md-3');
      const input = document.createElement('input');
      input.classList.add('form-control', 'form-control-sm');
      input.id = key;
      input.value = value;
      input.type = 'text'
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

  Object.entries(state.servers).forEach(([key, value]) => {
    const group = document.createElement('optgroup');
    group.label = key;
    value.forEach(server => {
      const option = document.createElement('option');
      option.text = server.location;
      option.value = server.alias;
      group.appendChild(option);
    });
    dropdown.appendChild(group);
	});
};

const onVersionChange = () => document.getElementById('version').replaceChildren(document.createTextNode('v' + state.version));

const updateServersIndex = () => {
  const dropdown = document.getElementById('servers-list');
  const server = state.current.server || 'smart';
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
  return apiPost(`/preferences/${key}/${document.getElementById(key).value}`)
    .then(loadPreferences)
    .catch(function(err) {
      console.error('Failed to load version', err);
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
    console.error('Failed to load servers', err);
  });
};

const loadPreferences = async () => {
  return apiGet('/preferences').then(function(response) {
    return response.json();
  }).then(function(data) {
    console.info('Preferences', data);
		state.preferences = data.preferences;
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
    .catch(function(err) {
      console.error('Failed to connect to: ' + server, err);
    }).finally(enableControls);
};

const disconnect = async () => {
  console.info('Disconnecting');

  return disableControls('disconnect')
    .then(() => apiPost('/disconnect'))
    .then(loadStatus)
    .catch(function(err) {
      console.error('Failed to disconnect', err);
    }).finally(enableControls);
};

const refreshCluster = async () => {
  console.info('Refreshing cluster');

  return disableControls('refresh-cluster')
    .then(() => apiPost('/refresh'))
    .then(loadServers)
    .then(loadStatus)
    .catch(function(err) {
      console.error('Failed to disconnect', err);
    }).finally(enableControls);
};

const enableControls = () => {
  ['connect', 'disconnect', 'refresh-cluster'].forEach(id => {
    const btn = document.getElementById(id);
    btn.disabled = false;
    btn.children[0].classList.add("visually-hidden");
  });

  document.getElementById('disconnect').disabled = !isConnected();
};

const disableControls = async (id) => {
  ['connect', 'disconnect', 'refresh-cluster'].forEach(btnId => document.getElementById(btnId).disabled = true);
  if (id) document.getElementById(id).children[0].classList.remove("visually-hidden");
};

const loadAll = () => {
  disableControls()
    .then(loadVersion)
    .then(loadServers)
    .then(loadStatus)
    .then(loadPreferences)
    .finally(enableControls);

  setInterval(loadStatus, 10000)
};

window.addEventListener('load', loadAll);
