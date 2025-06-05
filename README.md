# member_rating
Generate a weighted list of members of an association who are proposed as (mandatory) candidates for a board election.

## Data Folder

Folder containing data files for the election process (relative to the application): `../nachwahl_data`

Expected content of `nachwahl_data`:

- `mitglieder.xlsx` - Member data
  or
- `mitglieder.tsv` - Member data in tabulator separated version (TSV) format
- `NachwahlProcedere.md` - Election procedure data as markdown file

## Usage

Run the script with the following command:

```bash
python main.py mitglieder_table.xlsx
```

## Requirements

- Python 3.8 or higher
- Required packages listed in `requirements.txt`

