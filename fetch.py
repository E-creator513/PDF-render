from flask import Flask, request, send_from_directory, render_template, abort, jsonify
import os
from werkzeug.utils import secure_filename
import tru
from fpdf import FPDF
import pandas as pd
import re
import requests
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PDF_OUTPUT_FOLDER'] = 'pdf_outputs/'
app.config['DOWNLOAD_FOLDER'] = 'download/'

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        if len(files) > 40:
            return render_template('upload.html', message="You can only upload up to 40 files.")
        
        all_data = []
        csv_list = []  # List to keep track of CSV files generated
        table_html_list = []  # List to keep track of extracted table HTMLs for PDF creation

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
                    processed_tables = tru.process_pdf_file(file_stream, filename, invoice_number)
                    if processed_tables:
                        csv_paths = tru.save_tables_to_csv(processed_tables, app.config['UPLOAD_FOLDER'], f"output_table_{file_index}")
                        csv_list.extend(csv_paths)
                        for csv_path in csv_paths:
                            data = pd.read_csv(csv_path)
                            table_html = data.to_html(classes='table table-striped', index=False)
                            all_data.append((table_html, csv_path, filename))
                            table_html_list.append(table_html)  # Store HTML for PDF generation
                    else:
                        print(f"Failed to process PDF file: {filename}")
                        return render_template('upload.html', message=f"Failed to process PDF file: {filename}"), 400
            else:
                print("No file uploaded or file is invalid.")
                return render_template('upload.html', message="No file uploaded or file is invalid.")

        # Generate PDF with all extracted tables
        table_pdf_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], 'Extracted_Tables.pdf')
        save_table_to_pdf(table_html_list, table_pdf_path)

        # Prepare the data for the template
        data_for_template = [{'table': table, 'csv_path': csv_path, 'filename': filename} for table, csv_path, filename in all_data]
        return render_template('display_tables.html', tables=data_for_template, table_pdf_path=table_pdf_path)
    return render_template('upload.html')

@app.route('/download-pdf/<path:csv_filename>', methods=['GET'])
def download_pdf(csv_filename):
    # Paths
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    pdf_filename = f"{os.path.splitext(csv_filename)[0]}.pdf"
    output_pdf_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)

    # Generate PDF
    csv_to_pdf(csv_path, output_pdf_path)

    # Serve the PDF file for download
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], pdf_filename, as_attachment=True)

@app.route('/download-pdf1/<path:csv_filename>', methods=['GET'])
def download_pdf1(csv_filename):
    # Paths
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    pdf_filename = f"{os.path.splitext(csv_filename)[0]}.pdf"
    output_pdf_path1 = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)

    # Generate PDF
    csv_to_pdf1(csv_path, output_pdf_path1)

    # Serve the PDF file for download
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], pdf_filename, as_attachment=True)
    
