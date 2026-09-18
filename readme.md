This script cleans and normalizes BibTeX files for journal publication:

- Standard run (keeps and protects titles):
```Bash
python3 clean_bib.py -i refs.bib -o refs_cleaned.bib
```

- For journals like PRL/FRL (strips all titles):
```Bash
python3 clean_bib.py -i refs.bib -o refs_cleaned.bib --no-titles
```