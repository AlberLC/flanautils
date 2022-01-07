import datetime
import random
from typing import Iterable

from flanautils.data_structures.bi_dict import BiDict
from flanautils.data_structures.ordered_set import OrderedSet

NUMBER_WORDS = {
    'es': BiDict({
        '-': 'menos',
        0: 'cero', 1: 'uno', 2: 'dos', 3: 'tres', 4: 'cuatro', 5: 'cinco', 6: 'seis', 7: 'siete', 8: 'ocho', 9: 'nueve',
        10: 'diez', 11: 'once', 12: 'doce', 13: 'trece', 14: 'catorce', 15: 'quince', 16: 'dieciséis',
        20: 'veinte', 30: 'treinta', 40: 'cuarenta', 50: 'cincuenta', 60: 'sesenta', 70: 'setenta', 80: 'ochenta', 90: 'noventa',
        100: 'cien'
    })
}
NUMBERS_RATIO_MATCHING = 0.65
TIME_UNITS_RATIO_MATCHING = 0.75
WEEKS_IN_A_MONTH = 4.34524
SYMBOLS = ('!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '[',
           '\\', ']', '^', '_', '`', '{', '|', '}', '~', '¡', '¨', 'ª', '¬', '´', '·', 'º', '¿', '€')


# noinspection PyPropertyDefinition
class CommonWords:
    common_words = {
        'en': {
            'adverbs': (
                'abnormally', 'above', 'abroad', 'absentmindedly', 'accidentally', 'actually', 'adventurously',
                'afterwards', 'almost', 'already', 'always', 'annually', 'anxiously', 'anywhere', 'arrogantly', 'away',
                'awkwardly', 'back', 'badly', 'barely', 'bashfully', 'beautifully', 'behind', 'bitterly', 'bleakly',
                'blindly', 'blissfully', 'boastfully', 'boldly', 'bravely', 'briefly', 'brightly', 'briskly', 'broadly',
                'busily', 'calmly', 'carefully', 'carelessly', 'cautiously', 'certainly', 'cheerfully', 'clearly',
                'cleverly', 'closely', 'coaxingly', 'colorfully', 'commonly', 'completely', 'continually', 'coolly',
                'correctly', 'courageously', 'crossly', 'cruelly', 'curiously', 'daily', 'daintily', 'deal', 'dearly',
                'deceivingly', 'deeply', 'defiantly', 'deliberately', 'delightfully', 'diligently', 'dimly',
                'doubtfully', 'downstairs', 'dreamily', 'eagerly', 'easily', 'elegantly', 'elsewhere', 'emotely',
                'energetically', 'enormously', 'enough', 'enthusiastically', 'entirely', 'equally', 'especially',
                'even', 'evenly', 'eventually', 'ever', 'exactly', 'excitedly', 'extremely', 'fairly', 'faithfully',
                'famously', 'far', 'fast', 'fatally', 'ferociously', 'fervently', 'few', 'fiercely', 'fondly',
                'foolishly', 'fortunately', 'frankly', 'frantically', 'freely', 'frenetically', 'frequently',
                'frightfully', 'fully', 'furiously', 'generally', 'generously', 'gently', 'gladly', 'gleefully', 'good',
                'gracefully', 'gratefully', 'greatly', 'greedily', 'grimly', 'happily', 'hardly', 'hastily',
                'healthily', 'heavily', 'helpfully', 'helplessly', 'here', 'highly', 'honestly', 'hopelessly', 'hourly',
                'hungrily', 'immediately', 'indoor', 'innocently', 'inquisitively', 'inside', 'instantly', 'intensely',
                'intently', 'interestingly', 'inwardly', 'irritably', 'jaggedly', 'jealously', 'jovially', 'joyfully',
                'joyously', 'jubilantly', 'judgmentally', 'just', 'justly', 'keenly', 'kiddingly', 'kindheartedly',
                'kindly', 'knavishly', 'knowingly', 'knowledgeably', 'kookily', 'last', 'later', 'lazily', 'less',
                'lightly', 'likely', 'limply', 'little', 'lively', 'loftily', 'longingly', 'loosely', 'lot', 'lots',
                'loudly', 'lovingly', 'lowly', 'loyally', 'madly', 'majestically', 'many', 'meaningfully',
                'mechanically', 'merrily', 'miserably', 'mockingly', 'month', 'monthly', 'more', 'mortally', 'mostly',
                'much', 'mysteriously', 'naturally', 'nearby', 'nearly', 'neatly', 'nervously', 'never', 'nicely',
                'noisily', 'normally', 'not', 'nothing', 'now', 'obediently', 'obnoxiously', 'occasionally', 'oddly',
                'offensively', 'officially', 'often', 'only', 'openly', 'optimistically', 'out', 'outside',
                'overconfidently', 'painfully', 'partially', 'patiently', 'perfectly', 'physically', 'playfully',
                'politely', 'poorly', 'positively', 'potentially', 'powerfully', 'promptly', 'properly', 'punctually',
                'quaintly', 'queasily', 'queerly', 'questionably', 'quicker', 'quickly', 'quietly', 'quirkily', 'quite',
                'quizzically', 'randomly', 'rapidly', 'rarely', 'rather', 'readily', 'really', 'reassuringly',
                'recklessly', 'regularly', 'reluctantly', 'repeatedly', 'reproachfully', 'restfully', 'righteously',
                'rightfully', 'rigidly', 'roughly', 'rudely', 'safely', 'scarcely', 'scarily', 'searchingly',
                'secretly', 'sedately', 'seemingly', 'seldom', 'selfishly', 'separately', 'seriously', 'shakily',
                'sharply', 'sheepishly', 'shrilly', 'shyly', 'silently', 'sleepily', 'slowly', 'smoothly', 'softly',
                'solemnly', 'solidly', 'some', 'sometimes', 'soon', 'specifically', 'speedily', 'stealthily', 'sternly',
                'strictly', 'strongly', 'successfully', 'suddenly', 'supposedly', 'surprisingly', 'suspiciously',
                'sweetly', 'swiftly', 'sympathetically', 'tenderly', 'tensely', 'terribly', 'thankfully', 'then',
                'there', 'thoroughly', 'thoughtfully', 'tightly', 'today', 'tomorrow', 'tonight', 'too', 'towards',
                'tremendously', 'triumphantly', 'truly', 'truthfully', 'ultimately', 'unabashedly', 'unaccountably',
                'unbearably', 'unethically', 'unexpectedly', 'unfortunately', 'unimpressively', 'unnaturally',
                'unnecessarily', 'upbeat', 'upright', 'upside-down', 'upward', 'urgently', 'usefully', 'uselessly',
                'usually', 'utterly', 'vacantly', 'vaguely', 'vainly', 'valiantly', 'vastly', 'verbally', 'very',
                'viciously', 'victoriously', 'violently', 'vivaciously', 'voluntarily', 'warmly', 'weakly', 'wearily',
                'week', 'weetly', 'well', 'wetly', 'wholly', 'wildly', 'willfully', 'wisely', 'wishfully', 'woefully',
                'wonderfully', 'worriedly', 'wrongly', 'yawningly', 'year', 'yearly', 'yearningly', 'yesterday',
                'yieldingly', 'youthfully', 'zealously', 'zestfully', 'zestily'),
            'determiner': {
                'definite_article': ('the',),
                'indefinite': ('another', 'any', 'every', 'few', 'lot', 'much', 'other', 'several', 'some', 'very'),
                'indefinite_article': ('a', 'an'),
                'possessive': ('hers', 'his', 'its', 'my', 'our', 'their', 'whose', 'your'),
                'demonstrative': ('that', 'these', 'this', 'those'),
                'numeral': (),
                'ordinal': ('first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth'),
            },
            'greetings': ('Good morning.', 'Good afternoon.', 'Goodnight.'),
            'preposition': ('about', 'above', 'abroad', 'accordance', 'according', 'account', 'across', 'addition',
                            'after', 'against', 'ago', 'ahead', 'along', 'amidst', 'among', 'amongst', 'apart', 'around',
                            'as', 'aside', 'at', 'away', 'because', 'before', 'behalf', 'behind', 'below', 'beneath',
                            'beside', 'besides', 'between', 'beyond', 'but', 'by', 'case', 'close', 'despite', 'down',
                            'due', 'during', 'except', 'farwell', 'for', 'from', 'front', 'hence', 'in', 'inside',
                            'instead', 'into', 'lieu', 'like', 'means', 'near', 'next', 'notwithstanding', 'of', 'off',
                            'on', 'onto', 'opposite', 'out', 'outside', 'over', 'owing', 'past', 'per', 'place', 'prior',
                            'round', 'since', 'spite', 'than', 'through', 'throughout', 'till', 'times', 'to', 'top',
                            'toward', 'towards', 'under', 'underneath', 'unlike', 'until', 'unto', 'up', 'upon', 'via',
                            'view', 'with', 'within', 'without', 'worth'),
            'pronoun': {
                'interrogative': ('what', 'which', 'who', 'whom', 'whose'),
                'object': ('her', 'him', 'it', 'me', 'them', 'us', 'you'),
                'possessive': ('hers', 'his', 'its', 'mine', 'ours', 'theirs', 'yours'),
                'reflexive': ('herself', 'himself', 'itself', 'myself', 'ourselves', 'themselves', 'yourself',
                              'yourselves'),
                'subject': ('he', 'i', 'it', 'she', 'they', 'we', 'you'),
            },
            'others': ("don't", 'dont', 'let', "let's", 'lets', 'no', 'not', 'yes')
        },
        'es': {
            'adverbs': (
                'abajo', 'aca', 'acaso', 'actualmente', 'ademas', 'ahi', 'ahora', 'algo', 'alla', 'alli', 'alrededor',
                'anoche', 'anteriormente', 'antes', 'aprisa', 'aproximadamente', 'aqui', 'arriba', 'asi', 'asimismo',
                'atras', 'aun', 'ayer', 'bastante', 'bien', 'casi', 'cerca', 'ciertamente', 'cierto', 'claro', 'como',
                'concretamente', 'debajo', 'delante', 'demasiado', 'dentro', 'deprisa', 'despacio', 'despues', 'detras',
                'efectivamente', 'encima', 'enfrente', 'enseguida', 'estupendamente', 'exacto', 'facilmente',
                'fielmente', 'fuera', 'hoy', 'inclusive', 'incluso', 'jamas', 'lejos', 'luego', 'mal', 'mas', 'mañana',
                'medio', 'mejor', 'menos', 'mientras', 'mismamente', 'mucho', 'muy', 'nada', 'negativamente', 'no',
                'nunca', 'obvio', 'peor', 'poco', 'posiblemente', 'precisamente', 'primeramente', 'probablemente',
                'prontamente', 'pronto', 'propiamente', 'proximamente', 'quiza', 'quizas', 'regular',
                'responsablemente', 'seguramente', 'si', 'siempre', 'siquiera', 'solamente', 'solo', 'tal', 'tambien',
                'tampoco', 'tan', 'tanto', 'tarde', 'temprano', 'todavia', 'todo', 'ultimamente', 'unicamente',
                'verdaderamente', 'vez', 'viceversa', 'ya'),
            'determiner': {
                'definite_article': ('al', 'del', 'el', 'la', 'las', 'lo', 'los'),
                'indefinite': ('algun', 'alguna', 'algunas', 'alguno', 'algunos', 'bastante', 'bastantes', 'cualesquiera',
                               'cualquier', 'cualquiera', 'demasiada', 'demasiadas', 'demasiado', 'demasiados', 'misma',
                               'mismas', 'mismo', 'mismos', 'mucha', 'muchas', 'mucho', 'muchos', 'ningun', 'ninguna',
                               'ningunas', 'ninguno', 'ningunos', 'otra', 'otras', 'otro', 'otros', 'poca', 'pocas', 'poco',
                               'pocos', 'tal', 'tales', 'tanta', 'tantas', 'tanto', 'tantos', 'toda', 'todas', 'todo',
                               'todos', 'uno', 'varias', 'varios'),
                'indefinite_article': ('un', 'una', 'unas', 'unos'),
                'possessive': ('mi', 'mia', 'mias', 'mio', 'mios', 'mis', 'nuestra', 'nuestras', 'nuestro', 'nuestros',
                               'su', 'sus', 'suya', 'suyas', 'suyo', 'suyos', 'tu', 'tus', 'tuya', 'tuyas', 'tuyo',
                               'tuyos', 'vuestra', 'vuestras', 'vuestro', 'vuestros'),
                'demonstrative': ('aquel', 'aquella', 'aquellas', 'aquello', 'aquellos', 'esa', 'esas', 'ese', 'eso',
                                  'esos', 'esta', 'estas', 'este', 'estos'),
                'numeral': (),
                'ordinal': ('primero', 'segundo', 'tercero', 'cuarto', 'quinto', 'sexto', 'septimo', 'octavo', 'noveno',
                            'decimo'),
            },
            'greetings': ('Buenos días.', 'Buenas tardes.', 'Buenas noches.'),
            'preposition': ('a', 'ante', 'bajo', 'cabe', 'con', 'contra', 'de', 'desde', 'durante', 'en', 'entre', 'hacia',
                            'hasta', 'mediante', 'para', 'por', 'según', 'sin', 'so', 'sobre', 'tras', 'versus', 'vía'),
            'pronoun': {
                'interrogative': ('cual', 'cuales', 'cuanta', 'cuantas', 'cuanto', 'cuantos', 'que'),
                'object': ('conmigo', 'consigo', 'contigo', 'el', 'ella', 'ellas', 'ello', 'ellos', 'mi', 'nosotras',
                           'nostros', 'si', 'ti', 'usted', 'ustedes', 'vos', 'vosotras', 'vosotros'),
                'possessive': ('mia', 'mias', 'mio', 'mios', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'suya', 'suyas',
                               'suyo', 'suyos', 'tuya', 'tuyas', 'tuyo', 'tuyos', 'vuestra', 'vuestras', 'vuestro',
                               'vuestros'),
                'reflexive': ('me', 'nos', 'os', 'se', 'te'),
                'subject': ('el', 'ella', 'ellas', 'ello', 'ellos', 'la', 'las', 'le', 'les', 'lo', 'los', 'me', 'nos',
                            'nosotras', 'nosotros', 'os', 'se', 'te', 'tu', 'usted', 'ustedes', 'vos', 'vosotras', 'vosotros', 'yo'),
            },
            'others': ('ha', 'hace', 'hacer', 'hara', 'he', 'no', 'si', 'va', 'vamos', 'voy')
        }
    }

    @classmethod
    def _get_language_names(cls, language: str = None) -> Iterable[str]:
        if language:
            return language,
        else:
            return cls.common_words.keys()

    @classmethod
    @property
    def en_greetings(cls) -> list[str]:
        return cls.get_greetings_by_language('en')

    @classmethod
    @property
    def en_words(cls) -> list[str]:
        return cls.get_words_by_language('en')

    @classmethod
    def get_greetings_by_language(cls, language: str = None) -> list[str]:
        return [greeting for language_name in cls._get_language_names(language) for greeting in cls.common_words[language_name]['greetings']]

    @classmethod
    def get_words_by_language(cls, language: str = None) -> list[str]:
        words = OrderedSet()

        for language_name in cls._get_language_names(language):
            for v1 in cls.common_words[language_name].values():
                match v1:
                    case dict():
                        for k2, v2 in v1.items():
                            words += v2
                    case [*_]:
                        words += v1

        return list(words)

    @classmethod
    @property
    def greetings(cls) -> list[str]:
        return cls.get_greetings_by_language()

    @classmethod
    @property
    def es_greetings(cls) -> list[str]:
        return cls.get_greetings_by_language('es')

    @classmethod
    @property
    def es_words(cls) -> list[str]:
        return cls.get_words_by_language('es')

    @classmethod
    def random_time_greeting(cls, language: str = None) -> str:
        language = language or random.choice(list(cls.common_words.keys()))
        return random.choice((
            cls.time_greeting(language),
            cls.time_greeting(language).lower(),
            cls.time_greeting(language)[:-1],
            cls.time_greeting(language).lower()[:-1]
        ))

    @classmethod
    def time_greeting(cls, language='es') -> str:
        hour = datetime.datetime.now().hour

        if 7 <= hour < 12:
            return cls.get_greetings_by_language(language)[0]
        elif 12 <= hour < 21:
            return cls.get_greetings_by_language(language)[1]
        else:
            return cls.get_greetings_by_language(language)[2]

    @classmethod
    @property
    def words(cls) -> list[str]:
        return cls.get_words_by_language()
