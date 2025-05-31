from flask import Flask, jsonify, request, Response
from functools import wraps
import random

app = Flask(__name__)

# Basic auth credentials (for demonstration; in production, use a secure method)
USERS = {
    "admin": "password1"
}


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                'Unauthorized', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        return f(*args, **kwargs)

    return decorated


def check_auth(username, password):
    return username in USERS and USERS[username] == password


@app.route('/rest/system/identity', methods=['GET'])
@require_auth
def system_identity():
    return jsonify({
        "name": "System1",
        "routerboard": True,
        "version": "7.0.1",
        "serial-number": "1234567890"
    })


@app.route('/rest/routing/bgp/template', methods=['GET'])
@require_auth
def bgp_template():
    disabled = request.args.get('disabled', 'false').lower() == 'true'
    templates = [
        {
            "id": "bgp",
            "name": "bgp",
            "disabled": False,
            "as": 65000,
            "output": {"network": "bgp-networks"},
            "router-id": "4.4.4.4",
        },
    ]
    filtered_templates = [t for t in templates if t['disabled'] == disabled]
    return jsonify(filtered_templates)


@app.route('/rest/routing/bgp/connection', methods=['GET'])
@require_auth
def bgp_connection():
    connections = [
        {
            "name": "peer1",
            "as": "65000",
            "router-id": "4.4.4.4",
            "local.address": "10.0.14.2",
            "remote.as": "65000",
            "remote.address": "10.0.14.1/32"
        },
        {
            "name": "peer2",
            "as": "65000",
            "router-id": "4.4.4.4",
            "local.address": "10.0.24.2",
            "remote.as": "65000",
            "remote.address": "10.0.24.1/32"
        },
        {
            "name": "peer3",
            "as": "65000",
            "router-id": "4.4.4.4",
            "local.address": "10.0.34.2",
            "remote.as": "65000",
            "remote.address": "10.0.34.1/32"
        },
        {
            "name": "peer5",
            "as": "65000",
            "router-id": "4.4.4.4",
            "local.address": "10.0.45.1",
            "remote.as": "65000",
            "remote.address": "10.0.45.2/32"
        },
    ]
    return jsonify([
        c for c in connections
        if random.random() < 0.5
    ])


@app.route('/rest/ip/route', methods=['GET'])
@require_auth
def ip_route():
    routes = [
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.1.0/24",
            "gateway": "10.0.14.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.2.0/24",
            "gateway": "10.0.14.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.3.0/24",
            "gateway": "10.0.14.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.4.0/24",
            "gateway": "10.0.14.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.5.0/24",
            "gateway": "10.0.24.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.6.0/24",
            "gateway": "10.0.24.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.7.0/24",
            "gateway": "10.0.24.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.8.0/24",
            "gateway": "10.0.24.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.9.0/24",
            "gateway": "10.0.34.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.10.0/24",
            "gateway": "10.0.34.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.11.0/24",
            "gateway": "10.0.34.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.12.0/24",
            "gateway": "10.0.34.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.17.0/24",
            "gateway": "10.0.45.2",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.18.0/24",
            "gateway": "10.0.45.2",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.19.0/24",
            "gateway": "10.0.45.2",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.20.0/24",
            "gateway": "10.0.45.2",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "192.168.179.0/24",
            "gateway": "10.0.14.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "1.1.1.1/32",
            "gateway": "10.0.14.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "2.2.2.2/32",
            "gateway": "10.0.24.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "3.3.3.3/32",
            "gateway": "10.0.34.1",
            "distance": "200"
        },
        {
            "router-id": "4.4.4.4",
            "dst-address": "5.5.5.5/32",
            "gateway": "10.0.45.2",
            "distance": "200"
        }
    ]
    return jsonify(routes) if random.random() < 0.1 else jsonify([
        r for r in routes
        if random.random() > 0.5
    ])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
