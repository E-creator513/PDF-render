from flask import Flask, request, send_from_directory, render_template, abort, jsonify
import os
from werkzeug.utils import secure_filename
import pdf_processing
import pandas as pd
import time
import tru
from fpdf import FPDF
import re
import requests
import json

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PDF_OUTPUT_FOLDER'] = 'pdf_outputs/'
app.config['DOWNLOAD_FOLDER'] = 'download/'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        if len(files) > 40:
            return render_template('upload.html', message="You can only upload up to 40 files.")
        
        all_data = []
        csv_list = []

        for file_index, file in enumerate(files, start=1):
            if file and file.filename:
                original_filename = file.filename
                filename = secure_filename(original_filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                print(f"File saved to: {file_path}")
                  
                match = re.search(r'Счет на оплату № (\d+)', original_filename)
                if match:
                    invoice_number = f"Счет на оплату № {match.group(1)}"
                else:
                    invoice_number = "UnknownInvoiceNumber"
                    print("No invoice number found in filename.") 
                    
                with open(file_path, 'rb') as file_stream:
                    processed_tables, contains_target_phrase, buyer_sentences = pdf_processing.process_pdf_file(file_stream, filename, invoice_number)
                    if processed_tables:
                        csv_paths = pdf_processing.save_tables_to_csv(processed_tables, app.config['UPLOAD_FOLDER'], f"output_table_{file_index}")
                        csv_list.extend(csv_paths)
                        for csv_path in csv_paths:
                            data = pd.read_csv(csv_path)
                            all_data.append({
                                'table': data.to_html(classes='table table-striped', index=False),
                                'csv_path': csv_path,
                                'filename': filename,
                                'contains_target_phrase': contains_target_phrase,
                                'buyer_sentence': buyer_sentences
                            })
                    else:
                        print(f"Failed to process PDF file: {filename}")
                        return render_template('upload.html', message=f"Failed to process PDF file: {filename}"), 400
            else:
                print("No file uploaded or file is invalid.")
                return render_template('upload.html', message="No file uploaded or file is invalid.")

        data_for_template = [{'table': item['table'], 'csv_path': item['csv_path'], 'filename': item['filename'], 'contains_target_phrase': item['contains_target_phrase'], 'buyer_sentence': item['buyer_sentence']} for item in all_data]
        return render_template('display_tables.html', tables=data_for_template)
    return render_template('upload.html')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    csv_path = request.form.get('csv_path')
    contains_target_phrase = request.form.get('contains_target_phrase') == 'True'
    pdf_files = []
    data = pd.read_csv(csv_path)
    index = 1
    for _, item in data.iterrows():
        pdf_path = pdf_processing.create_pdf1(item, index, app.config['PDF_OUTPUT_FOLDER']) if contains_target_phrase else pdf_processing.create_pdf(item, index, app.config['PDF_OUTPUT_FOLDER'])
        pdf_files.append(pdf_path)
        index += 1
    merged_pdf_path = pdf_processing.merge_pdfs(pdf_files, os.path.join(app.config['PDF_OUTPUT_FOLDER'], 'Combined.pdf'))
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], 'Combined.pdf', as_attachment=True)


@app.route('/download-pdf/<path:csv_filename>', methods=['GET'])
def download_pdf(csv_filename):
    # Paths
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    pdf_filename = f"{os.path.splitext(csv_filename)[0]}_standard.pdf"
    output_pdf_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
    buyer_sentences = request.args.getlist('buyer_sentences')
    # Generate PDF
    csv_to_pdf(csv_path, output_pdf_path)

    # Serve the PDF file for download
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], pdf_filename, as_attachment=True)

@app.route('/download-pdf1/<path:csv_filename>', methods=['GET'])
def download_pdf1(csv_filename):
    # Paths
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    pdf_filename = f"{os.path.splitext(csv_filename)[0]}_custom.pdf"
    output_pdf_path1 = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)

    # Get buyer sentences from query parameters
    buyer_sentences = request.args.getlist('buyer_sentences')

    # Generate PDF
    pdf_filename = csv_to_pdf1(csv_path, output_pdf_path1, buyer_sentences)

    # Serve the PDF file for download
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], pdf_filename, as_attachment=True)

