import sys, csv
from credentials import site, API_key # Use sample-credentials.py as a model for creating this file.
from pprint import pprint
from data_dictionary_util import clone_data_dictionary, set_data_dictionary
from lil_lex import base_schema_type

def synthesize_data_dictionary(reader, set_types=False):
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

    type_override_attempts = 0
    fields = []
    for row in reader:
        field = {'id': row['column'],
                'info': {'label': row.get('label', ''),
                        'notes': row.get('description', ''),
                        },
                #'type':
                }
        if 'type_override' in row and row['type_override'] in base_schema_type.keys():
            field['info']['type_override'] = row['type_override']
            type_override_attempts += 1 # The new type could be checked against
            # existing type to verify that an actual change is being attempted.
        fields.append(field)

    print(f"NOTE!!! If you are trying to modify the types of {type_override_attempts} field{'s' if type_override_attempts != 1 else ''}, note that you must click on Manage and switch to the Datastore tab and then click the 'Upload to Datastore' button to actually update the fields.\n")
    return fields

if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise ValueError("Please specify the filename of the CSV file (representing the data dictionary) and the resource ID of the CKAN table that is the destination for the integrated data dictionary.\nUsage:\n   > python upload_data_dictionary.py data_dictionary.csv <CKAN resource ID>")
    csv_file_path, destination_resource_id = sys.argv[1], sys.argv[2]

    # Validate data dictionary.
    with open(csv_file_path, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        fields = synthesize_data_dictionary(reader)

    results = set_data_dictionary(site, destination_resource_id, fields, API_key)
    if 'fields' in results:
        print("The destination resource's final data dictionary is:")
        pprint(results['fields'])
