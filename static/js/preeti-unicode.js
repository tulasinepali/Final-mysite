/**
 * Preeti <-> Unicode Nepali Font Converter
 * Built for tulasinepali.com.np
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.PreetiConverter = factory();
    }
}(typeof self !== 'undefined' ? self : this, function () {

    // Preeti to Unicode dictionary mapping
    var preetiToUnicodeMap = {
        '~': 'र्',
        '!': '१',
        '@': '२',
        '#': '३',
        '$': '४',
        '%': '५',
        '^': '६',
        '&': '७',
        '*': '८',
        '(': '९',
        ')': '०',
        '-': '(',
        '_': ')',
        '+': 'ं',
        'q': 'त्र',
        'w': 'ध',
        'e': 'भ',
        'r': 'च',
        't': 'त',
        'y': 'थ',
        'u': 'ग',
        'i': 'ष',
        'o': 'य',
        'p': 'उ',
        '[': 'ृ',
        ']': 'े',
        '{': 'र्',
        '}': 'ै',
        '\\': '?',
        '|': '्',
        'a': 'ब',
        's': 'क',
        'd': 'म',
        'f': 'ा',
        'g': 'न',
        'h': 'ज',
        'j': 'व',
        'k': 'प',
        'l': 'ि',
        ';': 'स',
        ':': 'स्',
        '\'': 'ु',
        '"': 'ू',
        'z': 'श',
        'x': 'ह',
        'c': 'अ',
        'v': 'ख',
        'b': 'द',
        'n': 'ल',
        'm': 'फ',
        ',': 'र',
        '.': '।',
        '/': 'र',
        'Q': 'त्त',
        'W': 'ध्',
        'E': 'भ्',
        'R': 'च्',
        'T': 'त्',
        'Y': 'थ्',
        'U': 'ग्',
        'I': 'क्ष',
        'O': 'इ',
        'P': 'ए',
        'A': 'ब्',
        'S': 'क्',
        'D': 'म्',
        'F': 'ँ',
        'G': 'न्',
        'H': 'ज्',
        'J': 'व्',
        'K': 'प्',
        'L': 'ी',
        ':': 'स्',
        'Z': 'श्',
        'X': 'ह्',
        'C': 'ऋ',
        'V': 'ख्',
        'B': 'द्',
        'N': 'ल्',
        'M': 'फ्',
        '<': '?',
        '>': 'श्र',
        '?': 'रु'
    };

    // Special conjuncts in Preeti
    var specialPreeti = [
        ['qm', 'फ'],
        ['If', 'क्षा'],
        ['cf]', 'ओ'],
        ['cf}', 'औ'],
        ['cf', 'आ'],
        ['c', 'अ'],
        ['O{', 'ई'],
        ['O', 'इ'],
        ['pm', 'ऊ'],
        ['p', 'उ'],
        ['P', 'ए'],
        ['P]', 'ऐ'],
        ['c}', 'ऐ'],
        ['s|', 'क्र'],
        ['k|', 'प्र'],
        ['a|', 'ब्र'],
        ['v|', 'ख्र'],
        ['u|', 'ग्र'],
        ['3|', 'घ्र'],
        ['r|', 'च्र'],
        ['h|', 'ज्र'],
        ['t|', 'त्र'],
        ['y|', 'थ्र'],
        ['b|', 'द्र'],
        ['w|', 'ध्र'],
        ['g|', 'न्र'],
        ['k|', 'प्र'],
        ['km|', 'फ्र'],
        ['a|', 'ब्र'],
        ['e|', 'भ्र'],
        ['d|', 'म्र'],
        ['o|', 'य्र'],
        ['n|', 'ल्र'],
        ['j|', 'व्र'],
        ['z|', 'श्र'],
        ['if|', 'ष्र'],
        [';|', 'स्र'],
        ['x|', 'ह्र'],
        ['b\\w', 'द्ध'],
        ['b\\b', 'द्द'],
        ['b\\e', 'द्भ'],
        ['b\\d', 'द्म'],
        ['b\\o', 'द्य'],
        ['b\\u', 'द्ग'],
        ['b\\3', 'द्घ'],
        ['6\\', 'ट्'],
        ['7\\', 'ठ्'],
        ['8\\', 'ड्'],
        ['9\\', 'ढ्'],
        ['0\\', 'ण्'],
        ['1\\', 'ज्ञ्'],
        ['2\\', 'द्'],
        ['3', 'घ'],
        ['4', 'द्ध'],
        ['5', 'छ'],
        ['6', 'ट'],
        ['7', 'ठ'],
        ['8', 'ड'],
        ['9', 'ढ'],
        ['0', 'ण'],
        ['1', 'ज्ञ'],
        ['2', 'द्व']
    ];

    function preetiToUnicode(str) {
        if (!str) return '';
        var out = str;

        // Replace special multicharacter Preeti ligatures first
        for (var i = 0; i < specialPreeti.length; i++) {
            var p = specialPreeti[i][0];
            var u = specialPreeti[i][1];
            out = out.split(p).join(u);
        }

        // Handle 'l' (chhoti i matra - ि) which in Preeti appears BEFORE the consonant
        // e.g. 'ls' in Preeti -> 'कि' in Unicode
        var lRegex = /l([क-ह](्[क-ह])?)/g;
        out = out.replace(lRegex, '$1ि');

        // Handle single character mappings
        var result = '';
        for (var j = 0; j < out.length; j++) {
            var ch = out[j];
            if (preetiToUnicodeMap[ch] !== undefined) {
                result += preetiToUnicodeMap[ch];
            } else {
                result += ch;
            }
        }

        // Post-processing for reph ({) -> placed on the previous consonant
        result = result.replace(/([क-ह](्[क-ह])?(ा|ि|ी|ु|ू|े|ै|ो|ौ|ं|ँ)?)र्/g, 'र्$1');

        return result;
    }

    // Unicode to Preeti dictionary mapping
    var unicodeToPreetiMap = {
        '१': '!',
        '२': '@',
        '३': '#',
        '४': '$',
        '५': '%',
        '६': '^',
        '७': '&',
        '८': '*',
        '९': '(',
        '०': ')',
        'ं': '+',
        'ँ': 'F',
        '।': '.',
        'क': 's',
        'ख': 'v',
        'ग': 'u',
        'घ': '3',
        'ङ': 'ª',
        'च': 'r',
        'छ': '5',
        'ज': 'h',
        'झ': 'H',
        'ञ': '`',
        'ट': '6',
        'ठ': '7',
        'ड': '8',
        'ढ': '9',
        'ण': '0',
        'त': 't',
        'थ': 'y',
        'द': 'b',
        'ध': 'w',
        'न': 'g',
        'प': 'k',
        'फ': 'm',
        'ब': 'a',
        'भ': 'e',
        'म': 'd',
        'य': 'o',
        'र': '/',
        'ल': 'n',
        'व': 'j',
        'श': 'z',
        'ष': 'i',
        'स': ';',
        'ह': 'x',
        'क्ष': 'I',
        'त्र': 'q',
        'ज्ञ': '1',
        'श्र': '>',
        'ा': 'f',
        'ी': 'L',
        'ु': '\'',
        'ू': '"',
        'ृ': '[',
        'े': ']',
        'ै': '}',
        'ो': 'f]',
        'ौ': 'f}',
        'अ': 'c',
        'आ': 'cf',
        'इ': 'O',
        'ई': 'O{',
        'उ': 'p',
        'ऊ': 'pm',
        'ए': 'P',
        'ऐ': 'P]',
        'ओ': 'cf]',
        'औ': 'cf}',
        'ऋ': 'C'
    };

    function unicodeToPreeti(str) {
        if (!str) return '';
        var out = str;

        // Move chhoti 'ि' before consonant in Preeti
        // In Unicode: क + ि -> In Preeti: l + s
        out = out.replace(/([क-ह](्[क-ह])?)ि/g, 'l$1');

        var res = '';
        for (var i = 0; i < out.length; i++) {
            var ch = out[i];
            if (unicodeToPreetiMap[ch] !== undefined) {
                res += unicodeToPreetiMap[ch];
            } else {
                res += ch;
            }
        }

        // Halanta + character combinations
        res = res.replace(/्/g, '|');

        return res;
    }

    return {
        preetiToUnicode: preetiToUnicode,
        unicodeToPreeti: unicodeToPreeti
    };
}));
