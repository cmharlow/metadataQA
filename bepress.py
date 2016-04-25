from bs4 import BeautifulSoup
import requests
from lxml import etree
import re

base_url = 'http://digitalcommons.ilr.cornell.edu/'
base_aws = 's3://dc-ilr-cornell-edu-archive/archive/digitalcommons.ilr.cornell.edu/'
nsmap = {'oai': 'http://www.openarchives.org/OAI/2.0/',
         'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
         'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
         'dc': 'http://purl.org/dc/elements/1.1/'}
OAI = '{http://www.openarchives.org/OAI/2.0/}'
DC = '{http://purl.org/dc/elements/1.1/}'
OAIDC = '{http://www.openarchives.org/OAI/2.0/oai_dc/}'


def sw3_harvest():
    """get sw3 backup information including original metadata + filenames"""


def sw3_ids():
    """get sw3 backup information including original metadata + filenames"""


def meta_info(soup):
    """given a BeautifulSoup object representing a BePress page, extract the
    meta tags and return those of interest - keywords (split and stored as a
    list), series title, author, title, date, PDF URL, abstract URL (should
    match the record URL), and date online (roughly date created in BePress
    speak)"""

    html = requests.get(base_url + "globaldocs/430/").text
    soup = BeautifulSoup(html, 'html5lib')

    meta_dict = []
    for meta in soup.find_all('meta'):
        meta_dict['html' + meta.get('name')] = meta.get('contents')
    abstract = soup.find('div', {"id": "abstract"}).p.text
    comments = soup.find('div', {"id": "comments"}).p.text
    meta_dict['html_abstract'] = abstract
    meta_dict['html_comments'] = comments


def get_prefixes():
    """getting all the namespaces that could possibly appear in the OAI-PMH
    output"""
    meta_names = requests.get(base_url + 'do/oai/?verb=ListMetadataFormats')
    meta_root = etree.fromstring(meta_names.content)
    prefixes = meta_root.xpath(".//oai:metadataPrefix/text()",
                               namespaces=nsmap)
    prefixes = ['dcs' if x == 'simple-dublin-core' else x for x in prefixes]
    prefixes = ['qdc' if x == 'qualified-dublin-core' else x for x in prefixes]
    return(prefixes)


def oai_getID():



def oai_harvest():
    """get metadata from 4 different OAI-PMH feeds from live Bepress site,
    merge and populate into response JSON object. Used to then call webscraper
    and SW3"""
    prefixes = get_prefixes()
    for prefix in prefixes:
        data = requests.get(base_url +
                            'do/oai/?verb=ListRecords&metadataPrefix=' +
                            prefix).content

        # from http://boodebr.org/main/python/all-about-python-and-unicode#UNI_XML
        RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                         u'|' + \
                         u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                          (unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                           unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                           unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff))
        dataClean = re.sub(RE_XML_ILLEGAL, "?", data.content)

        while dataClean:
            root = etree.fromstring(dataClean)
            for child in root.iter(OAI + "record"):
                if event == "START_ELEMENT" and node.tagName == 'record':
                    events.expandNode(node)
                    node.writexml(ofile)
            more = re.search('<resumptionToken[^>]*>(.*)</resumptionToken>',
                             dataClean)
            if not more:
                break
            data = requests.get(base_url + "ListRecords&resumptionToken=" +
                                more.group(1))
            dataClean = re.sub(RE_XML_ILLEGAL, "?", data)


if __name__ == "__main__":
    resp = {}
    num_rec = 0
    num_file = 0



