import sys, ckanapi
from credentials import site, API_key # Use sample-credentials.py as a model for creating this file.
from pprint import pprint

def get_fields(site, resource_id, API_key=None):
    try:
        ckan = ckanapi.RemoteCKAN(site, apikey=API_key)
        results_dict = ckan.action.datastore_search(resource_id=resource_id, limit=0)
        schema = results_dict['fields']
        fields = [d['id'] for d in schema]
    except:
        return None

    return fields

def schema_dict(schema):
    # A basic schema (without the data-dictionary info field) looks like this:
    #[{'id': '_id', 'type': 'int4'},
    # {'id': 'pin', 'type': 'text'},
    # {'id': 'block_lot', 'type': 'text'},
    # {'id': 'filing_date', 'type': 'date'},
    # {'id': 'tax_year', 'type': 'int4'},
    # {'id': 'dtd', 'type': 'text'},
    # {'id': 'lien_description', 'type': 'text'},
    # {'id': 'municipality', 'type': 'text'},
    # {'id': 'ward', 'type': 'text'},
    # {'id': 'last_docket_entry', 'type': 'text'},
    # {'id': 'amount', 'type': 'float8'},
    # {'id': 'assignee', 'type': 'text'}]
    # This function converts it into a more useful form:
    # {'_id': 'int4', 'pin': 'text',...}
    d = {}
    for s in schema:
        d[s['id']] = s['type']
    return d

def get_schema(site, resource_id, API_key=None):
    try:
        ckan = ckanapi.RemoteCKAN(site, apikey=API_key)
        results_dict = ckan.action.datastore_search(resource_id=resource_id, limit=0)
        schema = results_dict['fields']
    except:
        return None

    return schema

def get_data_dictionary(site, resource_id, API_key=None):
    try:
        ckan = ckanapi.RemoteCKAN(site, apikey=API_key)
        results = ckan.action.datastore_search(resource_id=resource_id)
        return results['fields']
    except ckanapi.errors.NotFound: # Either the resource doesn't exist, or it doesn't have a datastore.
        return None

def set_data_dictionary(site, resource_id, old_fields, API_key):
    # Here "old_fields" needs to be in the same format as the data dictionary
    # returned by get_data_dictionary: a list of type dicts and info dicts.
    # Though the '_id" field needs to be removed for this to work.
    if old_fields[0]['id'] == '_id':
        old_fields = old_fields[1:]

    # Note that a subset can be sent, and they will update part of
    # the integrated data dictionary.
    ckan = ckanapi.RemoteCKAN(site, apikey=API_key)
    present_fields = get_data_dictionary(site, resource_id, API_key)
    new_fields = []
    # Attempt to set data-dictionary values, taking into account the deletion and addition of fields, and ignoring any changes in type.
    # Iterate through the fields in the data dictionary and try to apply them to the newly created data table.
    for field in present_fields:
        if field['id'] != '_id':
            definition = next((f['info'] for f in old_fields if f['id'] == field['id']), None)
            if definition is not None:
                nf = dict(field)
                nf['info'] = definition
                new_fields.append(nf)

    results = ckan.action.datastore_create(resource_id=resource_id, fields=new_fields, force=True)
    # The response without force=True is
    # ckanapi.errors.ValidationError: {'__type': 'Validation Error', 'read-only': 
    #  ['Cannot edit read-only resource. Either pass "force=True" or change url-type to "datastore"']}
    # With force=True, it works.

    return results

def compare_schemas(site, source_resource_id, destination_resource_id, API_key):
    source_schema_dict = schema_dict(get_schema(site, source_resource_id, API_key))
    destination_schema_dict = schema_dict(get_schema(site, destination_resource_id, API_key))

    source_fields = source_schema_dict.keys()
    destination_fields = destination_schema_dict.keys()

    if set(source_fields) == set(destination_fields):
        schemas_match = True
        print("The source and destination field names match exactly.")
        for field, field_type in source_schema_dict.items():
            if field_type != destination_schema_dict[field]:
                schemas_match = False
                print(f"  field type mismatch for {field} ({field_type} != {destination_schema_dict[field]}")
    else:
        schemas_match = False
        if len(source_fields & destination_fields) > 0:
            print("There are differences between the source and destination field names.")
            print(f"The field names that are common to both tables are: {source_fields & destination_fields}.")
        else:
            print("There are no common field names between the source and destination.")
        if len(source_fields - destination_fields) > 0:
            print(f"The field names that are unique to the source are: {source_fields - destination_fields}.")
        if len(destination_fields - source_fields) > 0:
            print(f"The field names that are unique to the destination are: {destination_fields - source_fields}.")
        print(f"(Field types have not been compared.)")
    return schemas_match 

def clone_data_dictionary(site, source_resource_id, destination_resource_id, API_key):
    """This function takes the integrated data dictionary from the source resource 
    and attempts to apply it to the destination resource."""

    fields = get_data_dictionary(site, source_resource_id, API_key)
    if fields is None:
        raise ValueError(f"Unable to get a data dictionary from the CKAN resource with ID {source_resource_id} (the source table).")
    destination_fields = get_data_dictionary(site, destination_resource_id, API_key)
    if destination_fields is None:
        raise ValueError(f"Unable to get a data dictionary from the CKAN resource with ID {destination_resource_id} (the destination table).")

    # Verify that data dictionary can be applied to the destination.
    schemas_match = compare_schemas(site, source_resource_id, destination_resource_id, API_key)

    # Regardless of the degree of matching between the schemas, try to apply as 
    # many of the source definitions as possible.
    print("Overwriting destination table's data dictionary with any matching fields from the source table's data dictionary.\n")
    results = set_data_dictionary(site, destination_resource_id, fields, API_key)
    return results

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Please specify two resource IDs, one for the source of the data dictionary and one for the destination.")
    source_resource_id, destination_resource_id = sys.argv[1], sys.argv[2]
    results = clone_data_dictionary(site, source_resource_id, destination_resource_id, API_key)
    if 'fields' in results:
        print("The destination resource's final data dictionary is:")
        pprint(results['fields'])
