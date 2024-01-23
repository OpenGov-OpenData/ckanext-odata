import re
import simplejson as json
import ckan.plugins.toolkit as t

from flask import make_response
from ckan.exceptions import CkanVersionException

try:
    from collections import OrderedDict  # from python 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict


TYPE_TRANSLATIONS = {
    'null': 'Edm.Null',
    'bool': 'Edm.Boolean',
    'float8': 'Edm.Double',
    'numeric': 'Edm.Double',
    'int4': 'Edm.Int32',
    'int8': 'Edm.Int64',
    'timestamp': 'Edm.DateTime',
    'text': 'Edm.String',
}

name_pattern = r'[^:A-Z_a-z.0-9\u00B7\u00C0-\u00D6\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\u0300-\u036F\u203F-\u2040]'

_base_url = None


def get_request_param():
    try:
        requires_ckan_version("2.9")
    except:
        return t.request.params
    else:
        return t.request.args


def name_2_xml_tag(name):
    ''' Convert a name into a xml safe name.

    From w3c specs (http://www.w3.org/TR/REC-xml/#NT-NameChar)
    a valid XML element name must follow these naming rules:

    NameStartChar ::= ":" | [A-Z] | "_" | [a-z] | [#xC0-#xD6] | [#xD8-#xF6] |
        [#xF8-#x2FF] | [#x370-#x37D] | [#x37F-#x1FFF] | [#x200C-#x200D] |
        [#x2070-#x218F] | [#x2C00-#x2FEF] | [#x3001-#xD7FF] | [#xF900-#xFDCF] |
        [#xFDF0-#xFFFD] | [#x10000-#xEFFFF]

    NameChar ::= NameStartChar | "-" | "." | [0-9] | #xB7 | [#x0300-#x036F] |
        [#x203F-#x2040]
    '''

    # leave well-formed XML element characters only
    name = re.sub(name_pattern, '', name)

    # add '_' in front of non-NameStart characters
    name = re.sub(re.compile(r'(?P<q>^[-.0-9\u00B7#\u0300-\u036F\u203F-\u2040])', re.MULTILINE),
                  '_\g<q>', name)

    # No valid XML element at all
    if name == '':
        name = 'NaN'

    return name


def get_qs_int(param, default):
    ''' Get a query string param as an int '''
    request_params = get_request_param()
    value = request_params.get(param, default)
    try:
        value = int(value)
    except ValueError:
        value = default
    return value


def base_url():
    ''' The base url of the OData service '''
    global _base_url
    if not _base_url:
        _base_url = t.url_for('/datastore/odata3.0/', qualified=True)
    return _base_url


def odata(context, data_dict):

    uri = data_dict.get('uri')
    
    match = re.search(r'^(.*)\((\d+)\)$', uri)
    if match:
        resource_id = match.group(1)
        row_id = int(match.group(2))
        filters = {'_id': row_id}
    else:
        row_id = None
        resource_id = uri
        filters = {}
    
    request_params = get_request_param()
    output_json = request_params.get('$format') == 'json'
    
    # Ignore $limit & $top paramters if $sqlfilter is specified
    # as they should be specified by the sql query
    if request_params.get('$sqlfilter'):
        action = t.get_action('datastore_search_sql')

        query = request_params.get('$sqlfilter', '')
        sql = "SELECT * FROM \"{}\" {}".format(resource_id, query)
        
        data_dict = {
            'sql': sql
        }
    else:
        action = t.get_action('datastore_search')
        
        limit = get_qs_int('$top', 500)
        offset = get_qs_int('$skip', 0)

        data_dict = {
            'resource_id': resource_id,
            'filters': filters,
            'limit': limit,
            'offset': offset
        }
        
    try:
        result = action({}, data_dict)
    except t.ObjectNotFound:
        t.abort(404, t._('DataStore resource not found'))
    except t.NotAuthorized:
        t.abort(401, t._('DataStore resource not authourized'))
    except t.ValidationError as e:
        return json.dumps(e.error_dict)
    
    if not request_params.get('$sqlfilter'):
        num_results = result['total']
        if num_results > offset + limit:
            next_query_string = '$skip=%s&$top=%s' % (offset + limit, limit)
        else:
            next_query_string = None
    else:
        next_query_string = None

    action = t.get_action('resource_show')
    resource = action({}, {'id': resource_id})

    if output_json:
        out = OrderedDict()
        out['odata.metadata'] = 'FIXME'
        out['value'] = result['records']

        response = json.dumps(out)
        return response
    else:
        convert = []
        for field in result['fields']:
            convert.append({
                'id': field['id'],
                'name': name_2_xml_tag(field['id']),
                # if we have no translation for a type use Edm.String
                'type': TYPE_TRANSLATIONS.get(field['type'], 'Edm.String'),
            })
        data = {
            'title': resource['name'],
            'updated': resource['last_modified'] or resource['created'],
            'base_url': base_url(),
            'collection': uri,
            'convert': convert,
            'entries': result['records'],
            'next_query_string': next_query_string,
        }
        try:
            t.requires_ckan_version("2.9")
        except CkanVersionException:
            t.response.headers['Content-Type'] = 'application/atom+xml;type=feed;charset=utf-8'
            return t.render('ckanext-odata/collection.xml', data)
        else:
            response = make_response(t.render('ckanext-odata/collection.xml', data))
            response.headers['Content-Type'] = 'application/atom+xml;type=feed;charset=utf-8'
            return response


def odata_metadata(context, data_dict):
    try:
        table_metadata_dict = {
            'resource_id': '_table_metadata',
            'limit': '1000',
            'sort': 'oid desc'
        }
        table_metadata = t.get_action('datastore_search')({}, table_metadata_dict)
        records = table_metadata.get('records', [])
    except t.ObjectNotFound:
        t.abort(404, t._('Table Metadata not found'))
    except t.NotAuthorized:
        t.abort(401, t._('Table Metadata not authourized'))


    collections = []
    for record in records:
        if record.get('name') == '_table_metadata' or len(record.get('name')) != 36:
            continue

        try:
            field_lookup_dict = {
                'resource_id': record.get('name'),
                'limit': '0',
            }
            field_lookup = t.get_action('datastore_search')({}, field_lookup_dict)
            fields = field_lookup.get('fields', [])
        except:
            continue

        collection = {
            'name': record.get('name'),
            'fields': [
                {
                    'name': name_2_xml_tag(field['id']),
                    'type': TYPE_TRANSLATIONS.get(field['type'], 'Edm.String')
                }
                for field in fields
            ]
        }
        collections.append(collection)

    data = { 'collections' : collections }

    try:
        t.requires_ckan_version("2.9")
    except CkanVersionException:
        t.response.headers['Content-Type'] = 'application/xml;charset=utf-8'
        return t.render('ckanext-odata/metadata.xml', data)
    else:
        response = make_response(t.render('ckanext-odata/metadata.xml', data))
        response.headers['Content-Type'] = 'application/xml;charset=utf-8'
        return response
