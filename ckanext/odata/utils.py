import ckan.plugins.toolkit as toolkit

def odata(uri):
    data_dict = {'uri': uri}
    result = toolkit.get_action('ckanext-odata_odata')({}, data_dict)
    return result

def odata_metadata():
    result = toolkit.get_action('ckanext-odata_metadata')({}, {})
    return result
