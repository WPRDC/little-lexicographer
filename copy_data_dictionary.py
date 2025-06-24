import sys, time, ckanapi
from credentials import site, API_key # Use sample-credentials.py as a model for creating this file.
from pprint import pprint
from data_dictionary_util import clone_data_dictionary

def get_resource_parameter(site, resource_id, parameter=None, API_key=None):
    # Some resource parameters you can fetch with this function are
    # 'cache_last_updated', 'package_id', 'webstore_last_updated',
    # 'datastore_active', 'id', 'size', 'state', 'hash',
    # 'description', 'format', 'last_modified', 'url_type',
    # 'mimetype', 'cache_url', 'name', 'created', 'url',
    # 'webstore_url', 'mimetype_inner', 'position',
    # 'revision_id', 'resource_type'
    # Note that 'size' does not seem to be defined for tabular
    # data on WPRDC.org. (It's not the number of rows in the resource.)
    ckan = ckanapi.RemoteCKAN(site, apikey=API_key)
    metadata = ckan.action.resource_show(id=resource_id)
    if parameter is None:
        return metadata
    else:
        return metadata[parameter]

def get_package_parameter(site, package_id, parameter=None, API_key=None):
    """Gets a CKAN package parameter. If no parameter is specified, all metadata
    for that package is returned."""
    # Some package parameters you can fetch from the WPRDC with
    # this function are:
    # 'geographic_unit', 'owner_org', 'maintainer', 'data_steward_email',
    # 'relationships_as_object', 'access_level_comment',
    # 'frequency_publishing', 'maintainer_email', 'num_tags', 'id',
    # 'metadata_created', 'group', 'metadata_modified', 'author',
    # 'author_email', 'state', 'version', 'department', 'license_id',
    # 'type', 'resources', 'num_resources', 'data_steward_name', 'tags',
    # 'title', 'frequency_data_change', 'private', 'groups',
    # 'creator_user_id', 'relationships_as_subject', 'data_notes',
    # 'name', 'isopen', 'url', 'notes', 'license_title',
    # 'temporal_coverage', 'related_documents', 'license_url',
    # 'organization', 'revision_id'
    ckan = ckanapi.RemoteCKAN(site, apikey=API_key)
    metadata = ckan.action.package_show(id=package_id)
    if parameter is None:
        return metadata
    else:
        if parameter in metadata:
            return metadata[parameter]
        else:
            return None

def get_resource_name(site, resource_id, API_key=None):
    return get_resource_parameter(site, resource_id, 'name', API_key)

def get_package_name_from_resource_id(site, resource_id, API_key=None):
    p_id = get_resource_parameter(site, resource_id, 'package_id', API_key)
    return get_package_parameter(site, p_id, 'title', API_key)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Please specify two resource IDs, one for the source of the data dictionary and one for the destination.")
    source_resource_id, destination_resource_id = sys.argv[1], sys.argv[2]

    source_name = get_resource_name(site, source_resource_id, API_key)
    source_package_name = get_package_name_from_resource_id(site, source_resource_id, API_key)
    destination_name = get_resource_name(site, destination_resource_id, API_key)
    destination_package_name = get_package_name_from_resource_id(site, destination_resource_id, API_key)

    print(f'Preparing to clone data dictionary from {source_name} ({source_package_name}) to {destination_name} ({destination_package_name})...')
    time.sleep(4)
    print('On you mark! Get set!')
    time.sleep(1)
    print('Clone!')

    results = clone_data_dictionary(site, source_resource_id, destination_resource_id, API_key)
    if 'fields' in results:
        print("The destination resource's final data dictionary is:")
        pprint(results['fields'])
