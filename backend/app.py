from flask import Flask, jsonify, request
import json
from pprint import pprint
from functions.orchestrator_lib import *
from objects.NodeInfo import NodeInfo
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Permet de récupérer les infos d'un node
@app.route("/node/<ip>/info", methods=['GET'])
def get_node_info_endpoint(ip):
    node_info_array = get_node_info(get_connector_to_node(ip))
    node_info=NodeInfo(node_info_array)
    print(node_info.__dict__)
    return jsonify(node_info.__dict__)


# Permet de récupérer les infos de tout les domaines
@app.route("/node/<ip>/domains/info", methods=['GET'])
def get_all_domains_info_endpoint(ip):
    domainArray = get_all_domain_info(get_connector_to_node(ip))
    domain_dicts = [domain.to_dict() for domain in domainArray]
    return jsonify(domain_dicts)

@app.route("/node/<ip>/domains/create/<name>", methods=['GET'])
def create_domain_endpoint(ip, name):
    return create_domain(get_connector_to_node(ip), name)

@app.route("/node/<ip>/domains/destroy/<name>", methods=['GET'])
def destroy_domain_endpoint(ip, name):
    return destroy_domain(get_connector_to_node(ip), name)

@app.route("/node/<ip>/domains/undefine/<name>", methods=['GET'])
def undefine_domain_endpoint(ip, name):
    return undefine_domain(get_connector_to_node(ip), name)

@app.route("/node/<ip>/domains/getsnapshot/<name>", methods=['GET'])
def get_snapshot_name_domain_endpoint(ip, name):
    snapshot_array = get_snapshot_name_domain(get_connector_to_node(ip), name)
    snapshot_dict = [{index:snapshot} for snapshot, index in enumerate(snapshot_array)]
    # TODO: Voir Maxx le format du retour
    return jsonify(snapshot_dict)

@app.route("/node/<ip>/domains/defineXML", methods=['POST'])
def defineXML_domain_endpoint(ip):
    return defineXML_domain(get_connector_to_node(ip), request)

@app.route("/node/<ip>/domains/migrateDomain", methods=['POST'])
def migrate_domain_endpoint(ip):
    return migrate_domain(get_connector_to_node(ip), request)

# Pour les tests
if __name__ == '__main__':
    app.run(debug=True)
    #help(libvirt)
    #get_node_info_endpoint("localhost")
    pprint(get_all_domains_info_endpoint("localhost"))


# TODO: METTRE DES COMMENTAIRES