# Little Lexicographer

### Generating data dictionaries
Whenever we publish new data on the [Western Pennsylvania Regional Data Center](https://www.wprdc.org)'s [open data portal](https://data.wprdc.org), we include a data dictionary to describe all the fields. To make this easier, I created a simple Python script that takes as a command-line argument the filename for a CSV file, scans its field values to try to infer the type, and then creates a data dictionary file (also in CSV format) with one row for each of the first file's fields, an example value for each field (not currently supported by the integrated data dictionary on data.wprdc.org), and blanks for field labels and optional additional description.

If example.csv contains this text:

```
numbers,letters,constants,truth_values
34,y,2.7182818284,True
5001,A,3.141592653589793,false
-1,k,-1.61803,
```

corresponding to this table:

numbers|letters|constants|truth_values
-------|-------|---------|------------
34|y|2.7182818284|True
5001|A|3.141592653589793|false
-1|k|-1.61803|

then running lil_lex.py on it like so,

```
> python lil_lex.py example.csv
```

will generate a file in the same directory as example.csv called example-data-dictionary.csv. Its tabular form looks kind of like this:

column|type|label|example|description
----------|----|-----------|-------|-----
numbers|int||34|"This is an example note I added, just to demonstrate the importance of putting quotes around any field value that contains a comma, lest it be interpreted as more fields than one."
letters|text||y|
constants|float||2.7182818284|
truth_values|bool||True|

Then all you have to do is check that the types are right and fill in the blanks. (Values can easily be inserted into CSVs in your favorite text editor of course, but I enjoy using [VisiData](https://github.com/saulpw/visidata) for editing CSV files since it makes viewing and manipulating CSV files in a terminal window so easy (so long as you're willing to learn some keyboard shortcuts).)

column|type|label|example|description
----------|----|-----------|-------|-----
numbers|int|This field contains integers.|34|"This is an example note I added, just to demonstrate the importance of putting quotes around any field value that contains a comma, lest it be interpreted as more fields than one."
letters|text|Single letters, randomly sampled from the alphabet.|y|
constants|float|These are all well-known mathematical constants.|2.7182818284|
truth_values|bool|Boolean values.|True|

Once your data dictionary file is filled in, it's ready for uploading to CKAN.

NOTE: These field names (`column`, `type`, `label`, and `description`) correspond to those generated when you download the integrated data dictionary from data.wprdc.org through the Web interface. However, internally and in the API, CKAN refers to the `description` field as `notes`. Also (as mentioned above), the `example` field is not used at al by the CKAN integrated data dictionary at present. I've left it in this script because it's convenient for the user of the script to see example values for each field.

### Uploading integrated data dictionaries

Say you have a data dictionary in the above format (with fields `column`, `label`, and `description`) as a CSV file and want to upload it to the CKAN integrated data dictionary for a particular existing resource. Do the following:

1) Configure your credentials.py script to look something like this:

```
API_key = 'long-string-of-alphanumeric-characters-you-got-from-your-data.wprdc.org-user-account'
site = 'https://data.wprdc.org'
```
2) Run this script:

> python upload_data_dictionary.py path-to-your-data-dictionary.csv \<CKAN-resource-ID-for-table-of-interest\>

The data dictionary should be uploaded, filling in `label` and `description` values for the corresponding fields.

If you want to attempt to set types of some of the fields, add a `type_override` column to your data dictionary and run the script.
Then you have to log in to your CKAN account on data.wprdc.org, find the resource, click on the 'Manage' button, switch to the 'Datastore' tab, and push the 'Upload to Datastore' button. You can monitor the Datastore upload progress by reloading that page, but eventually the type overrides should take effect.

### Cloning integrated data dictionaries

Run

> python clone_data_dictionary.py \<CKAN-source-resource-ID\> \<CKAN-destination-resource-ID\>

to apply the `label` and `description` values from the source resource to any corresponding fields in the destination resource.
