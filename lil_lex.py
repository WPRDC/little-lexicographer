import re, sys, csv, pprint

from icecream import ic
from beartype import beartype
from typing import Tuple

from collections import OrderedDict, defaultdict
from dateutil import parser

type_hierarchy = {None: -1, 'text': 0, 'bool': 1, 'int': 2, 'float': 3, 'datetime': 4, 'date': 4} # Ranked by test stringency

def test_type(value,candidate):
    """Return True if the value might be of type candidate and False only if it is
    definitely not of type candidate."""
    if value in ['', 'NA', 'N/A', 'NULL']:
        return True
    if candidate == 'datetime':
        try:
            x = parser.parse(value)
            if x.isoformat() == value:
                #print(f"{value} is a datetime.")
                return True
            elif x.isoformat() == re.sub(' ', 'T', value): # Handle datetimes of the form "2021-05-12 21:52:00"
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
            if value[0] == '0' and value.strip() != '0' and '.' not in value:
                return False # Avoid reporting strings
            # that start with '0' as potential integers.
            # These should stay as strings.
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
        # Even if it doesn't contain a decimal point, it could be an integer, and an integer
        # could occur in a column that is mostly floats (where the type of the column should
        # be float).
        ## The section below can let integers pass, but this creates false positives, misidentifying all
        ## integer fields as floats. Instead, we need to restructure the whole process to flip a
        ## field to a float if it's all integers except for one value which is identified as a float.

        ## if re.match('^-?\d+$',value) is not None:
        ##     if value[0] != '0' or value.strip() == '0':
        ##         return True
        # Examples of scientific notation to detect: 3e+05, 2e-04
        if re.match('^-?\d\.\d+[eE][+-]*\d+$', value) is not None or re.match('^-?\d+[eE][+-]*\d+$',value) is not None:
            print(f"{value} looks like it is in scientific notation! Because of the way the float type works, it's probably best to keep this as a string to avoid mangling precision. [Actually, this is a judgment call that depends on the situation. Marshmallow WILL convert 2e-4 to 0.0002.]")
            return False

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
    if all([v is None or len(v) <= 10 for v in values]): # len('2019-04-13') == 10
        return 'date'
    for v in values:
        if v not in ['', 'NA', 'N/A', 'NULL', None]:
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

    if fieldname.lower() in ['zip', 'zipcode', 'zip_code', 'zip code'] or 'zip_code' in fieldname.lower() or 'zip code' in fieldname.lower():
        if selection == 'int':
            return 'text'

    if re.search('_id$', fieldname.lower()) is not None: # If it's an ID interpreted as an integer,
        if selection == 'int':                           # force it to be a string.
            return 'text'

    if fieldname.lower() in ['geoid', 'id']: # If it's an ID interpreted as an integer,
        if selection == 'int':                           # force it to be a string.
            return 'text'

    return selection

base_schema_type = {'text': 'String',
        'int': 'Integer',
        'float': 'Float',
        'bool': 'Boolean',
        'date': 'Date',
        'datetime': 'DateTime'}

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

def handle_forbidden_characters(s):
    return re.sub('[\/:]', '_', s)
    # Maybe the periods need to be presevered in the load_from part
    # because of rocket-etl's schema/source comparisons?

def snake_case(s, maintain_case=False):
    s = handle_forbidden_characters(s)
    if maintain_case:
        return re.sub("[^a-zA-Z0-9]", "_", s) # Change each such character to an underscore to better match
        # the form of the original field name (which is needed by marshmallow for some unknown reason).
    inferred_case = detect_case(s)
    s = re.sub("[,-]", '_', s)
    if inferred_case in ['upper', 'capitalized', 'snake_case', 'Unknown', 'camelCase']:
        s = re.sub("[^a-zA-Z0-9.#\ufeff]", "_", s.lower())
#    elif inferred_case in ['camelCase']:
#        s = camelCase_to_snake_case(s).lower()
    else:
        s = best_guess = re.sub("[^a-zA-Z0-9#\ufeff]", "_", s.lower())
        #print("While this function is unnsure how to convert '{}' to snake_case, its best guess is {}".format(s,best_guess))
    return s

def intermediate_format(s):
    # This function attempts to take the original field name and return
    # Marshmallow-ized version of it.
    return re.sub('\s+', '_', s).lower()

def eliminate_extra_underscores(s):
    s = re.sub('_+', '_', s)
    s = re.sub('^_', '', s)
    return re.sub('_$', '', s)

def eliminate_BOM(s):
    # It is reputedly possible to work around the BOM character
    # if one loads the file with a utf-sig-8 encoding, but I have
    # not gotten that to work, so I'm selectively eliminating it
    # to preserve it in the load_to part of the schema but
    # get ride of it elsewhere.
    return re.sub(u'\ufeff', '', s)

def convert_dots(s):
    return re.sub('[.]', '_', s) # We want dots in the load_from
    # part, but not the dump_to part or the variable name.

def is_unique(xs):
    if len(xs) > len(set(xs)):
        return False
    return True

def dump_to_format(field, maintain_case=False):
    field = convert_dots(eliminate_BOM(field))
    return eliminate_extra_underscores(snake_case(field, maintain_case))

