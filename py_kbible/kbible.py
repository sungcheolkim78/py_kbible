"""
kbible.py - base bible object and commands
"""

import pandas as pd
import yaml
import os

__author__ = "Sungcheol Kim <sungcheol.kim78@gmail.com>"
__docformat__ = "restructuredtext en"

class KBible(object):
    """ Bible text object """

    def __init__(self, version="개역한글판성경", debug=False, **kwargs):
        """ read or parse bible text """

        self._biblelist = []
        self.add(version, **kwargs)

    def add(self, version, **kwargs):
        """ add different version """
        b = read_full_bible(version_name=version, **kwargs)
        self._biblelist.append(b)

    def bystr(self, sstr, form="pd"):
        """ extract bible verse """

        if form in ["string", "md"]:
            msg = ""
            for b in self._biblelist:
                msg = msg + extract_bystr(b, sstr, form=form) + '\n'
            return msg
        elif form == "pd":
            res = pd.DataFrame()
            for b in self._biblelist:
                res = pd.concat([res, extract_bystr(b, sstr, form="pd")], axis=0)
            return res


def bible_parser(version_name="개역한글판성경"):
    """ read bible text and return panda database
    inputs:
        version_name : available versions 개역한글판성경, 개역개정판성경
    output:
        bible panda dataframe as short version
    """

    # read bible txt file
    this_dir, this_filename = os.path.split(__file__)
    filename = os.path.join(this_dir, "data", version_name + ".txt")
    with open(filename, "r") as f:
        lines = f.readlines()

    # prepare data container
    books = []
    chapters = []
    verses = []
    texts = []

    for i, line in enumerate(lines):
        line = line.strip('\n\r')

        # check comment line
        if len(line) == 0:
            continue
        if line[0] == "#":
            continue
        if line.find(':') == -1:
            continue

        # find header
        hp = line.find(' ')
        if hp > 1 and hp < 20:
            header = line[:hp]
            text = line[hp+1:]

            # find book, chapter, verse, text
            try:
                tmp = header.split(':')[0]
                if tmp.find('.') > 0:   # english bible
                    book = tmp.split('.')[0]
                    chapter = tmp.split('.')[1]
                else:   # korean bible
                    book = ''.join(filter(str.isalpha, tmp))
                    chapter = ''.join(filter(str.isdigit, tmp))
                verse = header.split(':')[1]
            except:
                print('... header error: ({}) {}'.format(i, header))
                continue

            # convert data
            try:
                verse = int(verse)
                chapter = int(chapter)
            except:
                print("... conversion error: ({}) {} {}".format(i, verse, chapter))
                continue

            # collect
            books.append(book)
            chapters.append(chapter)
            verses.append(verse)
            texts.append(text)
        else:
            print("... unrecognized line: ({}) {}".format(i, line))

    df_bible = {'book':books, 'chapter':chapters, 'verse':verses, 'text':texts}
    idx = range(len(books))
    bible = pd.DataFrame(data=df_bible, index=idx)

    return bible


def read_full_bible(version_name="개역한글판성경", save=False):
    """ read bible version and combine book data
    inputs:
        version_name: bible version
        save: [True|False]
    output:
        bible panda dataframe
    """

    try:
        this_dir, this_filename = os.path.split(__file__)
        filename = os.path.join(this_dir, "data", version_name + ".csv.gz")
        full_bible = pd.read_csv(filename, index_col=0, compression = "gzip")
        return full_bible
    except FileNotFoundError:
        print('... generate bible database: {}'.format(filename))

    bible = bible_parser(version_name=version_name)

    listname = os.path.join(this_dir, "data", u"book_names.csv")
    table = pd.read_csv(listname, index_col=0)

    if bible['book'][0] == 'Gen':
        table['book'] = table['eng_short']
    else:
        table['book'] = table['kor_short']

    full_bible = pd.merge(bible, table, on='book', how='left')

    if save:
        full_bible.to_csv(filename, compression='gzip')

    return full_bible


def find_id(bible, book=[], chapter=[], verse=[], verb=False):
    """ find index on full bible database
    inputs:
        bible: bible panda database
        book: book names as list
        chapter: chapters as list
        verse: verses as list
        verb: [True|False] show details
    output:
        panda dataframe filtered by all combination of book, chapter, verses
    """

    isfullbible = False

    # check books
    books = set(bible['book'])
    if "code" in bible.columns:
        isfullbible = True

    if len(book) == 0:
        book = books[0]
    if isinstance(book, str):
        book = [book]

    if verb: print('... search book:{}'.format(book))
    if isfullbible:
        result = bible.loc[bible.kor.isin(book) | bible.kor_short.isin(book) | bible.eng.isin(book) | bible.eng_short.isin(book)]
    else:
        result = bible.loc[bible.book.isin(book)]

    # check chapter
    if isinstance(chapter, int):
        chapter = [chapter]
    if len(chapter) == 0:
        return result

    if verb: print('... search chapter: {}'.format(chapter))
    result = result.loc[bible.chapter.isin(chapter)]

    # check verse
    if isinstance(verse, int):
        verse = [verse]
    if len(verse) == 0:
        return result

    if verb: print('... search verse: {}'.format(verse))
    result = result.loc[bible.verse.isin(verse)]

    if len(result) > 0:
        return result
    else:
        print("... not found: {}, {}, {}".format(book, chapter, verse))
        return []