def csv_to_pdf1(csv_path, output_pdf_path1, buyer_sentences=None):
    data = pd.read_csv(csv_path)

    # Initialize PDF object
    pdf = FPDF(orientation='L')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Add a frame around the page
    pdf.set_line_width(0.6)
    pdf.rect(5, 5, pdf.w - 10, pdf.h - 10)
    
    # Add custom fonts
    pdf.add_font('timesnrcyrmt_inclined', '', 'timesnrcyrmt_inclined.ttf', uni=True)
    pdf.add_font('timesnrcyrmt_bold', '', 'timesnrcyrmt_bold.ttf', uni=True)
    pdf.add_font('timesnrcyrmt', '', 'timesnrcyrmt.ttf', uni=True)

    # Set initial font
    pdf.set_font('timesnrcyrmt_inclined', '', 10)

    # Add company logo and header information
    pdf.image('ftkframe.jpeg', 260, 8, 29)
    pdf.set_xy(30, 10)
    pdf.cell(33, 10, 'ООО «ФТК»', 0, 1, '')
    pdf.set_xy(30, 13)
    pdf.cell(33, 13, '198095, Санкт-Петербург г, пер Химический, д. 1, литера АЦ, ЧАСТЬ ПОМ. 1-Н, ПОМ. 17', 0, 1, '')
    pdf.set_xy(30, 16)
    pdf.cell(33, 16, '+7 (905) 300-02-55', 0, 1, '')
    pdf.set_xy(30, 19)
    pdf.cell(33, 19, 'sale@techcomplekt.ru', 0, 1, '')
    pdf.set_xy(30, 22)
    pdf.cell(33, 22, 'metgost.ru', 0, 1, '')

    # Add certification image and description
    pdf.ln(20)
    pdf.image('est.png', 8, 42, 15)
    pdf.set_xy(25, 33)
    pdf.set_font('timesnrcyrmt_inclined', '', 8)
    pdf.cell(17, 28, 'СИСТЕМА МЕНЕДЖМЕНТА КАЧЕСТВА СЕРТИФИЦИРОВАНА НА СООТВЕТСТВИЕ ТРЕБОВАНИЯМ ГОСТ ISO 9001:2015 № РОСС RU.3745.04УЛЛ0 / СМК.2711-24', 0, 1, '')

    # Add document title
    pdf.set_font('timesnrcyrmt_bold', '', 16)
    pdf.set_xy(0, 39)
    pdf.cell(0, 39, 'Паспорт-сертификат № ___ от ___.___.20__ г.', 0, 2, 'C')
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.cell(0, 44, '(на партию отгруженного товара)', 0, 2, 'C')

    # Add a line separator
    pdf.set_line_width(0.6)
    pdf.line(17, 69, 280, 69)

    # Add company and customer details
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.set_xy(17, 50)
    pdf.cell(0, 10, 'Изготовитель: ', 0, 1, '')
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    pdf.set_xy(41, 50)
    pdf.cell(0, 10, 'ООО «ПФТ», ИНН 7819030811, КПП 781901001, 198207, г. Санкт-Петербург, Трамвайный проспект, д.6, тел.: 8(812)983-70-83', 0, 1, '')

    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.set_xy(17, 53)
    pdf.cell(0, 10, 'Поставщик: ', 0, 1, '')
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    pdf.set_xy(41, 53)
    pdf.cell(0, 10, 'ООО «ФТК», ИНН 6318048615, КПП 780501001, 198095, город Санкт-Петербург, Химический пер, д. 1 литера АЦ, часть пом. 1-н пом. 17', 0, 1, '')

    # Adding table rows
    header_height = 10
    row_height = 7

    pdf.set_font("timesnrcyrmt", '', 8)
    for index, row in data.iterrows():
        pdf.cell(10, row_height, str(index), 1)
        for item in row[:3]:
            pdf.cell(90, row_height, str(item), 1)
        pdf.ln()

    # Adjust Y position after the table
    pdf.set_y(pdf.get_y() + 5.04)

    # Add buyer sentences to the PDF
    pdf.set_font('timesnrcyrmt_inclined', '', 12)
    if buyer_sentences:
        for sentence in buyer_sentences:
            pdf.multi_cell(0, 10, sentence, align='L')
            pdf.ln(5)

    # Adding footer or conclusion data
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    footer_text = (
        "Дата изготовления: 2024 г.\n"
        "Страна производства: Россия\n"
        "Срок годности: Не ограничен\n"
        "Заключение: Продукция соответствует установленным техническим требованиям, "
        "по внешнему виду, размерам и механическим свойствам."
    )
    pdf.multi_cell(0, 10, footer_text)

    # Position signatures aligned to the right
    pdf.set_font('timesnrcyrmt', '', 10)
    current_y = pdf.get_y()
    pdf.set_xy(pdf.w - 105, current_y)

    # Add the signatures
    pdf.cell(0, 10, 'Директор:_____________________________Волков И.В.', 0, 1, 'R')
    pdf.cell(0, 10, 'Начальник ОТК:________________________Волков И.В.', 0, 1, 'R')

    # Save the PDF
    unique_filename = f"{os.path.splitext(os.path.basename(csv_path))[0]}_custom_{int(time.time())}.pdf"
    pdf.output(os.path.join(app.config['PDF_OUTPUT_FOLDER'], unique_filename))
    return unique_filename

