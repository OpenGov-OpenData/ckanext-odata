import ckan.plugins as p
import ckanext.odata.actions as action

if p.toolkit.check_ckan_version('2.9'):
    from ckanext.odata.plugin.flask_plugin import MixinPlugin
else:
    from ckanext.odata.plugin.pylons_plugin import MixinPlugin


def link(resource_id):
    return '{0}{1}'.format(action.base_url(), resource_id)


class ODataPlugin(MixinPlugin, p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IActions)
    p.implements(p.ITemplateHelpers, inherit=True)

    def update_config(self, config):
        p.toolkit.add_template_directory(config, '../templates')
        p.toolkit.add_resource('../resources', 'odata')

    def get_actions(self):
        actions = {
            'ckanext-odata_metadata': action.odata_metadata,
            'ckanext-odata_odata': action.odata,
        }
        return actions

    def get_helpers(self):
        return {
            'ckanext_odata_link': link,
        }
