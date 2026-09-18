### pip install bibtexparser iso4
import argparse
import re
import bibtexparser
import iso4
import nltk

# Auto-download wordnet if missing
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


def is_title_already_normalized(title: str) -> bool:
    """Checks if title already contains LaTeX curly braces around capitalized words."""
    return "{" in title and "}" in title


def is_author_already_normalized(author_str: str) -> bool:
    """
    Checks if given names are already reduced to initials.
    Matches formats like 'C. Liu', 'J. D. Smith', or 'Liu, C.'
    """
    authors = author_str.split(" and ")
    for author in authors:
        author = author.strip()
        # Extract first/given names
        if "," in author:
            given_names = author.split(",", 1)[1].strip().split()
        else:
            parts = author.rsplit(" ", 1)
            if len(parts) == 1:
                continue
            given_names = parts[0].strip().split()

        # If any given name is longer than 2 chars (e.g., "Chang" vs "C."), it's not normalized
        for name in given_names:
            clean = re.sub(r"[{}']", "", name)
            if len(clean) > 2 or (len(clean) == 1 and not clean.isupper()):
                return False
    return True


def is_journal_already_normalized(journal_name: str) -> bool:
    """
    Checks if a journal is already abbreviated (contains dots like 'J. Fluid Mech.')
    or is a single-word journal (e.g., 'Nature', 'Science').
    """
    words = journal_name.split()
    # Single-word journals don't need abbreviation
    if len(words) == 1:
        return True
    # If multi-word journal already has abbreviations with periods, treat as normalized
    return any("." in word for word in words)


def fix_title_casing(title: str) -> str:
    if is_title_already_normalized(title):
        return title

    words = title.split()
    fixed_words = []
    for word in words:
        if word.startswith("{") and word.endswith("}"):
            fixed_words.append(word)
            continue
        if any(c.isupper() for c in word if c.isalpha()) and not word.startswith("\\"):
            match = re.match(r"^(\W*)(.*?)([\W]*)$", word)
            if match:
                prefix, core, suffix = match.groups()
                fixed_words.append(f"{prefix}{{{core}}}{suffix}")
            else:
                fixed_words.append(f"{{{word}}}")
        else:
            fixed_words.append(word)
    return " ".join(fixed_words)


def shorten_author_names(author_str: str) -> str:
    if is_author_already_normalized(author_str):
        return author_str

    authors = author_str.split(" and ")
    shortened_authors = []

    for author in authors:
        author = author.strip()
        if not author:
            continue

        if "," in author:
            parts = author.split(",", 1)
            last = parts[0].strip()
            firsts = parts[1].strip().split()
        else:
            parts = author.rsplit(" ", 1)
            if len(parts) == 1:
                shortened_authors.append(author)
                continue
            firsts = parts[0].strip().split()
            last = parts[1].strip()

        initials = []
        for name in firsts:
            clean_name = re.sub(r"[{}']", "", name)
            if clean_name:
                initials.append(f"{clean_name[0]}.")

        short_name = f"{' '.join(initials)} {last}".strip()
        shortened_authors.append(short_name)

    return " and ".join(shortened_authors)

def process_bib_file(input_file: str, output_file: str, remove_titles: bool = False):
    library = bibtexparser.parse_file(input_file)

    for entry in library.entries:
        # Title processing
        if "title" in entry:
            if remove_titles:
                del entry["title"]
            else:
                entry["title"] = fix_title_casing(entry["title"])

        # Author processing
        if "author" in entry:
            entry["author"] = shorten_author_names(entry["author"])

        # Journal processing
        if "journal" in entry:
            raw_journal = entry["journal"].strip("{} ")
            if not is_journal_already_normalized(raw_journal):
                entry["journal"] = iso4.abbreviate(raw_journal)

    bibtexparser.write_file(output_file, library)
    print(f"Processed {input_file} -> saved to {output_file} (Remove Titles: {remove_titles})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and normalize BibTeX files.")
    parser.add_argument("-i", "--input", default="refs.bib", help="Input .bib file")
    parser.add_argument("-o", "--output", default="refs_cleaned.bib", help="Output .bib file")
    parser.add_argument(
        "--no-titles",
        action="store_true",
        help="Remove all titles from BibTeX entries (e.g., for PRL/FRL formats)",
    )

    args = parser.parse_args()
    process_bib_file(args.input, args.output, remove_titles=args.no_titles)