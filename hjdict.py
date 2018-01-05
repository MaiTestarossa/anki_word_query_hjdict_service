# -*- coding:utf-8 -*-#
import re
import urllib2
import urllib
import types
import xml.etree.ElementTree
from bs4.BeautifulSoup import BeautifulSoup
import ssl
import sys
from aqt.utils import showInfo, showText
from .base import WebService, export, with_styles, register
from ..utils import ignore_exception


@register(u'沪江小D')
class hjdict(WebService):
    def __init__(self):
        super(hjdict, self).__init__()

    def _get_content(self):
        # 不知道如何处理非英文字符，没有例子，stackoverflow怎么解决就怎么抄
        reload(sys)
        sys.setdefaultencoding('utf8')

        # 沪江https会报错，不知原理，google后写下这段
        ssl.match_hostname = lambda cert, hostname: True

        url = 'https://www.hjdict.com/jp/jc/' + urllib2.quote(self.word.encode('utf-8'))

        # 沪江需要请求头，因为它会判断如果是手机浏览器就逼你下app
        request = urllib2.Request(url, headers={"Accept-Language": "en-US,en;q=0.5",
                                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"})
        contents = urllib2.urlopen(request).read()
        soup = BeautifulSoup(contents)

        #变量大小写规范不管了，之前抄不知道日本人还是韩国人的anki weblio爬虫插件，里面有大写就跟着大写了
        NetDicBody = soup.find('div', class_="word-details")
        if type(NetDicBody) == types.NoneType:
            errorMsg = '查无此词'
            return self.cache_this({'expressions': '', 'Meaning':'','phonetic': '','mp3':'',
              'sentences': '', 'sentence_trans': '', 'status': errorMsg})
        if not isinstance(NetDicBody.find('header', class_='word-details-pane-header-multi'), types.NoneType):
            errorMsg = '一词多义'
            return self.cache_this({'expressions': '', 'Meaning':'','phonetic': '','mp3':'',
              'sentences': '', 'sentence_trans': '', 'status': errorMsg})


        Expression = NetDicBody.find('div', 'word-text').h2.string
        Pronounces = NetDicBody.find('div', 'pronounces').span.string[1:-1]
        mp3 = NetDicBody.find('span', 'word-audio').get('data-src')

        Meaning = ''
        Poses = NetDicBody.find('div', 'simple').find_all("span", class_=None)

        MeaningRawRaw = NetDicBody.find_all('span', 'simple-definition')
        # 用来去除例句多余空格，这里不知道怎么处理，随便抄了几段处理的代码重复操作几遍，写的很难看
        for s in range(len(MeaningRawRaw)):
            MeaningRaw = ' '.join(re.split(' +|\n+', MeaningRawRaw[s].get_text())).strip()
            m_temp = ' '.join(MeaningRaw.split())
            if len(Poses) < 1:
                Meaning += m_temp+"\n"
            else:
                Meaning += Poses[s].get_text() + m_temp + "\n"
        Meaning = Meaning.rstrip()
        Meaning = Meaning.replace("； ", "")

        sents_raw = NetDicBody.find_all("p", "def-sentence-from")
        sentstrans_raw = NetDicBody.find_all("p", "def-sentence-to")
        Sents = ''
        sentstrans = ''
        for s in sents_raw:
            Sents += ' '.join(s.get_text().split()) + "<br />"
        for s in sentstrans_raw:
            sentstrans += ' '.join(s.get_text().split()) + "<br />"
        Sents = Sents.rstrip()
        sentstrans = sentstrans.rstrip()


        return self.cache_this(
             {'expressions': Expression, 'Meaning':Meaning,'phonetic': Pronounces,'mp3':mp3,
              'sentences': Sents, 'sentence_trans': sentstrans, 'status': ''})

    @export(u'原文', 0)
    def fld_expressions(self):
        return self.cache_result('expressions') if self.cached('expressions') else self._get_content()['expressions']

    @export(u'释义', 1)
    def fld_meaning(self):
        return self.cache_result('Meaning') if self.cached('Meaning') else self._get_content()['Meaning']

    @export(u'读音', 2)
    def fld_phonetic(self):
        return self.cache_result('phonetic') if self.cached('phonetic') else self._get_content()['phonetic']

    @export(u'mp3', 3)
    def fld_mp3(self):
        # 沪江下载mp3发音的api同样需要user-agent
        urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36 SE 2.X MetaSr 1.0'

        audio_url = self.cache_result('mp3')
        # showInfo(audio_url)
        filename = u'_hj_{}.mp3'.format(self.word)
        try:
            urllib.urlretrieve(audio_url, filename)
            return self.get_anki_label(filename, 'audio')
        except Exception as e:
            return audio_url
        # if self.download(audio_url,filename):
        #     return self.get_anki_label(filename, 'audio')
        # return audio_url

    @export(u'例句', 4)
    def fld_sentences(self):
        return self.cache_result('sentences') if self.cached('sentences') else self._get_content()['sentences']

    @export(u'例句解释', 5)
    def fld_sentence_trans(self):
        return self.cache_result('sentence_trans') if self.cached('sentence_trans') else self._get_content()['sentence_trans']
    
    @export(u'状态', 6)
    def fld_statusmsg(self):
        return self.cache_result('status') if self.cached('status') else self._get_content()['status']
