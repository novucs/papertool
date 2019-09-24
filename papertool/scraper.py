import re
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from typing import (
    List,
    Tuple,
)

import arxiv
import bibtexparser
import googlesearch
import requests
import tika
from tika import parser

from papertool.journal import (
    join_authors,
    JournalReference,
    JournalType,
    sorted_references,
)

PDF_TITLE_CHECK_DEPTH = 5


def scrape_paper(paper: str, executor: ThreadPoolExecutor):
    if '/' in paper and paper.endswith('.pdf'):
        # Attempt to download and parse a pdf and its title from a potential url
        try:
            response = requests.get(paper, stream=True)
            pdf = tika.parser.from_buffer(response.raw)
            lines = pdf['content'].strip().splitlines()
            seen_caps = False
            for line, _ in zip(reversed(lines[:PDF_TITLE_CHECK_DEPTH]),
                               range(PDF_TITLE_CHECK_DEPTH)):
                if not line.strip():
                    continue
                if line.isupper():
                    seen_caps = True
                    paper = line
                if not seen_caps:
                    paper = line
        except IOError:
            pass

    # Search arxiv
    searchable_paper_name = re.sub(r'[^a-zA-Z0-9\s]+', ' ', paper).lower()
    result = next(iter(arxiv.query(f'ti:"{searchable_paper_name}"', max_results=1)), None)
    references = []

    if result:
        authors = join_authors(result['authors'])
        year = result['published_parsed'].tm_year
        title = result['title']
        journal = 'arXiv Preprint'
        volume, issue = result['id'].split('/')[-1].split('v')
        pages = None
        accessed = datetime.now().strftime('[Accessed %d %B %y]')
        url = result['pdf_url']
        references.append(JournalReference(
            authors, year, title, journal, volume, issue, pages, accessed,
            url, JournalType.ELECTRONIC))

        # Search doi if exists
        doi = result['doi']
        if doi:
            reference = scrape_doi(doi)
            if reference:
                references.append(reference)

    # Search google
    google_references, google_dois = scrape_google(paper, executor)
    references.extend(google_references)

    # Search all DOIs found from Google
    references.extend(executor.map(scrape_doi, google_dois))

    return sorted_references(list(filter(None, set(references))), paper)


def scrape_doi(doi):
    bibtex_response = requests.get(f'https://doi.org/{doi}', headers={
        'Accept': 'application/x-bibtex; charset=utf-8'
    })
    if bibtex_response.status_code == 200:
        try:
            return JournalReference.parse_bibtex(bibtex_response.text)
        except ValueError:
            pass
    return None


def scrape_google(paper: str, executor: ThreadPoolExecutor):
    urls = list(googlesearch.search(f'"bibtex" {paper}', stop=10))
    all_references = []
    all_dois = []

    for references, dois in executor.map(scrape_web_page, urls):
        all_references.extend(references)
        all_dois.extend(dois)

    return all_references, all_dois


def scrape_web_page(url: str) -> Tuple[List[JournalReference], List[str]]:
    text = requests.get(url).text

    if not text:
        return [], []

    found_at = False
    bracket_indent = 0
    raw_bibtex = ""
    raw_bibtex_list = []

    for c in text:
        raw_bibtex += c

        if found_at:
            if c == '{':
                bracket_indent += 1
                continue

            if c == '}':
                bracket_indent -= 1
                if bracket_indent == 0:
                    check = raw_bibtex.lower()
                    if 'title' in check and 'author' in check:
                        raw_bibtex_list.append(raw_bibtex)
                    found_at = False
                continue

        if c == '@':
            found_at = True
            raw_bibtex = c
            continue

    references = []

    for raw_bibtex in raw_bibtex_list:
        try:
            for bibtex in bibtexparser.loads(raw_bibtex).entries:
                references.append(JournalReference.parse_bibtex(bibtex))
        except:
            continue

    dois = re.findall(r'\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])\S)+)\b', text)
    return references, dois
