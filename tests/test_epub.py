"""EPUB processing tests: only the Russian text may change, every other byte stays.

python -m unittest discover tests
"""
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from epub_rulat import process_epub, transliterate_file, transliterate_markup


class TestMarkup(unittest.TestCase):
    def check(self, source, expected):
        self.assertEqual(transliterate_markup(source), expected)

    def test_text(self):
        self.check('<p>Привет, мир!</p>', '<p>Privet, mir!</p>')

    def test_xhtml11_doctype_and_named_entities_kept(self):
        self.check(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
            '<p>Да&nbsp;нет&mdash;может &laquo;быть&raquo; &amp; &lt;тег&gt;</p></body></html>',
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
            '<p>Da&nbsp;net&mdash;moxet &laquo;bytq&raquo; &amp; &lt;teg&gt;</p></body></html>')

    def test_doctype_with_internal_subset_kept(self):
        self.check('<!DOCTYPE html [<!ENTITY нечто "Щ">]><p>Щука</p>',
                   '<!DOCTYPE html [<!ENTITY нечто "Щ">]><p>Wcuka</p>')

    def test_markup_kept_exactly(self):
        # Empty elements, attribute order and quotes, namespaces, whitespace
        self.check(
            '<html xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ru">\n'
            '<head><meta charset="utf-8"><script src="a.js"></script></head>\n'
            "<body><section epub:type='chapter' id=\"s\"><a id=\"p1\"></a><div></div><br/>\n"
            '<p class="Щ" title="Привет &amp; пока">Текст<sup><a epub:type="noteref" href="#n1">1</a></sup></p>\n'
            '<pre>  код   с   пробелами\n  строка</pre></section></body></html>',
            '<html xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ru">\n'
            '<head><meta charset="utf-8"><script src="a.js"></script></head>\n'
            "<body><section epub:type='chapter' id=\"s\"><a id=\"p1\"></a><div></div><br/>\n"
            '<p class="Щ" title="Привет &amp; пока">Tekst<sup><a epub:type="noteref" href="#n1">1</a></sup></p>\n'
            '<pre>  kod   s   probelami\n  stroka</pre></section></body></html>')

    def test_attribute_with_angle_bracket(self):
        self.check('<p title="a > b">Щи</p>', '<p title="a > b">Wci</p>')

    def test_comments_cdata_and_processing_instructions_kept(self):
        self.check(
            '<?xml version="1.0"?><?xml-stylesheet href="s.css"?><!-- коммент -->'
            '<p><![CDATA[Щ < Ш]]> Щука</p>',
            '<?xml version="1.0"?><?xml-stylesheet href="s.css"?><!-- коммент -->'
            '<p><![CDATA[Щ < Ш]]> Wcuka</p>')

    def test_script_and_style_untouched(self):
        self.check(
            '<script>//<![CDATA[\nif (a < b && c) { s = "Щука"; }\n//]]></script>'
            '<style type="text/css">p:before { content: "Щ"; }</style><SCRIPT>"Я"</SCRIPT><p>Я</p>',
            '<script>//<![CDATA[\nif (a < b && c) { s = "Щука"; }\n//]]></script>'
            '<style type="text/css">p:before { content: "Щ"; }</style><SCRIPT>"Я"</SCRIPT><p>Ja</p>')

    def test_self_closed_script_does_not_swallow_text(self):
        self.check('<script src="a.js"/><p>Щука</p>', '<script src="a.js"/><p>Wcuka</p>')

    def test_plain_html_not_restructured(self):
        self.check(
            '<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>Т</title></head>'
            '<body><p>Один<br>два<p>Три &nbsp; <img src="a.jpg"> четыре</body></html>',
            '<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>T</title></head>'
            '<body><p>Odin<br>dva<p>Tri &nbsp; <img src="a.jpg"> cetyre</body></html>')

    def test_numeric_references_to_russian_letters(self):
        self.check('<p>&#1071; &#x417;&#1053;&#1040;&#1070; &#169; &#x2014;</p>',
                   '<p>JA ZNAJU &#169; &#x2014;</p>')

    def test_soft_hyphens_kept_as_written(self):
        self.check('<p>при&shy;мер, при&#173;мер, при&#xAD;мер, при­мер</p><p>ПРИ&shy;МЕР Я</p>',
                   '<p>pri&shy;mer, pri&#173;mer, pri&#xAD;mer, pri­mer</p><p>PRI&shy;MER JA</p>')

    def test_stress_marks_kept_as_written(self):
        self.check('<p>Ру&#769;сский Э&#x301;ТО Я&#769; ЗНА́Ю</p>',
                   '<p>Ru&#769;sskij E&#x301;QTO JA&#769; ZNÁJU</p>')

    def test_joiners_in_skipped_text_untouched(self):
        self.check('<script>при&shy;мер</script><dc:identifier>при&shy;мер</dc:identifier><p>Щ&shy;</p>',
                   '<script>при&shy;мер</script><dc:identifier>при&shy;мер</dc:identifier><p>Wc&shy;</p>')

    def test_less_than_sign_in_html(self):
        # Like in browsers: < before a letter starts a tag, other < is text
        self.check('<p>Щука < 5 кг, 3<4</p>', '<p>Wcuka < 5 kg, 3<4</p>')
        self.check('<p>Щука <b class="x">кот</b></p>', '<p>Wcuka <b class="x">kot</b></p>')

    def test_caps_across_inline_tags(self):
        self.check('<h1>Я <i>ЗНАЮ</i></h1><p><b>Ю</b>ЛЯ сказала: «Я знаю».</p>',
                   '<h1>JA <i>ZNAJU</i></h1><p><b>JU</b>LJA skazala: «Ja znaju».</p>')

    def test_caps_across_entities_and_comments(self):
        self.check('<p>Я&nbsp;ЗНАЮ</p><p>ЗНА<!-- x -->Ю Я</p>', '<p>JA&nbsp;ZNAJU</p><p>ZNA<!-- x -->JU JA</p>')

    def test_namespaced_inline_tags(self):
        self.check('<h:p>Я <h:b>ЗНАЮ</h:b></h:p>', '<h:p>JA <h:b>ZNAJU</h:b></h:p>')

    def test_paragraphs_are_separate(self):
        self.check('<div>Я <p>ЗНАЮ</p></div><p>Я</p><p>ЗНАЮ</p><p>Я<br/>ЗНАЮ</p>',
                   '<div>Ja <p>ZNAJU</p></div><p>Ja</p><p>ZNAJU</p><p>Ja<br/>ZNAJU</p>')

    def test_opf(self):
        self.check(
            '<package unique-identifier="id"><metadata>'
            '<dc:identifier id="id">книга-123</dc:identifier><dc:identifier/>'
            '<dc:title>Алиса в Стране чудес</dc:title><dc:creator id="c">Льюис Кэрролл</dc:creator>'
            '<meta refines="#c" property="file-as">Кэрролл, Льюис</meta>'
            '<meta name="cover" content="обложка"/><dc:language>ru</dc:language></metadata>'
            '<manifest><item id="обложка" href="Обложка.jpg" media-type="image/jpeg"/></manifest></package>',
            '<package unique-identifier="id"><metadata>'
            '<dc:identifier id="id">книга-123</dc:identifier><dc:identifier/>'
            '<dc:title>Alisa v Strane cudes</dc:title><dc:creator id="c">Lqjuis Keqrroll</dc:creator>'
            '<meta refines="#c" property="file-as">Keqrroll, Lqjuis</meta>'
            '<meta name="cover" content="обложка"/><dc:language>ru</dc:language></metadata>'
            '<manifest><item id="обложка" href="Обложка.jpg" media-type="image/jpeg"/></manifest></package>')

    def test_ncx(self):
        self.check(
            '<navPoint id="n1"><navLabel><text>ГЛАВА I. Вниз по кроличьей норе</text></navLabel>'
            '<content src="ch1.xhtml"/></navPoint>',
            '<navPoint id="n1"><navLabel><text>GLAVA I. Vniz po krolicqej nore</text></navLabel>'
            '<content src="ch1.xhtml"/></navPoint>')

    def test_no_markup(self):
        self.check('', '')
        self.check('Щука', 'Wcuka')

    def test_idempotent(self):
        once = transliterate_markup('<p>Я&nbsp;<b>ЗНАЮ</b> &#1071;</p>')
        self.assertEqual(transliterate_markup(once), once)


