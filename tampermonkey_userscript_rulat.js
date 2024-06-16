// ==UserScript==
// @name         RuLat
// @namespace    http://tampermonkey.net/
// @version      1.5
// @description  RuLat is an art-project user script
// @author       https://github.com/dobrosketchkun
// @match        http://*/*
// @match        https://*/*
// @grant        none
// @license      The Uncertain Commons License https://gist.github.com/dobrosketchkun/d0c6aba085fb4a910926616a8b83c4c5
// ==/UserScript==

(function() {
    'use strict';

    function transliterate(text) {
        // Define the mapping from Cyrillic to Latin
        const charMap = {
            'A': 'A', 'a': 'a',
            'B': 'B', 'b': 'b',
            'V': 'V', 'v': 'v',
            'G': 'G', 'g': 'g',
            'D': 'D', 'd': 'd',
            'E': 'E', 'e': 'e',
            'JO': 'JO', 'jo': 'jo',
            'X': 'X', 'x': 'x',
            'Z': 'Z', 'z': 'z',
            'I': 'I', 'i': 'i',
            'J': 'J', 'j': 'j',
            'K': 'K', 'k': 'k',
            'L': 'L', 'l': 'l',
            'M': 'M', 'm': 'm',
            'N': 'N', 'n': 'n',
            'O': 'O', 'o': 'o',
            'P': 'P', 'p': 'p',
            'R': 'R', 'r': 'r',
            'S': 'S', 's': 's',
            'T': 'T', 't': 't',
            'U': 'U', 'u': 'u',
            'F': 'F', 'f': 'f',
            'H': 'H', 'h': 'h',
            'TS': 'TS', 'ts': 'ts',
            'C': 'C', 'c': 'c',
            'W': 'W', 'w': 'w',
            'WQ': 'WQ', 'wq': 'wq',
            'Q': 'Q', 'q': 'q',
            'Y': 'Y', 'y': 'y',
            'Q': 'Q', 'q': 'q',
            'JE': 'JE', 'je': 'je',
            'JU': 'JU', 'ju': 'ju',
            'JA': 'JA', 'ja': 'ja',
        };

        // Define exception patterns and their replacements
        const exceptions = [
            [/tsy/gi, 'tsy'],
            [/wu/gi, 'wu'],
            [/wy/gi, 'wy'],
            [/wy/gi, 'wy'],
            [/wi/gi, 'wi'],
            [/xi/gi, 'xi'],
            [/cu/gi, 'cu'],
            [/([xwhtscwq])(q)(?=[^a-jajo]|$)/gi, '$1'],  // Remove final soft sign after sibilants if not followed by a vowel
            [/tq?sja(?![a-jajo])/gi, 'tsa'],  // Replace -tsa and -tsja with 'tsa' if not followed by a vowel
        ];

        // Apply exception replacements
        exceptions.forEach(([pattern, replacement]) => {
            text = text.replace(pattern, replacement);
        });

        let result = "";
        for (let i = 0; i < text.length; i++) {
            let char = text[i];
            if (charMap[char]) {
                result += charMap[char];
            }
            else {
                result += char;
            }
        }
        return result;
    }

    function processNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            node.textContent = transliterate(node.textContent);
        }
        else if (node.nodeType === Node.ELEMENT_NODE) {
            node.childNodes.forEach(processNode);
        }
    }

    processNode(document.body);

    // Process new nodes added to DOM
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(processNode);
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
