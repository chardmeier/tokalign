# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import logging
import sys

import tokalign

from bs4 import BeautifulSoup
from pathlib import Path


#logger = logging.getLogger(__name__)


def read_basedata(mmax, doc):
    bd = mmax / 'Basedata' / (doc + '_words.xml')
    with bd.open() as f:
        soup = BeautifulSoup(f.read(), 'xml')
    toks = [w.string for w in soup.find_all('word')]
    idx = [w['id'] for w in soup.find_all('word')]
    return toks, idx


def convert_level(inxml, alig, idx1, idx2, outmrkdir):
    logging.info('Converting level ' + inxml.name)
    with inxml.open() as f:
        soup = BeautifulSoup(f.read(), 'xml')

    alig_lookup = {s: t for s, t in alig if s is not None and t is not None}
    id_lookup = {x: i for i, x in enumerate(idx1)}

    for mrk in soup.find_all('markable'):
        oldspan = mrk['span']

        unaligned = False
        oldranges = oldspan.split(',')
        newranges = []
        for r in oldranges:
            nr = [alig_lookup.get(id_lookup[x]) for x in r.split('..')]
            if None in nr:
                unaligned = True
                break
            else:
                newranges.append('..'.join(idx2[x] for x in nr))

        if not unaligned:
            newspan = ','.join(newranges)
            logging.debug('Converted ' + oldspan + ' to ' + newspan)
            mrk['span'] = newspan
        else:
            logging.warning('Discarding unaligned markable ' + mrk['id'])
            mrk.decompose()

    outxml = outmrkdir / inxml.name
    with outxml.open(mode='w') as f:
        f.write(soup.prettify())


def main():
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    #logger.setLevel(logging.DEBUG)

    if len(sys.argv) != 3:
        print("Usage: import_mmax_annot.py mmax1 mmax2", file=sys.stderr)
        sys.exit(1)

    mmax1 = Path(sys.argv[1])
    mmax2 = Path(sys.argv[2])

    docs1 = {x.name[:-5] for x in mmax1.iterdir() if x.name.endswith('.mmax')}
    docs2 = {x.name[:-5] for x in mmax2.iterdir() if x.name.endswith('.mmax')}

    if not docs2.issubset(docs1):
        print("MMAX bundles don't match.", file=sys.stderr)
        print(docs1, file=sys.stderr)
        print(docs2, file=sys.stderr)
        sys.exit(1)

    for doc in sorted(docs2):
        logging.info('Reading document ' + doc)
        txt1, idx1 = read_basedata(mmax1, doc)
        txt2, idx2 = read_basedata(mmax2, doc)

        logging.info('Aligning document...')
        alig = tokalign.align(txt1, txt2)

        inmrkdir = mmax1 / 'markables'
        outmrkdir = mmax2 / 'markables'
        levels = [x for x in inmrkdir.iterdir()
                    if x.name.startswith(doc + '_') and x.name.endswith('_level.xml')
                    and not x.name.endswith('_sentence_level.xml')]
        for l in levels:
            convert_level(l, alig, idx1, idx2, outmrkdir)


if __name__ == "__main__":
    main()
