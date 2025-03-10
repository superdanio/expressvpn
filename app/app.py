import dataclasses
from flask import Flask, Response, jsonify, redirect, render_template, request
from client import Client

app = Flask(__name__)
client = Client()


@app.route('/')
@app.route('/home')
@app.route('/index.html')
def home():
    return render_template('index.html')

@app.route('/api/test', methods=['GET'])
def test():
    try:
        return redirect(request.args['url'].strip())
    except KeyError:
        return jsonify(error="Query param 'url' is missing"), 400

@app.route('/api/version', methods=['GET'])
def get_version():
    return dataclasses.asdict(client.version())

@app.route('/api/servers', methods=['GET'])
def get_servers():
    return dataclasses.asdict(client.servers())

@app.route('/api/status', methods=['GET'])
def get_status():
    return dataclasses.asdict(client.status())

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    client.disconnect()
    return Response(204)

@app.route('/api/connect', defaults={'server': 'smart'}, methods=['POST'])
@app.route('/api/connect/<string:server>', methods=['POST'])
def connect(server):
    try:
        client.connect(server)
        return Response(204)
    except ValueError as e:
        return jsonify(error=str(e)), 500

@app.route('/api/refresh', methods=['POST'])
def refresh():
    client.refresh()
    return Response(204)

@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    return dataclasses.asdict(client.preferences())

@app.route('/api/preferences/<string:name>/<string:value>', methods=['POST'])
def set_preference(name, value):
    try:
        client.set_preference(name, value)
        return Response(204)
    except ValueError as e:
        return jsonify(error=str(e)), 500

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response
