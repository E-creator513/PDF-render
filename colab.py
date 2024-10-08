from flask import Flask, request, send_from_directory
import os
import pandas as pd
from fpdf import FPDF
import time

app = Flask(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PDF_OUTPUT_FOLDER'] = 'pdf_outputs/'
app.config['DOWNLOAD_FOLDER'] = 'download/'

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

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['PDF_OUTPUT_FOLDER']):
        os.makedirs(app.config['PDF_OUTPUT_FOLDER'])
    
    app.run(debug=True)
