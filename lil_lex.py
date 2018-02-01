import re, sys, csv

from collections import OrderedDict

type_hierarchy = {None: -1, 'text': 0, 'bool': 1, 'int': 2, 'float': 3} # Ranked by test stringency

def test_type(value,candidate):
    if value =='':
        return True
    if candidate == 'text':
        try:
            x = str(value)
        except:
            return False
        return True

    if candidate == 'int':
        if re.match('-?\d+',value) is not None:
            return True
        return False
        #try:
        #    x = int(value)
        #except:
        #    return False
        #return True

    if candidate == 'float':
        if re.match('-?\d*\.\d+',value) is not None or re.match('-?\d+\.\d*',value) is not None:
            return True
        return False
        #try:
        #    x = float(value)
        #except:
        #    return False
        #return True

    if candidate == 'bool':
        if value in [0, '0', False, 'False', 'false', 1, '1', True, 'True', 'true']:
            return True
        return False

    # Dates, times, and datetimes are more difficult to deal with.
    # I'll also save JSON for later.

def choose_type(options):
    selection = None
    for option in options:
        if type_hierarchy[option] > type_hierarchy[selection]:
            selection = option
    return selection

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
                rows = list(reader) # This is necessary since if you just iterate over 
                # the reader once, you can't use it again without doing something.
                for n,field in enumerate(headers):
                    field_type = None
                    value_example = None
                    type_options = ['text','int','float','bool'] #'json','timestamp','time','date']

                    for row in rows:
                        if field in row:
                            if row[field] is not None and value_example is None:
                                value_example = row[field]
                            # Type elimination by brute force
                            if row[field] is not None:
                                for option in type_options: 
                                    if not test_type(row[field],option):
                                        type_options.remove(option)
                    field_type = choose_type(type_options)
                    print(field,field_type,type_options)
                    if field_type is None:
                        raise ValueError("No values found for the field {}.".format(field))
                    if value_example is None:
                        raise ValueError("values: No values found for the field {}.".format(value_example))
                    types.append(field_type)
                    examples.append(value_example)


            # Remove the _id field added by CKAN, if it's there.
            if '_id' in headers:
                headers.remove('_id')
            list_of_dicts = []
            for n,field in enumerate(headers):
                tuples = [('field_name', field),
                        ('type', types[n]),
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
