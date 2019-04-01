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
        self._versionlist = {}
        self.add(version, **kwargs)

    def add(self, version, **kwargs):
        """ add different version """
        b = read_full_bible(version_name=version, **kwargs)
        self._biblelist.append(b)
        self._versionlist[version] = len(self._biblelist) - 1

    def delete(self, version):
        """ remove version """
        if (version in self._versionlist) and (len(self._versionlist) > 1):
            i = self._versionlist[version]
            del self._versionlist[version]
            del self._biblelist[i]
        else:
            print('... not found or only have one bible version: {}'.format(version))

    def save(self, version="개역한글판성경"):
        """ save bible text as compressed csv """

        if version in self._versionlist:
            this_dir, this_filename = os.path.split(__file__)
            filename = os.path.join(this_dir, "data", version + ".csv.gz")

            b = self._biblelist[self._versionlist[version]]
            b.to_csv(filename, compression='gzip')
            print('... save file: {}'.format(filename))

    def get(self, version="개역한글판성경"):
        """ return bible as pandas """

        try:
            return self._biblelist[self._versionlist[version]]
        except:
            print('... no bible version: {}'.format(version))
            return []

    def bystr(self, sstr, form="md"):
        """ extract bible verse """

        if form == "pd":
            res = pd.DataFrame()
            for b in self._biblelist:
                res = pd.concat([res, extract_bystr(b, sstr, form="pd")], axis=0)
            return res
        else:
            msg = ""
            for b in self._biblelist:
                msg = msg + extract_bystr(b, sstr, form=form) + '\n'
            return msg

    def search(self, sstr, form="md", regex=False):
        """ search string in bible """

        res = pd.DataFrame()
        for b in self._biblelist:
            b_res_idx = b.text.str.contains(sstr, regex=regex)
            if sum(b_res_idx) > 0:
                res = pd.concat([res, b[b_res_idx]], axis=0)

        if len(res) > 0:
            return get_texts(res, form=form)
        else:
            print('... no matched results')
            return []


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

    return get_texts(res, form=form, sstr=sstr)


def get_texts(bible_pd, form="md", sstr="", sep=""):
    """ print verses using different format """

    if form == "pd":
        return bible_pd

    bible_pd.loc[:, "id"] = bible_pd.loc[:, "book"] + sep + bible_pd["chapter"].astype(str) + ":" + bible_pd["verse"].astype(str)
    bible_pd = tidy_footnote(bible_pd)

    if (len(set(bible_pd["book"])) == 1) and (sstr.find(":") == -1):
        min_v = bible_pd["verse"].min()
        max_v = bible_pd["verse"].max()
        sstr = "{}:{}-{}".format(sstr, min_v, max_v)

    if form == "string":
        if sstr == "":
            bible_pd[form] = bible_pd["id"] + " - " + bible_pd[form].astype(str)
            msg = '\n'.join(bible_pd[form].values)
        else:
            msg = sstr + ' ' + ' '.join(bible_pd[form].values)
        return msg

    if form == "md":
        if sstr == "":
            bible_pd[form] = "`" + bible_pd["id"] + "` " + bible_pd[form].astype(str)
            msg = '\n'.join(bible_pd[form].values)
        else:
            msg = '`{}` '.format(sstr) + ' '.join(bible_pd[form].values)

        if sum(bible_pd["footnote"] != "") > 0:
            return msg + '\n' + ''.join(bible_pd["footnote"].values)
        else:
            return msg

    if form == "mdlines":
        bible_pd["md"] = "`" + bible_pd["id"] + "` " + bible_pd["md"].astype(str)
        msg = '\n'.join(bible_pd["md"].values)

        if sum(bible_pd["footnote"] != "") > 0:
            return msg + '\n' + ''.join(bible_pd["footnote"].values)
        else:
            return msg

    print('... {} format is not implemented: ["pd", "md", "string"]'.format(form))
    return []


def tidy_footnote(bible_pd, keyword="FOOTNOTE"):
    """ remove footnote """

    bible_pd["md"] = bible_pd["text"]
    bible_pd["string"] = bible_pd["text"]
    bible_pd["footnote"] = ""

    start_word = "__a__{}__a__".format(keyword)
    end_word = "__b__{}__b__".format(keyword)
    fn_idx = ["a", "b", "c", "d", "e", "f"]

    # search different verses
    for i in bible_pd.index[bible_pd.text.str.contains(start_word)]:
        # search in one verse
        text = bible_pd.at[i, "text"]
        tmp = text.replace("_b_", "_a_").split(start_word)

        bible_pd.at[i, "string"] = tmp[0] + ''.join(tmp[2::2])

        # check multiple footnotes
        md = tmp[0]
        fn = ""
        for j in range(int(len(tmp)/2)):
            md = md + "[^{}{}]".format(bible_pd.at[i, "id"], fn_idx[j]) + tmp[j*2 + 2]
            fn = fn + "[^{}{}]:".format(bible_pd.at[i, "id"], fn_idx[j]) + tmp[j*2 + 1].replace("TR","") + '\n'

        bible_pd.at[i, "md"] = md
        bible_pd.at[i, "footnote"] = fn

    return bible_pd


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
