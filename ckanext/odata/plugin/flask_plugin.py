import ckan.plugins as p
import ckanext.odata.views as views


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)

    def get_blueprint(self):
        return views.get_blueprints()
