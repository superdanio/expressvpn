import dataclasses
from typing import cast
from flask import Flask, jsonify, redirect, render_template, request
from models import SinglePreference
from client import Client

app = Flask(__name__)
client = Client()

@app.errorhandler(Exception)
def handle_exception(e):
    return { 'error': str(e) }, 500

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

@app.route('/api/ips', methods=['GET'])
def get_ips():
    return dataclasses.asdict(client.ips())

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    client.disconnect()
    return '', 204

@app.route('/api/connect', defaults={'server': 'smart'}, methods=['POST'])
@app.route('/api/connect/<string:server>', methods=['POST'])
def connect(server):
    try:
        client.connect(server)
        return '', 204
    except ValueError as e:
        return jsonify(error=str(e)), 500

@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    return client.preferences()

@app.route('/api/preferences', methods=['POST'])
def set_preference():
    try:
        pref: SinglePreference = cast(SinglePreference, request.json)
        client.set_preference(pref["key"], pref["value"])
        return '', 204
    except ValueError as e:
        return jsonify(error=str(e)), 500

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response
