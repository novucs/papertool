import difflib
from datetime import datetime
from enum import Enum
from typing import (
    Dict,
    List,
    Optional,
)

import bibtexparser


class JournalType(Enum):
    PAPER = 0
    ELECTRONIC = 1
    PREPRINT = 2


def join_authors(authors):
    return ' and '.join((', '.join(authors[:-1]), authors[-1]))


class JournalReference:
    def __init__(
            self,
            authors: str,
            year: str,
            title: str,
            journal: str,
            volume: str,
            issue: str,
            pages: Optional[str],
            accessed: Optional[str],
            url: Optional[str],
            journal_type: JournalType
    ):

        if pages is None and journal_type == JournalType.PAPER:
            raise ValueError('Paper journal references require page numbers')

        if accessed is None and journal_type == JournalType.ELECTRONIC:
            raise ValueError('Electronic journal references require date accessed')

        self.authors = authors
        self.year = year
        self.title = title
        self.journal = journal
        self.volume = volume
        self.issue = issue
        self.pages = pages
        self.accessed = accessed
        self.url = url
        self.journal_type = journal_type

    def __repr__(self):
        if self.journal_type == JournalType.PAPER:
            return f'{self.authors} ({self.year}) {self.title}. <i>{self.journal}</i>. ' \
                   f'{self.volume} ({self.issue}), pp. {self.pages}'
        if self.journal_type == JournalType.ELECTRONIC:
            pages = f', pp. {self.pages}. ' if self.pages else '. '
            return f'{self.authors} ({self.year}) {self.title}. <i>{self.journal}</i> ' \
                   f'[online]. {self.volume} ({self.issue}){pages}{self.accessed}'
        # TODO: Figure preprint :s
        # if self.journal_type == JournalType.PREPRINT:
        #     return f'{self.authors} ({self.year}) {self.title}. <i>{self.journal}</i> ' \
        #            f'[online]. {self.volume} ({self.issue}){pages}{self.accessed}'

    @staticmethod
    def parse_bibtex(bibtex: Dict[str, str]):
        if isinstance(bibtex, str):
            bibtex = bibtexparser.loads(bibtex).entries[0]

        def format_authors(text: str) -> str:
            authors = []
            for name in text.split(' and '):
                forename, *_, surname = name.split()
                if ',' in forename:
                    surname, forename = forename.rstrip(','), surname
                authors.append(f'{surname}, {forename[0]}.')
            if len(authors) == 1:
                return authors[0]
            return join_authors(authors)

        try:
            authors = format_authors(bibtex['author'])
            year = bibtex['year']
            title = bibtex['title']
            journal = bibtex.get('journal') or bibtex['series']
            volume = bibtex['volume']
            issue = bibtex.get('issue') or bibtex.get('number', 1)
            pages = bibtex.get('pages', '').replace("--", "-") or None
            accessed = datetime.now().strftime('[Accessed %d %B %y]')
            url = bibtex.get('pdf') or bibtex.get('url')
            journal_type = JournalType.PAPER if url is None else JournalType.ELECTRONIC
            return JournalReference(
                authors, year, title, journal, volume, issue, pages, accessed,
                url, journal_type)
        except KeyError as exception:
            print('Possibly invalid Bibtex found', bibtex, exception)
            raise ValueError('Bibtex not complete enough for '
                             'UWE Harvard referencing')

    def __eq__(self, other):
        return self.authors == other.authors and \
               self.year == other.year and \
               self.title == other.title and \
               self.journal == other.journal and \
               self.volume == other.volume and \
               self.issue == other.issue and \
               self.pages == other.pages and \
               self.accessed == other.accessed and \
               self.url == other.url and \
               self.journal_type == other.journal_type

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))


def sorted_references(
        references: List[JournalReference],
        term: str,
) -> List[JournalReference]:
    def compare_by_title(reference):
        return difflib.SequenceMatcher(a=reference.title.lower(), b=term.lower()).ratio()

    return sorted(references, reverse=True, key=compare_by_title)