@beartype
def args(field: str, nones: int, maintain_case: bool) -> Tuple[str, str]:
    arg_list = []
    arg_list.append(f"load_from='{snake_case(field)}'")
    if maintain_case:
        dump_to = dump_to_format(field, maintain_case)
    else:
        dump_to = dump_to_format(field.lower())
    arg_list.append(f"dump_to='{dump_to}'")
    if nones != 0:
        arg_list.append('allow_none=True')
    return ', '.join(arg_list), dump_to

def main():
    if len(sys.argv) < 2:
        print("Please specify the name of the CSV file for which you want to generate")
        print('a data dictionary as a command-line argument. For example:')
        print('      > python lil_lex.py robot_census.csv')
    else:
        maintain_case = False
        no_integers = False
        analyze_only = False
        if len(sys.argv) > 2:
            if 'maintain' in sys.argv[2:]:
                maintain_case = True
            if 'no_ints' in sys.argv[2:]:
                no_integers = True
            if 'no_integers' in sys.argv[2:]:
                no_integers = True
            if 'analyze' in sys.argv[2:]:
                analyze_only = True

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
                fix_nas = defaultdict(lambda: False)
                value_distribution = defaultdict(lambda: defaultdict(int))

                for n,field in enumerate(headers):
                    field_type = None
                    value_example = None
                    type_options = ['text', 'int', 'float', 'bool', 'datetime', 'date'] #'json', 'time']
                    excluded_types = []

                    for row in rows:
                        #if len(type_options) == 1: # This is an optimization that would speed up
                        #    break # type detection, BUT it would miss some none values. A correct
                        # none_count requires checking all values.
                        type_candidates = [x for x in type_options if x not in excluded_types]

                        if field in row:
                            value_distribution[field][row[field]] += 1
                            if row[field] in [None, '', 'NA', 'NULL']:
                                none_count[n] += 1
                            if row[field] not in [None, '', 'NA', 'NULL'] and value_example is None:
                                value_example = row[field]
                            # Type elimination by brute force
                            if row[field] is not None:
                                for option in type_candidates:
                                    if not test_type(row[field], option):
                                        excluded_types.append(option)

                                        # [ ] This type-detection scheme fails to detect non-strings when 'NA' values are present.
                    field_values = [row[field] for row in rows]
                    type_candidates = [x for x in type_options if x not in excluded_types]
                    field_type = choose_type(type_candidates, field_values, field)

                    if 'NA' in field_values or 'NULL' in field_values:
                        fix_nas[field] = True
                    parameters['unique'][field] = is_unique(field_values)
                    print("{} {} {} {}".format(field, field_type, type_candidates, "   ALL UNIQUE" if parameters['unique'][field] else "    "))
                    if field_type is None:
                        print("No values found for the field {}.".format(field))
                    if value_example is None:
                        print("values: No values found for the field {}.".format(field))
                        parameters['empty'][field] = True # Defaults to False because of the defaultdict.
                        field_type = 'text' # Override any other field_type and use text when no value was found.
                    examples.append(value_example)
                    types.append(field_type)

            print(f"#### VALUE DISTRIBUTION BY FIELD ####")
            single_value_fields = {}
            for field, dist in value_distribution.items():
                if len(dist) == 1:
                    value = list(dist.keys())[0]
                    if value not in [None, '', 'NA', 'NULL']:
                        single_value_fields[field] = value
                if len(dist) <= 5:
                    print(f"{field}: {dict(dist)} {'<============================' if len(dist) < 2 else ''}")
                else:
                    max_key = max(dist, key=dist.get)
                    print(f'{field}: {max_key} ({dist[max_key]} rows) + {len(dist) - 1} other values')

            print("\n\nEMPTY FIELDS: {}".format([field for field in parameters['empty'] if parameters['empty'][field]]))
            print(f"SINGLE-VALUE FIELDS: {single_value_fields}")
            print("POTENTIAL PRIMARY KEY FIELDS: {}".format([field for field in parameters['unique'] if parameters['unique'][field]]))

            if not analyze_only:
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

                dump_tos = []
                for n,field in enumerate(headers):
                    arg_string, dump_to = args(field, none_count[n], maintain_case)
                    s = f"{convert_dots(eliminate_BOM(snake_case(field)))} = fields.{schema_type[types[n]]}({arg_string})"
                    print(pprint.pformat(s, width=999).strip('"'))

                    if dump_to in dump_tos:
                        raise ValueError("That list dump_to name conflicts with one that's already in the schema!")
                    dump_tos.append(dump_to)

                tab = " "*4
                print(f"\nclass Meta:\n{tab}ordered = True\n")
                fields_with_nas = [f"'{intermediate_format(field)}'" for field, has_na in fix_nas.items() if has_na]
                print(f"@pre_load\ndef fix_nas(self, data):\n{tab}fields_with_nas = [{', '.join(fields_with_nas)}]\n{tab}for f in fields_with_nas:\n{tab*2}if data[f] in ['NA', 'NULL']:\n{tab*3}data[f] = None\n")

            # [ ] Infer possible primary-key COMBINATIONS.
            # [ ] Detect field names that need to be put in load_from arguments.
                # * Sense whether Marshmallow can convert source field name to snake_case name (exceptions?)

if __name__ == '__main__':
    main()
