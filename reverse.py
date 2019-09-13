# A little script to take a data dictionary, strip out the field names, and make a 
# blank CSV file with those field names as the headers.
import re, sys, csv
from collections import OrderedDict, defaultdict
from pprint import pprint

from lil_lex import detect_case

def is_snake_case(s):
    return detect_case(s) == 'snake_case'

def main():
    if len(sys.argv) < 2:
        print("Please specify the name of the data-dictionary CSV file from which you wish to generate")
        print('a template for a CSV file as a command-line argument. For example:')
        print('      > python reverse.py some_data_dictionary.csv')
    else:
        # Extract the column with name "field_name".
        csv_file_path = sys.argv[1]
        if re.search('\.csv$', csv_file_path) is None:
            print('This whole thing falls apart if the file name does not end in ".csv". Sorry.')
        else:
            with open(csv_file_path) as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                print(headers)

        if 'field_name' in headers:
            dictionary_filename = sys.argv[1]
            list_of_dicts = list(csv.DictReader(open(dictionary_filename)))

            fields = [d['field_name'] for d in list_of_dicts]

            headers_path = re.sub("\.csv","-headers.csv",csv_file_path)
            with open(headers_path, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()
            print("Template generated from data dictionary file.")
        else:
            print("This script could not find a column named 'field_name', which is where it expects to get the field names from.")


if __name__ == '__main__':
    main()
