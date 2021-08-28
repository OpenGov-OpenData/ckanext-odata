from ckan.plugins.toolkit import BaseController
from ckanext.odata import utils

class ODataController(BaseController):

    def odata(self, uri):
        return utils.odata(uri)

    def odata_metadata(self):
        return utils.odata_metadata()
