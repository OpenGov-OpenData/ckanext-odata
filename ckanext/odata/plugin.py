import ckan.plugins as p
import ckan.plugins.toolkit as toolkit

import ckanext.odata.actions as action


def link(resource_id):
    return '%s%s' % (action.base_url(), resource_id)

def resource_format(resource_id):
    result = toolkit.get_action('resource_show')({}, {'id': resource_id})
    res_format = result.get('format','').lower()
    if res_format == 'csv':
        return True
    else:
        return False

class ODataPlugin(p.SingletonPlugin):

    p.implements(p.IConfigurer)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IActions)
    p.implements(p.ITemplateHelpers, inherit=True)

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_resource('resources', 'odata')

    def before_map(self, m):
        m.connect('/datastore/odata3.0/$metadata',
                  controller='ckanext.odata.controller:ODataController',
                  action='odata_metadata')
        m.connect('/datastore/odata3.0/{uri:.*?}',
                  controller='ckanext.odata.controller:ODataController',
                  action='odata')
        return m

    def get_actions(self):
        actions = {
            'ckanext-odata_metadata': action.odata_metadata,
            'ckanext-odata_odata': action.odata,
        }
        return actions

    def get_helpers(self):
        return {
            'ckanext_odata_link': link,
            'ckanext_odata_res_format': resource_format,
        }
