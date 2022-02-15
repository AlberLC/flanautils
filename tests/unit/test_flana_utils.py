import unittest

import strings


class TestFlanaUtils(unittest.TestCase):
    def test_replace(self):
        tests_args = [
            ('hola', {}, 'hola'),
            ('hola', {'x': None}, 'hola'),
            ('hola', {'x': 'h', 's': 'x'}, 'hola'),

            ('holahola', {}, 'holahola'),
            ('holahola', {'x': None}, 'holahola'),
            ('holahola', {'x': 'h', 's': 'x'}, 'holahola'),

            ('hola', {'h': ''}, 'ola'),
            ('hola', {'h': '', 'o': None}, 'la'),
            ('hola', {'o': None}, 'hla'),
            ('hola', {'o': None, 'l': None}, 'ha'),
            ('hola', {'h': None, 'l': None}, 'oa'),

            ('holahola', {'h': '', 'o': None}, 'lala'),
            ('holahola', {'o': None}, 'hlahla'),

            ('holahola', {'a': 'h'}, 'holhholh'),

            ('holahola', {'a': 'h', 'h': ''}, 'olholh'),
            ('holahola', {'a': 'h', 'h': 'a'}, 'aolhaolh'),

            ('holahola', {'ho': '--'}, '--la--la'),
            ('holahola', {'ho': '-'}, '-la-la'),
            ('holahola', {'ho': ''}, 'lala'),
            ('holahola', {'ho': 'la', 'la': 'ho'}, 'laholaho'),

            ('hola', {'h': '', 'o': 'h'}, 'hla'),
            ('holahola', {'h': '', 'o': 'h'}, 'hlahla'),
            ('hola', {'o': '', 'a': 'x'}, 'hlx'),
            ('holahola', {'o': '', 'a': 'x'}, 'hlxhlx'),

            ('hola', {'ho': '', 'la': 'ho'}, 'ho'),
            ('holahola', {'ho': '', 'la': 'ho'}, 'hoho'),
            ('hola', {'ol': '', 'a': 'x'}, 'hx'),
            ('holahola', {'ol': '', 'a': 'x'}, 'hxhx'),

            ('hola', {'ho': '', 'ol': 'ho'}, 'la'),
            ('holahola', {'ho': '', 'ol': 'ho'}, 'lala'),
            ('hola', {'ho': '', 'ola': '--'}, 'la'),
            ('holahola', {'ho': '', 'ola': '--'}, 'lala'),

            ('hola', {'ho': '', 'hol': '--'}, 'la'),
            ('holahola', {'ho': '', 'hol': '--'}, 'lala'),
            ('hola', {'ho': '', 'hola': '-'}, 'la'),
            ('holahola', {'ho': '', 'hola': '-'}, 'lala'),
            ('hola', {'hola': '', 'a': '-'}, ''),
            ('holahola', {'hola': '', 'a': '-'}, ''),

            ('', {}, ''),
            ('', {'h': '', 'o': '-'}, ''),
            ('', {'ho': '', 'h': '-'}, ''),

            ('hola', {'hola': '1234', 'o': '-'}, '1234'),
            ('holahola', {'hola': '1234', 'o': '-'}, '12341234'),
            ('hola', {'hola': '1234', 'o': '-'}, '1234'),
            ('holahola', {'hola': '1234', 'o': '-'}, '12341234'),
            ('holahola', {'holahola': '12345678', 'o': '-'}, '12345678'),

            ('hola', {'h': 'o', 'o': '-'}, 'o-la'),
            ('holahola', {'h': 'o', 'o': '-'}, 'o-lao-la'),
            ('hola', {'ho': 'la', 'la': '--'}, 'la--'),
            ('holahola', {'ho': 'la', 'la': '--'}, 'la--la--'),

            ('hola', {'l': 'h', 'h': '-'}, '-oha'),
            ('holahola', {'l': 'h', 'h': '-'}, '-oha-oha'),
            ('hola', {'la': 'ho', 'ho': '-'}, '-ho'),
            ('holahola', {'la': 'ho', 'ho': '-'}, '-ho-ho'),

            ('hola', {'ol': 'l', 'hl': '--'}, 'hla'),
            ('holahola', {'ol': 'l', 'hl': '--'}, 'hlahla'),

            ('hola', {'o': '', 'h': 'x'}, 'xla'),
            ('holahola', {'o': '', 'h': 'x'}, 'xlaxla'),
            ('hola', {'ol': '', 'h': 'x'}, 'xa'),
            ('holahola', {'ol': '', 'h': 'x'}, 'xaxa'),

            ('hola', {'h': 'l', 'o': '', 'l': '-'}, 'l-a'),
            ('holahola', {'h': 'l', 'o': '', 'l': '-'}, 'l-al-a'),

            ('hello', {}, 'hello'),
            ('hello', {'x': None}, 'hello'),
            ('hello', {'x': 'h', 's': 'x'}, 'hello'),

            ('hellohello', {}, 'hellohello'),
            ('hellohello', {'x': None}, 'hellohello'),
            ('hellohello', {'x': 'h', 's': 'x'}, 'hellohello'),

            ('hello', {'h': ''}, 'ello'),
            ('hello', {'h': '', 'o': None}, 'ell'),
            ('hello', {'o': None}, 'hell'),
            ('hello', {'o': None, 'l': None}, 'he'),
            ('hello', {'h': None, 'l': None}, 'eo'),

            ('hellohello', {'h': '', 'o': None}, 'ellell'),
            ('hellohello', {'o': None}, 'hellhell'),

            ('hellohello', {'o': 'h'}, 'hellhhellh'),

            ('hellohello', {'o': 'h', 'h': ''}, 'ellhellh'),
            ('hellohello', {'o': 'h', 'h': 'o'}, 'oellhoellh'),

            ('hellohello', {'he': '--'}, '--llo--llo'),
            ('hellohello', {'he': '-'}, '-llo-llo'),
            ('hellohello', {'he': ''}, 'llollo'),
            ('hellohello', {'he': 'llo', 'llo': 'he'}, 'llohellohe'),

            ('hello', {'h': '', 'e': 'h'}, 'hllo'),
            ('hellohello', {'h': '', 'e': 'h'}, 'hllohllo'),
            ('hello', {'e': '', 'o': 'x'}, 'hllx'),
            ('hellohello', {'e': '', 'o': 'x'}, 'hllxhllx'),

            ('hello', {'he': '', 'llo': 'he'}, 'he'),
            ('hellohello', {'he': '', 'llo': 'he'}, 'hehe'),
            ('hello', {'el': '', 'o': 'x'}, 'hlx'),
            ('hellohello', {'el': '', 'o': 'x'}, 'hlxhlx'),

            ('hello', {'he': '', 'el': 'ho'}, 'llo'),
            ('hellohello', {'he': '', 'el': 'ho'}, 'llollo'),
            ('hello', {'he': '', 'ello': '--'}, 'llo'),
            ('hellohello', {'he': '', 'ello': '--'}, 'llollo'),

            ('hello', {'he': '', 'hell': '--'}, 'llo'),
            ('hellohello', {'he': '', 'hell': '--'}, 'llollo'),
            ('hello', {'he': '', 'hello': '-'}, 'llo'),
            ('hellohello', {'he': '', 'hello': '-'}, 'llollo'),
            ('hello', {'hello': '', 'o': '-'}, ''),
            ('hellohello', {'hello': '', 'o': '-'}, ''),

            ('', {}, ''),
            ('', {'h': '', 'e': '-'}, ''),
            ('', {'he': '', 'h': '-'}, ''),

            ('hello', {'hello': '1234', 'o': '-'}, '1234'),
            ('hellohello', {'hello': '1234', 'o': '-'}, '12341234'),
            ('hello', {'hello': '1234', 'o': '-'}, '1234'),
            ('hellohello', {'hello': '1234', 'o': '-'}, '12341234'),
            ('hellohello', {'hellohello': '12345678', 'o': '-'}, '12345678'),

            ('hello', {'h': 'e', 'e': '-'}, 'e-llo'),
            ('hellohello', {'h': 'e', 'e': '-'}, 'e-lloe-llo'),
            ('hello', {'he': 'llo', 'llo': '--'}, 'llo--'),
            ('hellohello', {'he': 'llo', 'llo': '--'}, 'llo--llo--'),

            ('hello', {'l': 'e', 'e': '-'}, 'h-eeo'),
            ('hellohello', {'l': 'e', 'e': '-'}, 'h-eeoh-eeo'),
            ('hello', {'llo': 'he', 'he': '-'}, '-he'),
            ('hellohello', {'llo': 'he', 'he': '-'}, '-he-he'),

            ('hello', {'el': 'l', 'hl': '--'}, 'hllo'),
            ('hellohello', {'el': 'l', 'hl': '--'}, 'hllohllo'),

            ('hello', {'e': '', 'h': 'x'}, 'xllo'),
            ('hellohello', {'e': '', 'h': 'x'}, 'xlloxllo'),
            ('hello', {'el': '', 'h': 'x'}, 'xlo'),
            ('hellohello', {'el': '', 'h': 'x'}, 'xloxlo'),

            ('hello', {'h': 'l', 'e': '', 'l': '-'}, 'l--o'),
            ('hellohello', {'h': 'l', 'e': '', 'l': '-'}, 'l--ol--o'),

            ('asd', {'a': 's', 's': 'x'}, 'sxd'),
            ('asdasd', {'a': 's', 's': 'x'}, 'sxdsxd'),
            ('asd', {'as': 'd', 'd': 'x'}, 'dx'),
            ('asdasd', {'as': 'd', 'd': 'x'}, 'dxdx'),
            ('asd', {'as': '', 'd': 'x'}, 'x'),
            ('asdasd', {'as': '', 'd': 'x'}, 'xx')
        ]

        for test_arg in tests_args:
            with self.subTest(test_arg):
                self.assertEqual(test_arg[2], strings.replace(test_arg[0], test_arg[1]))
