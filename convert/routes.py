import os
import uuid
import zipfile
import camelot
from flask import render_template, request, send_file, after_this_request, jsonify, current_app
from pdf2docx import Converter
from . import convert_bp

# OCR
import pytesseract
from pdf2image import convert_from_path
from docx import Document
from PyPDF2 import PdfReader


def is_text_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            return True
    return False

def ocr_pdf_to_docx(pdf_path, output_path):
    current_app.logger.info(f'OCR: запуск распознавания PDF {pdf_path}')
    images = convert_from_path(pdf_path, dpi=300)
    doc = Document()

    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image, lang='rus+eng')
        doc.add_paragraph(text)
        if i < len(images) - 1:
            doc.add_page_break()

    doc.save(output_path)
    current_app.logger.info(f'OCR: сохранён результат в {output_path}')


@convert_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@convert_bp.route('/convert', methods=['POST'])
def convert_pdf():
    files = request.files.getlist('file')
    format_selected = request.form.get('format')

    if not files or not format_selected:
        current_app.logger.warning("Пользователь не выбрал файлы или формат")
        return jsonify({'error': 'Файлы или формат не указаны'}), 400

    zip_filename = 'converted.zip'
    processed_files = []

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for file in files:
            try:
                uid = uuid.uuid4().hex
                input_path = f'{uid}_input.pdf'
                output_ext = 'docx' if format_selected == 'docx' else 'xlsx'
                output_path = f'{uid}_output.{output_ext}'

                file.save(input_path)
                current_app.logger.info(f'Получен файл: {file.filename}, формат: {format_selected}')

                if format_selected == 'docx':
                    if is_text_pdf(input_path):
                        current_app.logger.info(f'Конвертация в Word: обычный PDF')
                        cv = Converter(input_path)
                        cv.convert(output_path, start=0, end=None)
                        cv.close()
                    else:
                        current_app.logger.info(f'Файл без текста — используется OCR')
                        ocr_pdf_to_docx(input_path, output_path)

                elif format_selected == 'xlsx':
                    current_app.logger.info(f'Конвертация в Excel')
                    tables = camelot.read_pdf(input_path, pages='all', flavor='stream', backend='pdfium')
                    if len(tables) == 0:
                        current_app.logger.warning(f'Таблицы не найдены в {file.filename}, пропущен.')
                        continue
                    tables.export(output_path, f='excel')
                else:
                    current_app.logger.warning(f'Неверный формат: {format_selected}')
                    continue

                zipf.write(output_path, arcname=file.filename.replace('.pdf', f'.{output_ext}'))
                processed_files.append(output_path)

            except Exception as e:
                current_app.logger.error(f'Ошибка при обработке файла {file.filename}: {str(e)}')

            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)

    if not processed_files:
        return jsonify({'error': 'Не удалось обработать ни один файл'}), 400

    @after_this_request
    def remove_file(response):
        try:
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
                current_app.logger.info(f'Удалён zip: {zip_filename}')
        except Exception as e:
            current_app.logger.warning(f"Не удалось удалить zip: {e}")
        return response

    return send_file(zip_filename, as_attachment=True, download_name='result.zip')
