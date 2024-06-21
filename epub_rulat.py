import os
import re
import zipfile
import argparse
from bs4 import BeautifulSoup
from lxml import etree
import warnings

# Transliteration rules
char_map = {
    'А': 'A', 'а': 'a', 'Б': 'B', 'б': 'b', 'В': 'V', 'в': 'v', 'Г': 'G', 'г': 'g',
    'Д': 'D', 'д': 'd', 'Е': 'E', 'е': 'e', 'Ё': 'JO', 'ё': 'jo', 'Ж': 'X', 'ж': 'x',
    'З': 'Z', 'з': 'z', 'И': 'I', 'и': 'i', 'Й': 'J', 'й': 'j', 'К': 'K', 'к': 'k',
    'Л': 'L', 'л': 'l', 'М': 'M', 'м': 'm', 'Н': 'N', 'н': 'n', 'О': 'O', 'о': 'o',
    'П': 'P', 'п': 'p', 'Р': 'R', 'р': 'r', 'С': 'S', 'с': 's', 'Т': 'T', 'т': 't',
    'У': 'U', 'у': 'u', 'Ф': 'F', 'ф': 'f', 'Х': 'H', 'х': 'h', 'Ц': 'TS', 'ц': 'ts',
    'Ч': 'C', 'ч': 'c', 'Ш': 'W', 'ш': 'w', 'Щ': 'WQ', 'щ': 'wq', 'Ъ': 'Q', 'ъ': 'q',
    'Ы': 'Y', 'ы': 'y', 'Ь': 'Q', 'ь': 'q', 'Э': 'JE', 'э': 'je', 'Ю': 'JU', 'ю': 'ju',
    'Я': 'JA', 'я': 'ja'
}

# Exception patterns
exceptions = [
    (r'цы', 'tsy'),
    (r'шю', 'wu'),
    (r'ши', 'wy'),
    (r'шы', 'wy'),
    (r'щи', 'wi'),
    (r'жы', 'xi'),
    (r'чю', 'cu'),
    (r'([жшхцчщ])(ь)(?=[^а-яё]|$)', r'\1'),
    (r'ть?ся(?![а-яё])', 'tsa'),
]

def transliterate(text):
    # Apply exception replacements
    for pattern, replacement in exceptions:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    result = ""
    i = 0
    while i < len(text):
        char = text[i]
        if char in char_map:
            transliterated = char_map[char]
            # Check for all caps
            j = i
            is_all_caps = True
            while j < len(text) and text[j] in char_map:
                if text[j].islower():
                    is_all_caps = False
                    break
                j += 1
            
            # Apply capitalization rules
            if is_all_caps:
                result += transliterated.upper()
            elif char.isupper() and (i == 0 or not text[i-1].isalnum()):
                result += transliterated[0].upper() + transliterated[1:].lower()
            else:
                result += transliterated.lower()
        else:
            result += char
        i += 1
    
    return result

def process_epub(input_path, output_path):
    with zipfile.ZipFile(input_path, 'r') as zip_ref:
        with zipfile.ZipFile(output_path, 'w') as zip_out:
            for file_info in zip_ref.infolist():
                with zip_ref.open(file_info) as file:
                    content = file.read()
                    
                    if file_info.filename.endswith(('.html', '.xhtml', '.htm', '.xml')):
                        # Process HTML/XML files
                        soup = BeautifulSoup(content, 'lxml-xml')
                        for text_node in soup.find_all(text=True):
                            if text_node.parent.name not in ['script', 'style']:
                                new_text = transliterate(text_node.string)
                                text_node.replace_with(new_text)
                        content = str(soup).encode('utf-8')
                    elif file_info.filename.endswith('.opf'):
                        # Process OPF files
                        tree = etree.fromstring(content)
                        for elem in tree.iter():
                            if elem.text:
                                elem.text = transliterate(elem.text)
                            if elem.tail:
                                elem.tail = transliterate(elem.tail)
                        content = etree.tostring(tree, encoding='utf-8', xml_declaration=True)
                    
                    zip_out.writestr(file_info, content)

def main():
    parser = argparse.ArgumentParser(description='Transliterate Russian text in EPUB files. // Транслитерирует русский текст внутри epub формата')
    parser.add_argument('input', help='Input EPUB file path // Путь до epub файла')
    parser.add_argument('output', help='Output EPUB file path // Путь до места сохранения результата')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist. // ОШИБКА: Epub файл '{args.input}' не сущетсвуте")
        return

    if os.path.exists(args.output):
        print(f"Warning: Output file '{args.output}' already exists. It will be overwritten. // ВНИМАНИЕ: Файл '{args.output}' уже сущесвует и будет перезаписан.")

    try:
        process_epub(args.input, args.output)
        print(f"Transliteration complete. Output saved to '{args.output}' // Результат сохранён в  '{args.output}'")
    except Exception as e:
        print(f"Error occurred during processing: {str(e)} // Произошла следующая ошибка: {str(e)}")

if __name__ == "__main__":
    main()