def csv_to_pdf1(csv_path, output_pdf_path1):
    data = pd.read_csv(csv_path)

    pdf = FPDF(orientation='L')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font('timesnrcyrmt_inclined', '', 'timesnrcyrmt_inclined.ttf', uni=True)
    pdf.add_font('timesnrcyrmt_bold', '' , 'timesnrcyrmt_bold.ttf', uni=True)
    pdf.add_font('timesnrcyrmt', '','timesnrcyrmt.ttf',uni=True)
    pdf.set_font("Arial", size=12)
    pdf.set_font('timesnrcyrmt_inclined', '', 10)
    pdf.image('ftkframe.jpeg', 260, 8, 29)
    # Set font for the header
    pdf.set_font('timesnrcyrmt_inclined', '', 10)
    # Move to the right
    pdf.set_xy(30, 10)
    # Title
    pdf.cell(33, 10, 'ООО «ФТК» ', 0, 1, '')
    pdf.set_xy(30, 13)
    pdf.cell(33, 13, '198095, Санкт-Петербург г, пер Химический, д. 1, литера АЦ, ЧАСТЬ ПОМ. 1-Н, ПОМ. 17', 0, 1, '')
    pdf.set_xy(30, 16)
    pdf.cell(33, 16, '+7 (905) 300-02-55', 0, 1, '')
    pdf.set_xy(30, 19)
    pdf.cell(33, 19, 'sale@techcomplekt.ru', 0, 1, '')
    pdf.set_xy(30, 22)
    pdf.cell(33, 22, 'metgost.ru', 0, 1, '')
    # Line break
    pdf.ln(20)
    pdf.image('est.png', 8, 42, 10)
    pdf.set_font('timesnrcyrmt_inclined', '', 10)
    pdf.set_xy(16,33)
    pdf.cell(17,28, ' СИСТЕМА МЕНЕДЖМЕНТА КАЧЕСТВА СЕРТИФИЦИРОВАНА НА СООТВЕТСТВИЕ ТРЕБОВАНИЯМ ГОСТ ISO 9001:2015 № РОСС RU.3745.04УЛЛ0 / СМК.2711-24',0,1,'')
    pdf.set_font('timesnrcyrmt_bold', '', 16)
    pdf.set_xy(0,39)
    pdf.cell(0,39, 'Паспорт-сертификат № ___ от ___.___.20__ г.',0,2, 'C')
    pdf.set_font('timesnrcyrmt','',10)
    pdf.set_xy(0,42)
    pdf.cell(0,44,'(на партию отгруженного товара)',0,2,'C')
    pdf.set_line_width(0.6)
    pdf.line(17,69,280,69)
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.set_xy(17,50)
    pdf.cell(17,50,'Изготовитель: ',0,1,'')
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    pdf.set_xy(41,50)
    pdf.cell(41,50,' ООО «ПФТ», ИНН 7819030811, КПП 781901001, 198207, г. Санкт-Петербург, Трамвайный проспект, д.6, тел.: 8(812)983-70-83 ',0,1,'')
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.set_xy(17,53)
    pdf.cell(17,53,'Поставщик: ',0,1,'')
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    pdf.set_xy(41,53)
    pdf.cell(41,53,'ООО «ФТК», ИНН 6318048615, КПП 780501001, 198095, город Санкт-Петербург, Химический пер, д. 1 литера АЦ, часть пом. 1-н пом. 17',0,1,'')
    pdf.set_font('timesnrcyrmt_bold', '', 12)
    pdf.set_xy(17,56)
    pdf.cell(17,56,'Покупатель:_______________________________________________________________________________________________________________',0,1,'')
    
    # Adding table header
    pdf.set_font('Arial', 'B', 12)
    for column in data.columns:
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.set_font("DejaVu",'', size=8)
        pdf.cell(40, 10, column, 2)
    pdf.ln()

    # Adding table rows
    pdf.set_font('Arial', '', 12)
    for index, row in data.iterrows():
        for item in row:
            pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
            pdf.set_font("DejaVu", size=8)
            pdf.cell(40, 7, str(item), 2)
        pdf.ln()
    pdf.set_xy(-105, -25)
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.cell(-105, -25, 'Директор:_____________________________Третяк И.Н.', 0, 1, '')
    pdf.set_xy(-105, -15)
    pdf.cell(-105, -15, 'Начальник ОТК:________________________Ермина О.Р', 0, 1, '')
    # Save the PDF
    pdf.output(output_pdf_path1)
def csv_to_pdf(csv_path, output_pdf_path):
    data = pd.read_csv(csv_path)

    pdf = FPDF(orientation='L')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font('timesnrcyrmt_inclined', '', 'timesnrcyrmt_inclined.ttf', uni=True)
    pdf.add_font('timesnrcyrmt_bold', '' , 'timesnrcyrmt_bold.ttf', uni=True)
    pdf.add_font('timesnrcyrmt', '','timesnrcyrmt.ttf',uni=True)
    pdf.set_font("Arial", size=12)
    pdf.set_font('timesnrcyrmt_inclined', '', 10)
    pdf.image('logo.png', 10, 13, 26)
    pdf.set_xy(38, 10)
    pdf.cell(33, 10, 'ООО «ПФТ» ', 0, 1, '')
    pdf.set_xy(38, 13)
    pdf.cell(33, 13, 'Санкт- Петербург, Трамвайный проспект, д.6', 0, 1, '')
    pdf.set_xy(38, 16)
    pdf.cell(33, 16, '+7 (812) 983-70-83, +7(960)283-70-83', 0, 1, '')
    pdf.set_xy(38, 19)
    pdf.cell(33, 19, 'zakaz@metgost.ru', 0, 1, '')
    pdf.set_xy(38, 22)
    pdf.cell(33, 22, 'metgost.ru', 0, 1, '')
    pdf.ln(20)
    pdf.image('est.png', 8, 42, 10)
    pdf.set_font('timesnrcyrmt_inclined', '', 10)
    pdf.set_xy(17, 33)
    pdf.cell(17, 28, 'СИСТЕМА МЕНЕДЖМЕНТА КАЧЕСТВА СЕРТИФИЦИРОВАНА НА СООТВЕТСТВИЕ ТРЕБОВАНИЯМ ГОСТ ISO 9001:2015 № РОСС RU.3745.04УЛЛ0 / СМК.2711-24', 0, 1, '')
    pdf.set_font('timesnrcyrmt_bold', '', 16)
    pdf.set_xy(0, 39)
    pdf.cell(0, 39, 'Паспорт-сертификат № ___ от ___.___.20__ г.', 0, 0, 'C')
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.set_xy(0, 42)
    pdf.cell(0, 44, '(на партию отгруженного товара)', 0, 1, 'C')
    pdf.set_line_width(0.6)
    pdf.line(17, 69, 280, 69)
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.set_xy(17, 50)
    pdf.cell(17, 50, 'Изготовитель: ', 0, 1, '')
    pdf.set_font('timesnrcyrmt_bold', '', 10)
    pdf.set_xy(40, 50)
    pdf.cell(40, 50, ' ООО «ПФТ», ИНН 7819030811, КПП 781901001, 198207, г. Санкт-Петербург, Трамвайный проспект, д.6, тел.: 8(812)983-70-83 ', 0, 1, '')
    pdf.set_font('timesnrcyrmt_bold', '', 12)
    pdf.set_xy(17, 53)
    pdf.cell(17, 53, 'Покупатель:____________________________________________________________________________________________________', 0, 1, '')

    # Adding table header
    pdf.set_font('Arial', 'B', 12)
    for column in data.columns:
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.set_font("DejaVu",'', size=8)
        pdf.cell(40, 10, column, 1)
    pdf.ln()

    # Adding table rows
    pdf.set_font('Arial', '', 12)
    for index, row in data.iterrows():
        for item in row:
            pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
            pdf.set_font("DejaVu", size=8)
            pdf.cell(40, 7, str(item), 1)
        pdf.ln()
    pdf.set_xy(-105, -25)
    pdf.set_font('timesnrcyrmt', '', 10)
    pdf.cell(-105, -25, 'Директор:_____________________________Третяк И.Н.', 0, 1, '')
    pdf.set_xy(-105, -15)
    pdf.cell(-105, -15, 'Начальник ОТК:________________________Ермина О.Р', 0, 1, '')
    # Save the PDF
    pdf.output(output_pdf_path)