class TestFileEncoding(unittest.TestCase):
    def test_utf8(self):
        self.assertEqual(transliterate_file('<p>Щука</p>'.encode('utf-8')), b'<p>Wcuka</p>')

    def test_bom_kept(self):
        self.assertEqual(transliterate_file(b'\xef\xbb\xbf' + '<p>Щука</p>'.encode('utf-8')),
                         b'\xef\xbb\xbf<p>Wcuka</p>')

    def test_declared_encoding_kept(self):
        source = '<?xml version="1.0" encoding="windows-1251"?><p>Щука</p>'.encode('cp1251')
        self.assertEqual(transliterate_file(source),
                         b'<?xml version="1.0" encoding="windows-1251"?><p>Wcuka</p>')

    def test_utf16(self):
        source = '﻿<?xml version="1.0" encoding="UTF-16"?><p>Щука</p>'.encode('utf-16-le')
        self.assertEqual(transliterate_file(source),
                         '﻿<?xml version="1.0" encoding="UTF-16"?><p>Wcuka</p>'.encode('utf-16-le'))

    def test_unchanged_file_is_the_same_bytes(self):
        source = b'<?xml version="1.0"?>\r\n<container>  no cyrillic  </container>'
        self.assertIs(transliterate_file(source), source)

    def test_undecodable_file_left_as_is(self):
        source = b'<p>\xff\xfe broken utf-8</p>'
        self.assertIs(transliterate_file(source), source)
        source = b'<?xml version="1.0" encoding="no-such-encoding"?><p>x</p>'
        self.assertIs(transliterate_file(source), source)


