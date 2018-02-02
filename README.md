# Little Lexicographer

Whenever we publish new data on the [Western Pennsylvania Regional Data Center](https://www.wprdc.org)'s [open data portal](https://data.wprdc.org), we include a data dictionary to describe all the fields. To make this easier, I created a simple Python script that takes as a command-line argument the filename for a CSV file, scans its field values to try to infer the type, and then creates a data dictionary file (also in CSV format) with one row for each of the first file's fields, an example value for each field, and blanks for field descriptions and optional additional notes. 

```Usage:
> python lil_lex.py example.csv
```

This will generate a file in the same directory as example.csv called example-data-dictionary.csv.

Then all you have to do is check that the types are right and fill in the blanks. (Values can easily be inserted into CSVs in your favorite text editor of course, but I enjoy using [VisiData](https://github.com/saulpw/visidata) for editing CSV files since it makes viewing and manipulating CSV files in a terminal window so easy (so long as you're willing to learn some keyboard shortcuts).)

Once your data dictionary files is filled in, it's ready for uploading to CKAN.