def csv_to_pdf(csv_path, output_pdf_path):
    data = pd.read_csv(csv_path)
    
    pdf = FPDF(orientation='L')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Add custom fonts
    pdf.add_font('timesnrcyrmt_inclined', '', 'timesnrcyrmt_inclined.ttf', uni=True)
    pdf.add_font('timesnrcyrmt_bold', '', 'timesnrcyrmt_bold.ttf', uni=True)
    pdf.add_font('timesnrcyrmt', '', 'timesnrcyrmt.ttf', uni=True)
    
    pdf.set_font('timesnrcyrmt_inclined', '', 10)
    
    # Add company logo and header information
    pdf.image('logo.png', 10, 13, 26)
    pdf.set_xy(38, 10)
    pdf.cell(33, 10, 'ООО «ПФТ»', 0, 1, '')
    pdf.set_xy(38, 13)
    pdf.cell(33, 13, 'Санкт-Петербург, Трамвайный проспект, д.6', 0, 1, '')
    pdf.set_xy(38, 16)
    pdf.cell(33, 16, '+7 (812) 983-70-83, +7 (812) 123-45-67', 0, 1, '')
    pdf.set_xy(38, 19)
    pdf.cell(33, 19, 'info@pft.ru, www.pft.ru', 0, 1, '')
    
    # Add document title
    pdf.set_font('timesnrcyrmt_bold', '', 16)
    pdf.set_xy(0, 39)
    pdf.cell(0, 39, 'Паспорт-сертификат № ____ от __.__.20__ г.', 0, 2, 'C')
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.cell(0, 44, '(на партию отгруженного товара)', 0, 2, 'C')
    
    # Add a line separator
    pdf.set_line_width(0.6)
    pdf.line(10, 69, 280, 69)
    
    # Add company and customer details
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.set_xy(10, 50)
    pdf.cell(0, 10, 'Изготовитель: ', 0, 1, '')
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    pdf.set_xy(34, 50)
    pdf.cell(0, 10, 'ООО «ПФТ», ИНН 7819030811, КПП 781901001, 198207, г. Санкт-Петербург, Трамвайный проспект, д.6, тел.: 8(812)983-70-83', 0, 1, '')

    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.set_xy(10, 53)
    pdf.cell(0, 10, 'Поставщик: ', 0, 1, '')
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    pdf.set_xy(34, 53)
    pdf.cell(0, 10, 'ООО «ФТК», ИНН 6318048615, КПП 780501001, 198095, город Санкт-Петербург, Химический пер, д. 1 литера АЦ, часть пом. 1-н пом. 17', 0, 1, '')
    
    # Add a table
    header_height = 10
    row_height = 7

    pdf.set_font("timesnrcyrmt", '', 8)
    for index, row in data.iterrows():
        pdf.cell(10, row_height, str(index), 1)
        for item in row[:3]:
            pdf.cell(90, row_height, str(item), 1)
        pdf.ln()

    # Adjust Y position after the table
    pdf.set_y(pdf.get_y() + 5.04)

    # Adding footer or conclusion data
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    footer_text = (
        "Дата изготовления: 2024 г.\n"
        "Страна производства: Россия\n"
        "Срок годности: Не ограничен\n"
        "Заключение: Продукция соответствует установленным техническим требованиям, "
        "по внешнему виду, размерам и механическим свойствам."
    )
    pdf.multi_cell(0, 10, footer_text)

    # Position signatures aligned to the right
    pdf.set_font('timesnrcyrmt', '', 10)
    current_y = pdf.get_y()
    pdf.set_xy(pdf.w - 105, current_y)

    # Add the signatures
    pdf.cell(0, 10, 'Директор:_____________________________Волков И.В.', 0, 1, 'R')
    pdf.cell(0, 10, 'Начальник ОТК:________________________Волков И.В.', 0, 1, 'R')

    # Save the PDF
    unique_filename = f"{os.path.splitext(os.path.basename(csv_path))[0]}_custom_{int(time.time())}.pdf"
    pdf.output(os.path.join(app.config['PDF_OUTPUT_FOLDER'], unique_filename))
    return unique_filename

def get_info(product_id, path="172.16.0.40:40"):
    if not product_id:
        return None
    try:
        get_item_info = f'http://{path}/api/product-items/{product_id}/get_item_info/'
        response = requests.get(get_item_info)
        item_json = response.content.decode('utf-8')
        item_data = json.loads(item_json)
        return item_data
    except requests.RequestException as e:
        print(f"Error fetching product info: {e}")
        return None

@app.route('/product/<int:product_id>')
def product_label(product_id):
    product_data = get_info(product_id)
    if product_data is None:
        return jsonify({'error': 'Failed to retrieve product data'}), 500

    image_file = create_label_for_product(product_data)
    if image_file:
        return send_from_directory(app.config['UPLOAD_FOLDER'], image_file, as_attachment=True)
    else:
        return jsonify({'error': 'Failed to create label'}), 500

@app.route('/download/csv/<path:filename>')
def download_csv(filename):
    directory = app.config['DOWNLOAD_FOLDER']
    safe_filename = secure_filename(filename)
    try:
        return send_from_directory(directory, safe_filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/search', methods=['POST'])
def search_product():
    product_id = request.form.get('product_id')
    product_data = get_info(product_id)
    return render_template('display_tables.html', product_info=product_data)

if __name__ == '__main__':
    app.run(debug=True)