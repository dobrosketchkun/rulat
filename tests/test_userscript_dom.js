// Userscript behavior on a page, needs jsdom: npm install
// node tests/test_userscript_dom.js
const fs = require('fs');
const path = require('path');

let JSDOM;
try {
    ({ JSDOM } = require('jsdom'));
} catch (e) {
    console.log('SKIPPED: needs jsdom, run npm install');
    process.exit(0);
}

const script = fs.readFileSync(path.join(__dirname, '..', 'tampermonkey_userscript_rulat.js'), 'utf8');

function load(body) {
    const dom = new JSDOM(`<!DOCTYPE html><html><head><title>Тест</title></head><body>${body}</body></html>`,
        { runScripts: 'outside-only' });
    const { window } = dom;
    // jsdom has no isContentEditable, emulate the browser one
    Object.defineProperty(window.HTMLElement.prototype, 'isContentEditable', {
        get() { return this.closest('[contenteditable]:not([contenteditable="false"])') !== null; },
    });
    window.eval(script);
    return window;
}

// Lets the MutationObserver run
const tick = () => new Promise(resolve => setTimeout(resolve, 5));

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

function equal(actual, expected) {
    if (actual !== expected) throw new Error(`got ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
}

test('plain text', async () => {
    const window = load('<p>Привет, мир!</p>');
    equal(window.document.body.innerHTML, '<p>Privet, mir!</p>');
});

test('caps across inline tags', async () => {
    const window = load('<h1>Я <b>ЗНАЮ</b></h1><p>Я <a href="#"><i>ЗНАЮ</i></a></p>');
    equal(window.document.body.innerHTML, '<h1>JA <b>ZNAJU</b></h1><p>JA <a href="#"><i>ZNAJU</i></a></p>');
});

test('word split across inline tags', async () => {
    const window = load('<p><b>Ю</b>ЛЯ и <b>Щ</b>ука</p>');
    equal(window.document.body.innerHTML, '<p><b>JU</b>LJA i <b>Wc</b>uka</p>');
});

test('nested block is a separate paragraph', async () => {
    const window = load('<div>Я <p>ЗНАЮ</p></div><ul><li>Я</li><li>ЗНАЮ</li></ul>');
    equal(window.document.body.innerHTML, '<div>Ja <p>ZNAJU</p></div><ul><li>Ja</li><li>ZNAJU</li></ul>');
});

test('table cells are separate paragraphs', async () => {
    const window = load('<table><tbody><tr><td>Я</td><td>ЗНАЮ</td></tr></tbody></table>');
    equal(window.document.querySelector('tr').innerHTML, '<td>Ja</td><td>ZNAJU</td>');
});

test('script, style, noscript, textarea untouched', async () => {
    const body = '<script>var s = "скрипт";</script><style>p:before{content:"Щ"}</style>'
        + '<noscript>нет скриптов</noscript><textarea>не трогать</textarea>';
    const window = load(body);
    equal(window.document.body.innerHTML, body);
});

test('editable content untouched', async () => {
    const window = load('<div contenteditable="true">редактор <b>жирный</b></div><p>текст <span contenteditable="true">правка</span></p>');
    equal(window.document.body.innerHTML,
        '<div contenteditable="true">редактор <b>жирный</b></div><p>tekst <span contenteditable="true">правка</span></p>');
});

test('attributes untouched', async () => {
    const window = load('<p title="Привет"><img alt="Кот">кот</p>');
    equal(window.document.body.innerHTML, '<p title="Привет"><img alt="Кот">kot</p>');
});

test('added paragraph', async () => {
    const window = load('<div id="root"></div>');
    const root = window.document.getElementById('root');
    root.innerHTML = '<p>Новый <b>текст</b></p>';
    await tick();
    equal(root.innerHTML, '<p>Novyj <b>tekst</b></p>');
});

test('added text after an all-caps word', async () => {
    const window = load('<p id="p">ЗНАЮ</p>');
    const p = window.document.getElementById('p');
    p.appendChild(window.document.createTextNode(' Я'));
    await tick();
    equal(p.innerHTML, 'ZNAJU JA');
});

test('all-caps word added after a single letter', async () => {
    const window = load('<p id="p">Я </p>');
    const p = window.document.getElementById('p');
    equal(p.innerHTML, 'Ja ');
    const b = window.document.createElement('b');
    b.textContent = 'ЗНАЮ';
    p.appendChild(b);
    await tick();
    equal(p.innerHTML, 'JA <b>ZNAJU</b>');
});

test('lowercase word added after a single letter', async () => {
    const window = load('<p id="p">Я </p>');
    const p = window.document.getElementById('p');
    p.appendChild(window.document.createTextNode('знаю'));
    await tick();
    equal(p.innerHTML, 'Ja znaju');
});

test('text changed in place', async () => {
    const window = load('<p id="p">кот</p>');
    const p = window.document.getElementById('p');
    p.firstChild.nodeValue = 'Щука плывёт';
    await tick();
    equal(p.innerHTML, 'Wcuka plyvjot');
});

test('page replaces converted text with new text', async () => {
    const window = load('<p id="p">Я <b>знаю</b></p>');
    const p = window.document.getElementById('p');
    equal(p.innerHTML, 'Ja <b>znaju</b>');
    p.querySelector('b').firstChild.nodeValue = 'ЗНАЮ';
    await tick();
    equal(p.innerHTML, 'JA <b>ZNAJU</b>');
    p.querySelector('b').firstChild.nodeValue = 'знаем';
    await tick();
    equal(p.innerHTML, 'Ja <b>znaem</b>');
});

test('page sets Latin text', async () => {
    const window = load('<p id="p">кот</p>');
    const p = window.document.getElementById('p');
    p.firstChild.nodeValue = 'cat';
    await tick();
    equal(p.innerHTML, 'cat');
});

test('removed nodes do not break processing', async () => {
    const window = load('<div id="root"><p>один</p><p id="gone">два</p></div>');
    const root = window.document.getElementById('root');
    root.removeChild(window.document.getElementById('gone'));
    root.appendChild(window.document.createTextNode('три'));
    await tick();
    equal(root.innerHTML, '<p>odin</p>tri');
});

test('settles without endless updates', async () => {
    const window = load('<p id="p">Я </p>');
    const p = window.document.getElementById('p');
    let changes = 0;
    new window.MutationObserver(list => { changes += list.length; })
        .observe(p, { childList: true, characterData: true, subtree: true });
    p.appendChild(window.document.createTextNode('ЗНАЮ'));
    await tick();
    await tick();
    const settled = changes;
    await tick();
    await tick();
    equal(changes, settled);
    equal(p.innerHTML, 'JA ZNAJU');
});

(async () => {
    let failed = 0;
    for (const { name, fn } of tests) {
        try {
            await fn();
        } catch (e) {
            failed++;
            console.log(`FAIL ${name}: ${e.message}`);
        }
    }
    console.log(`${tests.length - failed}/${tests.length} passed`);
    process.exit(failed ? 1 : 0);
})();
