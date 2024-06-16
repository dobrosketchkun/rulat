// ==UserScript==
// @name         RuLat
// @namespace    http://tampermonkey.net/
// @version      1.8
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
            'А': 'A', 'а': 'a',
            'Б': 'B', 'б': 'b',
            'В': 'V', 'в': 'v',
            'Г': 'G', 'г': 'g',
            'Д': 'D', 'д': 'd',
            'Е': 'E', 'е': 'e',
            'Ё': 'JO', 'ё': 'jo',
            'Ж': 'X', 'ж': 'x',
            'З': 'Z', 'з': 'z',
            'И': 'I', 'и': 'i',
            'Й': 'J', 'й': 'j',
            'К': 'K', 'к': 'k',
            'Л': 'L', 'л': 'l',
            'М': 'M', 'м': 'm',
            'Н': 'N', 'н': 'n',
            'О': 'O', 'о': 'o',
            'П': 'P', 'п': 'p',
            'Р': 'R', 'р': 'r',
            'С': 'S', 'с': 's',
            'Т': 'T', 'т': 't',
            'У': 'U', 'у': 'u',
            'Ф': 'F', 'ф': 'f',
            'Х': 'H', 'х': 'h',
            'Ц': 'TS', 'ц': 'ts',
            'Ч': 'C', 'ч': 'c',
            'Ш': 'W', 'ш': 'w',
            'Щ': 'WQ', 'щ': 'wq',
            'Ъ': 'Q', 'ъ': 'q',
            'Ы': 'Y', 'ы': 'y',
            'Ь': 'Q', 'ь': 'q',
            'Э': 'JE', 'э': 'je',
            'Ю': 'JU', 'ю': 'ju',
            'Я': 'JA', 'я': 'ja',
        };

        // Define exception patterns and their replacements
        const exceptions = [
            [/цы/gi, 'tsy'],
            [/шю/gi, 'wu'],
            [/ши/gi, 'wy'],
            [/шы/gi, 'wy'],
            [/щи/gi, 'wi'],
            [/жы/gi, 'xi'],
            [/чю/gi, 'cu'],
            [/([жшхцчщ])(ь)(?=[^а-яё]|$)/gi, '$1'],  // Remove final soft sign after sibilants if not followed by a vowel
            [/ть?ся(?![а-яё])/gi, 'tsa'],  // Replace -ться and -тся with 'tsa' if not followed by a vowel
        ];

        // Apply exception replacements
        exceptions.forEach(([pattern, replacement]) => {
            text = text.replace(pattern, replacement);
        });

        let result = "";
        for (let i = 0; i < text.length; i++) {
            let char = text[i];
            if (charMap[char]) {
                let transliterated = charMap[char];
                let isAllCaps = true;
                let j = i;
                while (j < text.length && charMap[text[j]]) {
                    if (text[j] === text[j].toLowerCase()) {
                        isAllCaps = false;
                        break;
                    }
                    j++;
                }
                if (isAllCaps) {
                    result += transliterated.toUpperCase();
                } else if (char === char.toUpperCase() && (i === 0 || text[i-1].match(/[^a-zа-яё0-9]/i))) {
                    result += transliterated[0].toUpperCase() + transliterated.slice(1).toLowerCase();
                } else {
                    result += transliterated.toLowerCase();
                }
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
