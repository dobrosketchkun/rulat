// ==UserScript==
// @name         RuLat
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  RuLat is an art-project user script
// @author       https://github.com/dobrosketchkun
// @match        http://*/*
// @match        https://*/*
// @grant        none
// @license      The Uncertain Commons License https://gist.github.com/dobrosketchkun/d0c6aba085fb4a910926616a8b83c4c5
// ==/UserScript==

(function() {
    'use strict';

    // Mapping from Cyrillic to Latin, see misc/rulat_table.png
    const letters = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'jo',
        'ж': 'x', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'c', 'ш': 'w', 'щ': 'wc', 'ъ': 'q',
        'ы': 'y', 'ь': 'q', 'э': 'eq', 'ю': 'ju', 'я': 'ja',
    };

    // Soft hyphens and combining marks (stress) inside a word don't split it: при­мер, Ру́сский
    const wordPattern = /[а-яёА-ЯЁ](?:[\u00ad\u0300-\u036f]*[а-яёА-ЯЁ])*/g;

    function isUpper(word) {
        return word === word.toUpperCase();
    }

    function romanizeWord(word, caps) {
        const out = [];
        for (const c of word) {
            let latin = letters[c.toLowerCase()];
            if (latin === undefined) {
                // A stress mark goes on the vowel: Э́ -> Éq, not Eq́
                const prev = out.length - 1;
                if (prev >= 0 && /[\u0300-\u036f]/.test(c)) {
                    const vowel = out[prev].match(/[aeiouy][\u0300-\u036f]*(?=[^aeiouy]*$)/i);
                    if (vowel) {
                        const end = vowel.index + vowel[0].length;
                        out[prev] = out[prev].slice(0, end) + c + out[prev].slice(end);
                        continue;
                    }
                }
                out.push(c);
                continue;
            }
            if (caps) latin = latin.toUpperCase();
            else if (c !== c.toLowerCase()) latin = latin[0].toUpperCase() + latin.slice(1);
            out.push(latin);
        }
        return out.join('');
    }

    function letterCount(word) {
        return (word.match(/[а-яёА-ЯЁa-zA-Z]/g) || []).length;
    }

    // For each word, whether the nearest longer word before it (in the order
    // of indices) is all-caps: true/false, or null if there is no such word
    function nearestCaps(words, indices) {
        const result = new Array(words.length).fill(null);
        let last = null;
        for (const i of indices) {
            result[i] = last;
            if (letterCount(words[i]) > 1) last = isUpper(words[i]);
        }
        return result;
    }

    // Latin words are not romanized, they only give context for all-caps:
    // already romanized text (when the page changes) or words like API
    const contextPattern = new RegExp(wordPattern.source + '|[a-zA-Z](?:[\u00ad\u0300-\u036f]*[a-zA-Z])*', 'g');
    const cyrillicWord = new RegExp('^(?:' + wordPattern.source + ')$');

    // Transliterate pieces of one paragraph (e.g. its text split by <b>, <i>
    // tags) together, so all-caps is decided across the whole paragraph
    function transliterateParts(parts) {
        const words = parts.flatMap(part => part.match(contextPattern) || []);
        const caps = words.map(w => letterCount(w) > 1 && isUpper(w));
        // A single capital letter (Я) is all-caps only if the nearest longer words
        // around it are: Я ЗНАЮ -> JA ZNAJU, but Я знаю -> Ja znaju
        const indices = words.map((_, i) => i);
        const before = nearestCaps(words, indices);
        const after = nearestCaps(words, indices.slice().reverse());
        words.forEach((w, i) => {
            if (letterCount(w) === 1 && isUpper(w)) {
                const sides = [before[i], after[i]].filter(s => s !== null);
                caps[i] = sides.length > 0 && sides.every(s => s);
            }
        });
        const cyrillicCaps = caps.filter((_, i) => cyrillicWord.test(words[i]));
        let i = 0;
        return parts.map(part => part.replace(wordPattern, word => romanizeWord(word, cyrillicCaps[i++])));
    }

    function transliterate(text) {
        return transliterateParts([text])[0];
    }

    // Allows running the tests in Node: tests/test_userscript.js
    if (typeof document === 'undefined') {
        module.exports = { transliterate, transliterateParts };
        return;
    }

    // Text inside these tags belongs to the surrounding paragraph
    const inlineTags = new Set([
        'A', 'ABBR', 'B', 'BIG', 'CITE', 'CODE', 'DEL', 'DFN', 'EM', 'FONT', 'I',
        'INS', 'KBD', 'MARK', 'Q', 'S', 'SAMP', 'SMALL', 'SPAN', 'STRIKE',
        'STRONG', 'SUB', 'SUP', 'U', 'VAR',
    ]);
    const skipSelector = 'script, style, noscript, textarea';

    function isInline(element) {
        return inlineTags.has(element.tagName);
    }

    function isSkipped(element) {
        return element.closest(skipSelector) !== null || element.isContentEditable;
    }

    function blockOf(element) {
        while (isInline(element) && element.parentElement) element = element.parentElement;
        return element;
    }

    // Text nodes of the paragraph: directly in the block or inside its inline tags
    function textNodesOf(block) {
        const walker = document.createTreeWalker(block, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
            acceptNode: node => {
                if (node.nodeType === Node.TEXT_NODE) return NodeFilter.FILTER_ACCEPT;
                return isInline(node) && !isSkipped(node) ? NodeFilter.FILTER_SKIP : NodeFilter.FILTER_REJECT;
            },
        });
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        return nodes;
    }

    // Original text of the nodes we changed, so a paragraph can be redone from it
    // when more text arrives later: "Я " + later "ЗНАЮ" -> JA ZNAJU
    const originals = new WeakMap();

    function processBlock(block) {
        if (!block.isConnected || isSkipped(block)) return;
        const nodes = textNodesOf(block);
        const sources = nodes.map(node => {
            const known = originals.get(node);
            // If the page has changed the text since, the new text is the original
            return known && known.result === node.nodeValue ? known.source : node.nodeValue;
        });
        const texts = transliterateParts(sources);
        nodes.forEach((node, i) => {
            // Only assign on change, otherwise the observer below would loop
            if (texts[i] !== node.nodeValue) node.nodeValue = texts[i];
            if (texts[i] !== sources[i]) originals.set(node, { source: sources[i], result: texts[i] });
            else originals.delete(node);
        });
    }

    // Collect the blocks whose text is affected by an added or changed node
    function addBlocks(node, blocks) {
        if (node.nodeType === Node.TEXT_NODE) {
            if (node.parentElement) blocks.add(blockOf(node.parentElement));
        }
        else if (node.nodeType === Node.ELEMENT_NODE) {
            blocks.add(blockOf(node));
            node.querySelectorAll('*').forEach(element => {
                if (!isInline(element)) blocks.add(element);
            });
        }
    }

    const blocks = new Set();
    addBlocks(document.body, blocks);
    blocks.forEach(processBlock);

    // Process new nodes added to DOM and text changed in existing ones
    const observer = new MutationObserver(mutations => {
        const changed = new Set();
        mutations.forEach(mutation => {
            if (mutation.type === 'characterData') addBlocks(mutation.target, changed);
            else mutation.addedNodes.forEach(node => addBlocks(node, changed));
        });
        changed.forEach(processBlock);
    });
    observer.observe(document.body, { childList: true, characterData: true, subtree: true });
})();