CHAPTER = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Глава первая</title><link rel="stylesheet" href="style.css" type="text/css"/></head>
<body><h1>Я <i>ЗНАЮ</i></h1><p>Да&nbsp;нет&mdash;может</p><a id="end"></a></body>
</html>'''

CHAPTER_EXPECTED = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Glava pervaja</title><link rel="stylesheet" href="style.css" type="text/css"/></head>
<body><h1>JA <i>ZNAJU</i></h1><p>Da&nbsp;net&mdash;moxet</p><a id="end"></a></body>
</html>'''

OPF = '''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0" unique-identifier="id">
<metadata><dc:identifier id="id">урн-книга-1</dc:identifier><dc:title>Алиса в Стране чудес</dc:title></metadata>
<manifest><item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/></manifest>
</package>'''

NCX = '''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="урн-книга-1"/></head>
<navMap><navPoint id="n1"><navLabel><text>Глава первая</text></navLabel><content src="ch1.xhtml"/></navPoint></navMap>
</ncx>'''

CONTAINER = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''

CSS = 'p:before { content: "Щука"; }'
IMAGE = bytes(range(256)) + 'Щука'.encode('utf-8')


class TestProcessEpub(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.input = os.path.join(self.dir.name, 'in.epub')
        self.output = os.path.join(self.dir.name, 'out.epub')
        with zipfile.ZipFile(self.input, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip')
            z.writestr('META-INF/container.xml', CONTAINER)
            z.writestr('content.opf', OPF)
            z.writestr('toc.ncx', NCX)
            z.writestr('ch1.xhtml', CHAPTER)
            z.writestr('style.css', CSS)
            z.writestr('images/cover.png', IMAGE, zipfile.ZIP_STORED)

    def tearDown(self):
        self.dir.cleanup()

    def convert(self):
        process_epub(self.input, self.output)
        return zipfile.ZipFile(self.output)

    def test_chapter(self):
        with self.convert() as z:
            self.assertEqual(z.read('ch1.xhtml').decode('utf-8'), CHAPTER_EXPECTED)

    def test_opf_title_converted_identifier_kept(self):
        with self.convert() as z:
            self.assertEqual(z.read('content.opf').decode('utf-8'),
                             OPF.replace('Алиса в Стране чудес', 'Alisa v Strane cudes'))

    def test_ncx_label_converted_uid_kept(self):
        with self.convert() as z:
            self.assertEqual(z.read('toc.ncx').decode('utf-8'), NCX.replace('Глава первая', 'Glava pervaja'))

    def test_other_files_byte_identical(self):
        with self.convert() as z:
            self.assertEqual(z.read('META-INF/container.xml').decode('utf-8'), CONTAINER)
            self.assertEqual(z.read('style.css').decode('utf-8'), CSS)
            self.assertEqual(z.read('images/cover.png'), IMAGE)

    def test_zip_structure_kept(self):
        with zipfile.ZipFile(self.input) as original, self.convert() as z:
            self.assertEqual(z.namelist(), original.namelist())
            for before, after in zip(original.infolist(), z.infolist()):
                self.assertEqual(after.compress_type, before.compress_type, after.filename)
                self.assertEqual(after.date_time, before.date_time, after.filename)
            self.assertEqual(z.infolist()[0].filename, 'mimetype')
            self.assertEqual(z.infolist()[0].compress_type, zipfile.ZIP_STORED)
            self.assertIsNone(z.testzip())

    def test_input_unchanged(self):
        with open(self.input, 'rb') as f:
            before = f.read()
        self.convert().close()
        with open(self.input, 'rb') as f:
            self.assertEqual(f.read(), before)

    def test_same_file_refused(self):
        with open(self.input, 'rb') as f:
            before = f.read()
        with self.assertRaises(ValueError):
            process_epub(self.input, self.input)
        with open(self.input, 'rb') as f:
            self.assertEqual(f.read(), before)

    def test_existing_output_overwritten(self):
        with open(self.output, 'wb') as f:
            f.write(b'old')
        self.convert().close()
        self.assertTrue(zipfile.is_zipfile(self.output))

    def test_failure_leaves_nothing_behind(self):
        with open(self.input, 'wb') as f:
            f.write(b'not a zip')
        with open(self.output, 'wb') as f:
            f.write(b'old')
        with self.assertRaises(zipfile.BadZipFile):
            process_epub(self.input, self.output)
        # The existing output is not replaced by a broken file, no temporary files left
        with open(self.output, 'rb') as f:
            self.assertEqual(f.read(), b'old')
        self.assertEqual(sorted(os.listdir(self.dir.name)), ['in.epub', 'out.epub'])


class TestCommandLine(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(ROOT, 'epub_rulat.py'), *args],
                              capture_output=True)

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            book = os.path.join(d, 'book.epub')
            with zipfile.ZipFile(book, 'w') as z:
                z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip')
                z.writestr('ch1.xhtml', '<p>Щука</p>')
            self.assertEqual(self.run_cli(book, os.path.join(d, 'out.epub')).returncode, 0)
            self.assertEqual(self.run_cli(os.path.join(d, 'missing.epub'), os.path.join(d, 'x.epub')).returncode, 1)
            self.assertEqual(self.run_cli(book, book).returncode, 1)
            with open(os.path.join(d, 'bad.epub'), 'wb') as f:
                f.write(b'not a zip')
            self.assertEqual(self.run_cli(os.path.join(d, 'bad.epub'), os.path.join(d, 'y.epub')).returncode, 1)
            self.assertFalse(os.path.exists(os.path.join(d, 'y.epub')))


if __name__ == '__main__':
    unittest.main()