def extract_bystr(bible, sstr, form="pd"):
    """ extract verse by short search string
    inputs:
        bible: panda database of bible version
        sstr: search pattern
            - example "창3:16", "고후5:3", '요일1:1', "창세기1:1"
            - no spaces
            - one separator :
            - ',' and '-' is possible (창3:16,17) (창1:1-5)
        form: output format
            - "md" one line sentence with markdowm
            - "string" text string
            - "pd" panda dataframe
    output:
        object determined by form variable
    """

    # remove all spaces
    sstr = sstr.replace(" ", "")

    # find components
    if sstr.find(":") > 0:
        head = sstr.split(':')[0]
        verses = sstr.split(':')[1]
    else:
        head = sstr
        verses = []

    book = ''.join(filter(str.isalpha, head))
    chapter = ''.join(filter(str.isdigit, head))

    # if there is no chapter
    if len(chapter) == 0:
        chapter = []
    else:
        chapter = int(chapter)

    # check , in verse
    if len(verses) > 0:
        if verses.find(',') > 0:
            verses = verses.split(',')
        # check - in verse
        elif verses.find('-') > 0:
            start = verses.split('-')[0]
            end = verses.split('-')[1]
            try:
                verses = list(range(int(start), int(end)+1))
            except:
                print('... wrong format: {}'.format(sstr))
                return 0
        else:
            verses = [int(verses)]

        verses = [int(v) for v in verses]

    #print(book, chapter, verses)

    # return verses
    res = find_id(bible, book=book, chapter=chapter, verse=verses)
    if len(res) == 0:
        return []

    if form == "pd":
        return res
    if form == "string":
        texts, _ = remove_footnote(res['text'].values, trim=True)
        return '. '.join(texts)
    if form == "md":
        msg = "`{}` ".format(sstr)
        texts, footnotes = remove_footnote(res['text'].values, trim=False)

        if len(footnotes) > 0:
            return msg + '. '.join(texts) + '\n' + '\n'.join(footnotes)
        else:
            return msg + '. '.join(texts)

    print('... no format specified: "pd", "md", "string"')


def remove_footnote(texts, keyword="FOOTNOTE", trim=True):
    """ remove footnote """

    res = []
    footnotes = []
    i = 1

    start_word = "__a__{}__a__".format(keyword)
    end_word = "__b__{}__b__".format(keyword)

    for t in texts:
        text = str(t)
        ipos = text.find(start_word)

        # no footnote
        if ipos == -1:
            res.append(text)
            continue

        # find last footnote sign
        fpos = text.rfind(end_word)
        if trim:
            res.append(text[:ipos-1] + text[fpos+len(end_word):])
        else:
            res.append(text[:ipos-1] + "[^{}]".format(i) + text[fpos+len(end_word):])
        footnotes.append("[^{}]: {}".format(i,text[ipos+len(start_word):fpos]))
        i = i + 1

    return res, footnotes

def make_mdpage(bible, day_info, save_dir=None):
    """ print all verses in list using markdown format
    inputs:
        bible: name of version or panda dataframe
        day_info: name of day information file or yaml data
        save: [True|False]
    output:
        text strings of markdown page
    """

    # check day_info.yml file
    if isinstance(day_info, str):
        try:
            with open(day_info, "r") as f:
                day_info = yaml.load(f, yaml.BaseLoader)
        except:
            print("... file: {} parser error!".format(day_info))
            return 0

    bible_version = ""
    # check bible version
    if isinstance(bible, str):
        try:
            bible_version = "-" + bible
            bible = read_full_bible(bible)
        except:
            print("... read bible error: {}".format(bible_version[1:]))
            return 0

    msg = "# {}일차 - {}\n\n".format(day_info["day"],day_info["title"])
    msg = msg + "찬양 : {}\n\n".format(day_info["song"])
    msg = msg + "기도 : {}\n\n".format(day_info["prayer"])
    msg = msg + "요약 : {}\n\n".format(day_info["summary"])
    msg = msg + "성경 버전 : {}\n\n".format(bible_version[1:])

    for v in day_info["verses"]:
        msg = msg + '- {}\n\n'.format(extract_bystr(bible, v, form="md"))

    msg = msg + "### info\n\n"
    msg = msg + "- 성경 구절 갯수 : {}".format(len(day_info["verses"]))

    if save_dir is not None:
        filename = '{}/day{}-{}{}.md'.format(save_dir, day_info["day"], day_info["title"].replace(" ", ""), bible_version)
        with open(filename, "w") as f:
            f.write(msg)
        print('... save to {}'.format(filename))

    return msg
