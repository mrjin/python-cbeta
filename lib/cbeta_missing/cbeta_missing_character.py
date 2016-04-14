"""
This module contains the Class ``CbetaMissingCharacters``, which is used to
look for missing characters in the file, update the missing characters database
by extracting information from cbeta file and write the dictionary to file specified.
"""

import json
import os
from lxml import etree
import logging

from lib.utils.remove_namespace import remove_namespace


class CbetaMissingCharacter:
    """
    This Class is used to store some missing characters in the cbeta,
    it is based on a database with the format of json. The class contains
    some static variable, those are

    ``PATH_TO_DATA``: the path to a pre-generated json file, contains all
                      the missing characters in the cbeta corpus
    ``LOGGER``: logger
    ``FIELD_MAPPING``: a look-up table used in the ``extract_char``, to mapping fields
    """

    PATH_TO_DATA = '../resources/missing_character.json'

    LOGGER = logging.getLogger('Cbeta_Missing_Character')

    FIELD_MAPPING = {
        'big5': 'big5',
        'Character in the Siddham font': 'char_in_siddham_font',
        'composition': 'zzs',
        'normalized form': 'normal',
        'rjchar': 'rjchar',
        'Romanized form in CBETA transcription': 'roman_cbeta',
        'Romanized form in Unicode transcription': 'roman'
    }

    def __init__(self):
        """
        The init method loads json from the file and save it in the dict.
        Then, it generated a look-up table with the dict.
        :return: None
        """
        file_path = os.path.join(os.path.abspath(__file__),
                                 self.PATH_TO_DATA.replace('/', os.sep))
        with open(file_path) as file:
            self.missing_dict = json.loads(file)

        self.zzs_code = dict()
        self.create_zzs_code_lookup()

    def create_zzs_code_lookup(self):
        """
        Create the look-up table from zzs code(eg. "[(王*巨)/木]") to CB code(eg. "CB00006")
        The function add element in place
        :return: None
        """
        for key, value in self.missing_dict.items():
            if 'zzs' in value:
                self.zzs_code[value['zzs']] = key

    def get(self, cb_code):
        """
        return the corresponding result for cb code in the dictionary(`self.missing_dict`).
        If the cb code not in the dictionary, return None.
        :example
        an_instance.get("CB00006")

        return-value:
        {
            "zzs": "[(王*巨)/木]",
            "normal": "璩",
            "unicode": "249B2",
            "unicode-char": "𤦲"
        }
        :param cb_code: str
        :return: dict or None
        """
        if cb_code in self.missing_dict:
            return self.missing_dict[cb_code]
        else:
            return None

    def get_phonetic_notation(self, cb_code):
        """
        get the phonetic notation format for the specific CB code.
        :example
        an_instance.get_phonetic_notation("CB00023")

        return-value:
        [ "ㄍㄢˇ", "ㄍㄢ", "ㄧㄤˊ", "ㄇㄧˇ", "ㄇㄧㄝ", "ㄒㄧㄤˊ" ]
        :param cb_code: str
        :return: list or None
        """
        if cb_code in self.missing_dict and 'zhuyin' in self.missing_dict[cb_code]:
            return self.missing_dict[cb_code]['zhuyin']
        else:
            return None

    def extract_char(self, char):
        """
        char here is an instance of lxml.etree.Element
        extract some specific properties from char including localName and value
        in node ``charProp`` and unicode in node ``mapping``.

        If the localName is in the FIELD_MAPPINP, the dictionary defined before,
        it will be replaced by its corresponding field name, namely the value in
        the dictionary.

        If the type of the mapping is normal_unicode, the function will
        extract its unicode value. If the type is unicode, the function will do both
        extract its unicdoe value and change it to the unicode char.

        The function will return a dict.
        :param char: lxml.etree.Element
        :return: res: dict
        """
        res = {}
        char_id = char.attrib['id']

        for element in char.findall('./charProp'):
            local_name = element.find('./localName').text
            value = element.find('./value').text
            if local_name in self.FIELD_MAPPING:
                key = self.FIELD_MAPPING[local_name]
                res[key] = value
            else:
                self.LOGGER.info("Not handling charProp, char id=%s, key=%s, value=%s",
                                 char_id, local_name, value)

        type_to_store = ('normal_unicode', 'unicode')
        for element in char.findall('./mapping'):
            mapping_type = element.attrib['type']
            if mapping_type in type_to_store:
                unicode = element.text[2:-1]
                res[mapping_type] = unicode
                if mapping_type == 'unicode':
                    res['unicode-char'] = chr(int(unicode))

        return res

    def update_from_p5_file(self, filename):
        """
        The function update the dictionary ``missing_character`` of the instance, it
        will get related information from the file. It will use xpath to get all the
        ``char`` nodes in the file, which is needed. Then it will traverse all the nodes
        and add the information from the nodes to the dictionary.
        :param filename: str
        :return: None
        """
        self.LOGGER.info("Read Cbeta P5 file " + filename)

        try:
            doc = etree.parse(filename)
        except IOError as exception:
            self.LOGGER.error("open file error, filename=" + filename, exception)
            raise exception

        root = doc.getroot()
        namespace = '' if None not in root.nsmap else '{' + root.nsmap[None] + '}'
        remove_namespace(doc, namespace)
        for element in doc.finall('//charDecl/char'):
            self.missing_dict[element.attrib['id']] = self.extract_char(element)

    def update_from_p5_folder(self, folder):
        """
        The function will update the dictionary ``missing_character`` with all the cbeta
        file under the passed folder, it will recursively call itself or the function
        ``update_from_p5_file`.
        :param folder: str
        :return: None
        """
        for file in os.walk(folder):
            path = os.path.join(folder, file)
            if path.startswith('.'):
                continue
            elif os.path.isdir(path):
                self.update_from_p5_folder(path)
            else:
                self.update_from_p5_file(path)
