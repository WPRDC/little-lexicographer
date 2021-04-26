import re, sys, csv

from collections import OrderedDict, defaultdict
from dateutil import parser

type_hierarchy = {None: -1, 'text': 0, 'bool': 1, 'int': 2, 'float': 3, 'datetime': 4, 'date': 4} # Ranked by test stringency

def test_type(value,candidate):
    """Return True if the value might be of type candidate and False only if it is
    definitely not of type candidate."""
    if value in ['', 'NA', 'N/A']:
        return True
    if candidate == 'datetime':
        try:
            x = parser.parse(value)
            if x.isoformat() == value:
                #print(f"{value} is a datetime.")
                return True
            else:
                #print(f"{value} is NOT a datetime.")
                return False
        except:
            #print(f"{value} is NOT a datetime.")
            return False

    if candidate == 'date':
        try:
            x = parser.parse(value)
            if x.date().isoformat() == value:
                #print(f"{value} is a date.")
                return True
            else:
                #print(f"{value} is NOT a date")
                return False
        except:
            #print(f"{value} is NOT a date.")
            return False

    if candidate == 'text':
        try:
            x = str(value)
        except:
            return False
        return True

    if candidate == 'int':
        if re.match('^-?\d+$',value) is not None:
            return True
        return False
        #try:
        #    x = int(value)
        #except:
        #    return False
        #return True

    if candidate == 'float':
        if re.match('^-?\d*\.\d+$',value) is not None or re.match('^-?\d+\.\d*$',value) is not None:
            return True
        if re.match('^-?\d+$', value) is not None: # Integers can be valid float values.
            return True
        # Examples of scientific notation to deal with: 3e+05, 2e-04
        if re.match('^-?\d\.\d+[eE][+-]*\d+$', value) is not None or re.match('^-?\d+[eE][+-]*\d+$',value) is not None:
            print(f"{value} looks like it is in scientific notation!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
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

def date_or_datetime(options,values):
    # Distinguishing between dates and datetimes could be done on length, but data that comes in like
    # 2017-04-13 00:00 (with all times equal to midnight) are actually dates.
    if all([len(v) <= 10 for v in values]): # len('2019-04-13') == 10
        return 'date'
    for v in values:
        if v not in ['', 'NA', 'N/A']:
            dt = parser.parse(v)
            if not(dt.hour == dt.minute == dt.second == 0):
                return 'datetime'
    return 'date'

def choose_type(options, values, fieldname):
    selection = None
    for option in options:
        if type_hierarchy[option] > type_hierarchy[selection]:
            selection = option

    # Distinguishing between dates and datetimes could be done on length, but data that comes in like
    # 2017-04-13 00:00 (with all times equal to midnight) are actually dates.
    if selection in ['datetime', 'date']:
        selection = date_or_datetime(options,values)

    if fieldname.lower() in ['zip', 'zipcode', 'zip_code', 'zip code']:
        if selection == 'int':
            return 'text'

    return selection

base_schema_type = {'text': 'String',
        'int': 'Integer',
        'float': 'Float',
        'bool': 'Boolean',
        'date': 'Date',
        'datetime': 'Datetime'}

types_no_integers = dict(base_schema_type)
types_no_integers['int'] = 'String'

# Dates, datetimes, and booleans need to be inferred.

def detect_case(s):
    if s == s.upper():
        return 'upper'
    if re.sub("[^a-zA-Z0-9]+","_",s.lower()) == s:
        return 'snake_case'
    sp = re.sub("[^a-zA-Z0-9]+","_",s)
    words = sp.split("_")
    if all([word == word.capitalize() for word in words]):
        return 'capitalized'
    if re.match('([A-Z0-9]*[a-z][a-z0-9]*[A-Z]|[a-z0-9]*[A-Z][A-Z0-9]*[a-z])[A-Za-z0-9]*',s) is not None:
        return 'camelCase'
    return 'Unknown' # Work on detecting camelCase

def camelCase_to_snake_case(s):
    REG = r"(.+?)([A-Z])"
    def snake(match):
        return match.group(1).lower() + "_" + match.group(2).lower()
    t = re.sub(REG, snake, s, 0)
    u = re.sub('\s+_*', '_', t)
    return u

def snake_case(s):
    inferred_case = detect_case(s)
    if inferred_case in ['upper','capitalized','snake_case']:
        return re.sub("[^a-zA-Z0-9]+","_",s.lower())
    if inferred_case in ['camelCase']:
        return camelCase_to_snake_case(s)
    best_guess = re.sub("[^a-zA-Z0-9]+","_",s.lower())
    #print("While this function is unnsure how to convert '{}' to snake_case, its best guess is {}".format(s,best_guess))
    return best_guess

def is_unique(xs):
    if len(xs) > len(set(xs)):
        return False
    return True

def args(field, nones, maintain_case):
    arg_list = []
    arg_list.append(f"load_from='{field}'.lower()")
    if maintain_case:
        arg_list.append(f"dump_to='{snake_case(field)}'")
    else:
        arg_list.append(f"dump_to='{snake_case(field.lower())}'")
    if nones != 0:
        arg_list.append('allow_none=True')
    return ', '.join(arg_list)

def main():
    if len(sys.argv) < 2:
        print("Please specify the name of the CSV file for which you want to generate")
        print('a data dictionary as a command-line argument. For example:')
        print('      > python lil_lex.py robot_census.csv')
    else:
        maintain_case = False
        no_integers = False
        if len(sys.argv) > 2:
            if 'maintain' in sys.argv[2:]:
                maintain_case = True
            if 'no_ints' in sys.argv[2:]:
                no_integers = True
            if 'no_integers' in sys.argv[2:]:
                no_integers = True

        csv_file_path = sys.argv[1]
        if re.search('\.csv$', csv_file_path) is None:
            print('This whole fragile thing falls apart if the file name does not end in ".csv". Sorry.')
        else:
            with open(csv_file_path) as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                print(headers)
                examples = []
                types = []
                none_count = defaultdict(int)
                parameters = defaultdict(lambda: defaultdict(bool))

                rows = list(reader) # This is necessary since if you just iterate over
                # the reader once, you can't use it again without doing something.
                # Remove the _id field added by CKAN, if it's there.
                if '_id' in headers:
                    headers.remove('_id')
                for n,field in enumerate(headers):
                    field_type = None
                    value_example = None
                    type_options = ['text','int','float','bool','datetime','date'] #'json','time']

                    for row in rows:
                        if field in row:
                            if row[field] in [None,'']:
                                none_count[n] += 1
                            if row[field] not in [None,''] and value_example is None:
                                value_example = row[field]
                            # Type elimination by brute force
                            if row[field] is not None:
                                for option in type_options:
                                    if not test_type(row[field],option):
                                        type_options.remove(option)
                    field_values = [row[field] for row in rows]
                    field_type = choose_type(type_options, field_values, field)
                    parameters['unique'][field] = is_unique(field_values)
                    print("{} {} {} {}".format(field, field_type, type_options, "   ALL UNIQUE" if parameters['unique'][field] else "    "))
                    if field_type is None:
                        print("No values found for the field {}.".format(field))
                    if value_example is None:
                        print("values: No values found for the field {}.".format(field))
                        parameters['empty'][field] = True # Defaults to False because of the defaultdict.
                        field_type = 'text' # Override any other field_type and use text when no value was found.
                    examples.append(value_example)
                    types.append(field_type)

            print("\n\nEMPTY FIELDS: {}".format([field for field in parameters['empty'] if parameters['empty'][field]]))
            print("POTENTIAL PRIMARY KEY FIELDS: {}".format([field for field in parameters['unique'] if parameters['unique'][field]]))


            list_of_dicts = []
            for n,field in enumerate(headers):
                tuples = [('column', field),
                        ('type', types[n]),
                        ('label',''),
                        ('description',''),
                        ('example',examples[n])]

                list_of_dicts.append(OrderedDict(tuples))
            row1 = list_of_dicts[0]
            data_dictionary_fields = [tup for tup in row1]
            data_dictionary_path = re.sub("\.csv","-data-dictionary.csv",csv_file_path)
            with open(data_dictionary_path, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=data_dictionary_fields)
                writer.writeheader()
                writer.writerows(list_of_dicts)

            ### ETL Wizard functionality: Generate Marshamallow schema for ETL jobs
            print("\n\n *** *** ** *  *   * ** *      * ** ***** * *   *")
            schema_type = base_schema_type
            if no_integers: # Lots of fields are coded as integers, but we want to switch them
                # to strings because they are just ID numbers that one should not do math with (like ward IDs).
                print("Coercing all integer fields to strings, since so many such fields are not actual counts.")
                schema_type = types_no_integers

            for n,field in enumerate(headers):
                s = f"{snake_case(field)} = fields.{schema_type[types[n]]}({args(field, none_count[n], maintain_case)})"
                print(s)

            # [ ] Infer possible primary-key COMBINATIONS.
            # [ ] Detect field names that need to be put in load_from arguments.
                # * Sense whether Marshmallow can convert source field name to snake_case name (exceptions?)

if __name__ == '__main__':
    main()
