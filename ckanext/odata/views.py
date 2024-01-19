from flask import Blueprint
from ckanext.odata import utils


odata_blueprint = Blueprint(u'odata_blueprint', __name__)


def odata_metadata():
    return utils.odata_metadata()

def odata(uri):
    return utils.odata(uri)


odata_blueprint.add_url_rule('/datastore/odata3.0/$metadata', view_func=odata_metadata)
odata_blueprint.add_url_rule('/datastore/odata3.0/<uri>', view_func=odata)


def get_blueprints():
    return [odata_blueprint]
