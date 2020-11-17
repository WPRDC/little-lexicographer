import sys
from credentials import site, API_key # Use sample-credentials.py as a model for creating this file.
from pprint import pprint
from data_dictionary_util import clone_data_dictionary

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Please specify two resource IDs, one for the source of the data dictionary and one for the destination.")
    source_resource_id, destination_resource_id = sys.argv[1], sys.argv[2]
    results = clone_data_dictionary(site, source_resource_id, destination_resource_id, API_key)
    if 'fields' in results:
        print("The destination resource's final data dictionary is:")
        pprint(results['fields'])
