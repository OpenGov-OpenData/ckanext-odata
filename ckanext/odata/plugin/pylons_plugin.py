import ckan.plugins as p


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IRoutes, inherit=True)

    def before_map(self, m):
        m.connect('/datastore/odata3.0/$metadata',
                  controller='ckanext.odata.controller:ODataController',
                  action='odata_metadata')
        m.connect('/datastore/odata3.0/{uri:.*?}',
                  controller='ckanext.odata.controller:ODataController',
                  action='odata')
        return m
