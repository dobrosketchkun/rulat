// Transliteration cases from tests/cases.json, shared with test_rulat.py
// node tests/test_userscript.js
const path = require('path');
const { transliterate, transliterateParts } = require(path.join(__dirname, '..', 'tampermonkey_userscript_rulat.js'));
const cases = require('./cases.json');

// A list is the text of one paragraph split by tags
const run = source => Array.isArray(source) ? transliterateParts(source) : transliterate(source);
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

let total = 0;
let failed = 0;

function check(name, source, actual, expected) {
    total++;
    if (!same(actual, expected)) {
        failed++;
        console.log(`FAIL ${name}: ${JSON.stringify(source)} -> ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
    }
}

for (const [category, list] of Object.entries(cases)) {
    for (const [source, expected] of list) {
        check(category, source, run(source), expected);
        // Romanized text has no Russian letters left, so it must not change again
        check(`${category} (idempotent)`, expected, run(expected), expected);
        // Splitting a paragraph between words must not change the result
        if (!Array.isArray(source)) {
            check(`${category} (split by whitespace)`, source, transliterateParts(source.split(/(\s+)/)).join(''), expected);
        }
    }
}

console.log(`${total - failed}/${total} passed`);
process.exit(failed ? 1 : 0);