def save_table_to_pdf(tables, pdf_filename):
    pdf = FPDF()
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("DejaVu", size=12)  # Use DejaVu font which supports Unicode

    for index, table_html in enumerate(tables, start=1):
        pdf.multi_cell(0, 10, txt=f"Table {index}", align='C')
        pdf.ln()

        # Split table rows into pages if needed
        table_rows = table_html.split('<tr>')
        for i, row in enumerate(table_rows):
            if i == 0:  # Handle header row
                header_row = row.replace('<th>', '').replace('</th>', '').replace('</tr>', '').replace('<tr>', '')
                headers = header_row.split('</td>')
                for header in headers:
                    pdf.cell(40, 10, txt=header.strip(), border=1)
                pdf.ln()
            else:
                row = row.replace('<td>', '').replace('</td>', '').replace('</tr>', '')
                columns = row.split('</td>')
                for column in columns:
                    pdf.cell(40, 10, txt=column.strip(), border=1)
                pdf.ln()

            if pdf.get_y() > 260:  # Add a new page if the table exceeds the page limit
                pdf.add_page()

    pdf.output(pdf_filename)


@app.route('/generate-pdf-format1', methods=['POST'])
def generate_pdf_format1():
    csv_path = request.form.get('csv_path')
    pdf_files = []
    data = pd.read_csv(csv_path)
    index = 1
    for _, item in data.iterrows():
        pdf_path = tru.create_pdf(item, index, app.config['PDF_OUTPUT_FOLDER'])
        pdf_files.append(pdf_path)
        index += 1
    merged_pdf_path = tru.merge_pdfs(pdf_files, os.path.join(app.config['PDF_OUTPUT_FOLDER'], 'Combined_ФТК.pdf'))
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], 'Combined_ФТК.pdf', as_attachment=True)

@app.route('/generate-pdf-format2', methods=['POST'])
def generate_pdf_format2():
    csv_path = request.form.get('csv_path')
    pdf_files = []
    data = pd.read_csv(csv_path)
    index = 1
    for _, item in data.iterrows():
        pdf_path = tru.create_pdf1(item, index, app.config['PDF_OUTPUT_FOLDER'])
        pdf_files.append(pdf_path)
        index += 1
    merged_pdf_path = tru.merge_pdfs(pdf_files, os.path.join(app.config['PDF_OUTPUT_FOLDER'], 'Combined_ПФТ.pdf'))
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], 'Combined_ПФТ.pdf', as_attachment=True)

@app.route('/generate-pdf-format3', methods=['POST'])
def generate_pdf_format3():
    csv_path = request.form.get('csv_path')
    pdf_files = []
    data = pd.read_csv(csv_path)
    index = 1
    for _, item in data.iterrows():
        pdf_path = tru.create_pdf1(item, index, app.config['PDF_OUTPUT_FOLDER'])
        pdf_files.append(pdf_path)
        index += 1
    merged_pdf_path = tru.merge_pdfs(pdf_files, os.path.join(app.config['PDF_OUTPUT_FOLDER'], 'Combined_ПФТ.pdf'))
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], 'Combined_ПФТ.pdf', as_attachment=True)


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
