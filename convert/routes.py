import os
import uuid
import zipfile
import camelot
from flask import render_template, request, send_file, after_this_request, jsonify, current_app
from pdf2docx import Converter
from . import convert_bp

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
                    current_app.logger.info(f'Начинаем конвертацию в Word: {file.filename}')
                    cv = Converter(input_path)
                    cv.convert(output_path, start=0, end=None)
                    cv.close()
                elif format_selected == 'xlsx':
                    current_app.logger.info(f'Начинаем конвертацию в Excel: {file.filename}')
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
                current_app.logger.info(f'Файл обработан: {file.filename} → {output_ext}')

            except Exception as e:
                current_app.logger.error(f'Ошибка при обработке файла {file.filename}: {str(e)}')

            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)

    if not processed_files:
        current_app.logger.warning('Ни один файл не был успешно обработан')
        return jsonify({'error': 'Не удалось обработать ни один файл'}), 400

    @after_this_request
    def remove_file(response):
        try:
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
                current_app.logger.info(f'Удалён архив: {zip_filename}')
        except Exception as e:
            current_app.logger.warning(f"Не удалось удалить zip: {e}")
        return response

    current_app.logger.info(f'Успешно отправлен архив с {len(processed_files)} файлами')
    return send_file(zip_filename, as_attachment=True, download_name='result.zip')
