import os
import re
import sys
import codecs
import zipfile
import argparse
import tempfile
from rulat import JOINERS, transliterate_parts

# Files with text to transliterate, everything else is copied as is
TEXT_EXTENSIONS = ('.html', '.xhtml', '.htm', '.xml', '.ncx', '.opf')

# Text inside these tags belongs to the surrounding paragraph
INLINE_TAGS = {
    'a', 'abbr', 'b', 'big', 'cite', 'code', 'del', 'dfn', 'em', 'font', 'i',
    'ins', 'kbd', 'mark', 'q', 's', 'samp', 'small', 'span', 'strike',
    'strong', 'sub', 'sup', 'u', 'var',
}

# Text of these tags is data, not prose. The OPF identifier is also the key
# for obfuscated fonts, so changing it would break them.
SKIP_TAGS = {'identifier'}

# The markup is never parsed and re-serialized, only the text between tags is
# replaced, so entities, comments, doctype, encoding etc. stay byte-identical.
TOKEN = re.compile(r'''
      <!--.*?-->
    | <!\[CDATA\[.*?\]\]>
    | <\?.*?\?>
    | <!DOCTYPE(?:[^\[>]|\[.*?\])*>
    | <(?P<raw>script|style)\b[^>]*?(?<!/)>.*?</(?P=raw)\s*>
    | </?[A-Za-z][^>"']*(?:(?:"[^"]*"|'[^']*')[^>"']*)*>
    | &\#(?:[0-9]+|[xX][0-9a-fA-F]+);
    | &[A-Za-z][A-Za-z0-9]*;
''', re.S | re.X | re.I)

TAG_NAME = re.compile(r'</?([^\s/>]+)')
CYRILLIC_LETTER = re.compile('[а-яёА-ЯЁ]')
# Soft hyphens and stress marks, they don't split a word: при&shy;мер
JOINER = re.compile(f'[{JOINERS}]')


def transliterate_markup(markup):
    out = []
    paragraph = []  # indices in out of the current paragraph's text pieces
    joiners = {}  # text piece index -> how each joiner in it was written: &shy;, &#769; or as is
    skip = False

    def add_text(text, written=None):
        if skip:
            out.append(written or text)
            return
        written = [written] if written else JOINER.findall(text)
        if paragraph and paragraph[-1] == len(out) - 1:
            out[-1] += text
            joiners[len(out) - 1] += written
        else:
            out.append(text)
            paragraph.append(len(out) - 1)
            joiners[len(out) - 1] = written

    def flush():
        texts = transliterate_parts([out[i] for i in paragraph])
        for i, text in zip(paragraph, texts):
            # Put the joiners back the way they were written
            pieces = JOINER.split(text)
            out[i] = pieces[0] + ''.join(w + p for w, p in zip(joiners[i], pieces[1:]))
        paragraph.clear()

    pos = 0
    for match in TOKEN.finditer(markup):
        if match.start() > pos:
            add_text(markup[pos:match.start()])
        pos = match.end()
        token = match.group()

        if token.startswith('&#'):
            # Russian letters written as &#1071; are text too
            number = token[2:-1]
            char = chr(int(number[1:], 16) if number[0] in 'xX' else int(number))
            if CYRILLIC_LETTER.fullmatch(char):
                add_text(char)
                continue
            if JOINER.fullmatch(char):
                add_text(char, token)
                continue
        elif token == '&shy;':
            add_text('­', token)
            continue
        elif token.startswith('<') and token[1:2] not in ('!', '?') and not match.group('raw'):
            name = TAG_NAME.match(token).group(1).lower().split(':')[-1]
            if name not in INLINE_TAGS:
                flush()
            if name in SKIP_TAGS:
                skip = not token.startswith('</') and not token.endswith('/>')
        out.append(token)

    if pos < len(markup):
        add_text(markup[pos:])
    flush()
    return ''.join(out)


def detect_encoding(content):
    """Returns (encoding, BOM) of an XML/HTML file."""
    for bom, encoding in ((codecs.BOM_UTF8, 'utf-8'), (codecs.BOM_UTF16_LE, 'utf-16-le'),
                          (codecs.BOM_UTF16_BE, 'utf-16-be')):
        if content.startswith(bom):
            return encoding, bom
    match = re.match(rb'<\?xml[^>]*encoding\s*=\s*["\']([A-Za-z0-9._-]+)', content)
    return (match.group(1).decode('ascii') if match else 'utf-8'), b''


def transliterate_file(content):
    encoding, bom = detect_encoding(content)
    try:
        text = content[len(bom):].decode(encoding)
    except (LookupError, UnicodeDecodeError):
        return content
    new_text = transliterate_markup(text)
    if new_text == text:
        return content
    # Transliterated text is plain Latin, so it fits any encoding the file used
    return bom + new_text.encode(encoding)


def process_epub(input_path, output_path):
    if os.path.exists(output_path) and os.path.samefile(input_path, output_path):
        raise ValueError('input and output are the same file')
    # Write to a temporary file first, so a failure never leaves a broken output
    fd, temp_path = tempfile.mkstemp(suffix='.epub', dir=os.path.dirname(os.path.abspath(output_path)))
    os.close(fd)
    try:
        with zipfile.ZipFile(input_path, 'r') as zip_ref, zipfile.ZipFile(temp_path, 'w') as zip_out:
            for file_info in zip_ref.infolist():
                content = zip_ref.read(file_info)
                if file_info.filename.lower().endswith(TEXT_EXTENSIONS):
                    content = transliterate_file(content)
                # Same ZipInfo keeps the order, compression and dates, mimetype stays first and stored
                zip_out.writestr(file_info, content)
        os.replace(temp_path, output_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    parser = argparse.ArgumentParser(description='Transliterate Russian text in EPUB files. // Транслитерирует русский текст внутри epub формата')
    parser.add_argument('input', help='Input EPUB file path // Путь до epub файла')
    parser.add_argument('output', help='Output EPUB file path // Путь до места сохранения результата')
    args = parser.parse_args()
    # Messages are partly in Russian, don't crash on consoles/pipes that can't show it
    sys.stdout.reconfigure(errors='replace')

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist. // ОШИБКА: Epub файл '{args.input}' не существует")
        sys.exit(1)

    if os.path.exists(args.output) and os.path.samefile(args.input, args.output):
        print(f"Error: Output must be a different file than input. // ОШИБКА: Результат нужно сохранить в другой файл, не в исходный.")
        sys.exit(1)

    if os.path.exists(args.output):
        print(f"Warning: Output file '{args.output}' already exists. It will be overwritten. // ВНИМАНИЕ: Файл '{args.output}' уже существует и будет перезаписан.")

    try:
        process_epub(args.input, args.output)
        print(f"Transliteration complete. Output saved to '{args.output}' // Результат сохранён в '{args.output}'")
    except Exception as e:
        print(f"Error occurred during processing: {str(e)} // Произошла следующая ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
