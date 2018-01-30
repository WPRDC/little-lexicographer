import re, sys, csv

from collections import OrderedDict

type_converter = {str: 'text', int: 'integer', float: 'float', bool: 'boolean'}

def main():
    if len(sys.argv) < 2:
        print("Please specify the name of the CSV file for which you want to generate")
        print('a data dictionary as a command-line argument. For example:')
        print('      > python lillex.py robot_census.csv')
    elif len(sys.argv) > 2:
        print("This script is not yet ready to handle more than one file at a time.")
    else:
        csv_file_path = sys.argv[1]
        if re.search('\.csv$', csv_file_path) is None:
            print('This whole fragile thing fals apart if the file name does not end in ".csv". Sorry.')
        else:
            with open(csv_file_path) as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                print(headers)
                examples = []
                types = []
                # Remove the _id field added by CKAN, if it's there.
                if '_id' in headers:
                    headers.remove('_id')
                rows = list(reader) # This is necessary since if you just iterate over 
                # the reader once, you can't use it again without doing something.
                for n,field in enumerate(headers):
                    field_type = None
                    for row in rows:
                        if field in row:
                            if type(row[field]) is not None:
                                field_type = type(row[field])
                            if row[field] is not None:
                                value_example = row[field]

                    if field_type is None:
                        raise ValueError("No values found for the field {}.".format(field))
                    if value_example is None:
                        raise ValueError("values: No values found for the field {}.".format(value_example))
                    types.append(field_type)
                    examples.append(value_example)


            list_of_dicts = []
            for n,field in enumerate(headers):
                tuples = [('field_name', field),
                        ('type', type_converter[types[n]]),
                        ('description',''),
                        ('example',examples[n]),
                        ('notes','')]

                list_of_dicts.append(OrderedDict(tuples))
            row1 = list_of_dicts[0]
            data_dictionary_fields = [tup for tup in row1]
            data_dictionary_path = re.sub("\.csv","-data-dictionary.csv",csv_file_path)
            with open(data_dictionary_path, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=data_dictionary_fields)

                writer.writeheader()
                writer.writerows(list_of_dicts)


if __name__ == '__main__':
    main()
