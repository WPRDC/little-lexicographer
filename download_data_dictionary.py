import sys, csv
from credentials import site, API_key # Use sample-credentials.py as a model for creating this file.
from pprint import pprint
from icecream import ic
from data_dictionary_util import clone_data_dictionary, set_data_dictionary, get_data_dictionary
from lil_lex import base_schema_type

def write_to_csv(filename, list_of_dicts, keys=None):
    if keys is None: # Extract fieldnames if none were passed.
        print(f'Since keys == None, write_to_csv is inferring the fields to write from the list of dicts.')
        keys = list_of_dicts[0].keys() # Shouldn't this be fine?

        #keys = set()
        #for row in list_of_dicts:
        #    keys = set(row.keys()) | keys
        #keys = sorted(list(keys)) # Sort them alphabetically, in the absence of any better idea.
        ## [One other option would be to extract the field names from the schema and send that
        ## list as the third argument to write_to_csv.]
        print(f'Extracted keys: {keys}')
    with open(filename, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys, extrasaction='ignore', lineterminator='\n')
        dict_writer.writeheader()
        dict_writer.writerows(list_of_dicts)

def clean(s):
    import re
    s = re.sub('\t$', '', s)
    s = re.sub('\n$', '', s)
    s = re.sub('\r$', '', s)
    return s

# The current default fields for the CKAN integrated data dictionary are:
    # column - The actual field name
    # type - The type of the field
    # label - The human-readable version of the field name
    # notes - A more detailed description of the field (but the downloadable OUTPUT is called 'description').
    # type_override (optional) - Allow overriding of the existing CKAN field type.
    #       Note: This has not been tested on cases where the field values can 
    #       not be coerced to the specified type.

# CKAN wants the fields value to represent a data dictionary like this:
# [{'id': 'Number',
#  'info': {'label': '#', 'notes': 'The count', 'type_override': ''},
#  'type': 'text'},
# {'id': 'Another Number',
#  'info': {'label': "#'", 'notes': 'The other count', 'type_override': ''},
#  'type': 'text'},
# {'id': 'Subway',
#  'info': {'label': '!', 'notes': '', 'type_override': ''},
#  'type': 'text'}]

def convert_fields_to_list_of_dicts(fields):
# {'id': 'TAXYEAR',
#  'info': {'label': 'The current certified tax year\t',
#           'notes': 'The applicable year for which real estate taxes would '
#                    'apply for the parcel. Allegheny County currently assesses '
#                    'value based on how the parcel stood as of Jan 1 of that '
#                    'year. This need not correspond to a calendar year.\r\n',
#           'type_override': ''},
#  'type': 'text'},
# {'id': 'ASOFDATE',
#  'info': {'label': '',
#           'notes': 'The run date of this file\t',
#           'type_override': ''},
#  'type': 'text'}]
    rows = []
    for field in fields:
        info = field.get('info', {})
        row = {'column': field['id'], 'type': field['type'], 'label': clean(info.get('label', '')), 'description': clean(info.get('notes', ''))}
        rows.append(row)
    return rows

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError("Please specify the resource ID of the CKAN table that is the source for the integrated data dictionary.\nUsage:\n   > python download_data_dictionary.py <CKAN resource ID>")
    source_resource_id = sys.argv[1]

    fields = get_data_dictionary(site, source_resource_id, API_key)

    field_dicts = convert_fields_to_list_of_dicts(fields)
    write_to_csv(f'{source_resource_id}-data-dictionary.csv', field_dicts, ['column', 'type', 'label', 'description'])
    print(f"Wrote data dictionary to local file: {source_resource_id}-data-dictionary.csv")
