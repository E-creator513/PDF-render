import pdfplumber
import pandas as pd
import os
import re
from fpdf import FPDF
from PyPDF2 import PdfMerger

import pdfplumber
import re
import PyPDF2

def extract_sentences_starting_with_pokuvatel(pdf_file):
    """Extracts sentences starting with 'Покупатель' from a PDF file stream."""
    sentences = []
    reader = PyPDF2.PdfReader(pdf_file)
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()
        lines = text.split('\n')
        for i in range(len(lines)):
            if lines[i].startswith("Покупатель"):
                sentence = lines[i]
                if i + 1 < len(lines):
                    sentence += " " + lines[i + 1]
                sentences.append(sentence)
                #sentences.append(sentence)
                #sentences.append(sentence)
    return sentences

def process_pdf_file(file_stream, filename, invoice_number):
    """Process a given PDF file stream and save extracted tables as CSV."""
    contains_target_phrase = False
    
    try:
        with pdfplumber.open(file_stream) as pdf:
            tables = []

            for page in pdf.pages:
                text = page.extract_text()

                if text:
                    # Check for tables on the page
                    page_has_table = any(page.extract_table())

                    if "Промышленная фурнитура и тара" in text:
                        contains_target_phrase = True

                    # Extract tables from the page
                    page_tables = page.extract_tables()
                    tables.extend(page_tables)
            
        # Extract "Покупатель" sentences using the new method
        buyer_sentences = extract_sentences_starting_with_pokuvatel(file_stream)

        if not tables:
            print(f"No tables found in {filename}.")
            return None, contains_target_phrase, buyer_sentences

        processed_tables = []
        keywords = ["№", "Товары", "Количество", "Цена", "Сумма"]

        for table in tables:
            relevant_data = []
            relevant_columns = set()
            for row in table:
                for idx, cell in enumerate(row):
                    if any(re.search(r'\b' + re.escape(keyword) + r'\b', str(cell), re.IGNORECASE) for keyword in keywords):
                        relevant_columns.add(idx)
            if relevant_columns:
                relevant_table = [[row[col] for col in sorted(relevant_columns)] for row in table]
                relevant_data.append(relevant_table)
            if relevant_data:
                modified_table = split_product_details(relevant_data[0], invoice_number)
                processed_tables.append(modified_table)
            else:
                print(f"No relevant data found in tables of {filename}.")

        if not processed_tables:
            print(f"No processed tables for {filename}.")
        
        return processed_tables, contains_target_phrase, buyer_sentences
    except Exception as e:
        print(f"Error processing PDF file {filename}: {e}")
        return None, contains_target_phrase, []


def split_product_details(table, invoice_number):
    modified_table = []
    headers = table[0]
    product_col_index = next((i for i, cell in enumerate(headers) if 'Товары (работы, услуги)' in str(cell)), None)
    sum_index = headers.index("Сумма") if "Сумма" in headers else None

    new_headers = headers[:product_col_index + 1] + ['ГОСТ/ОСТ'] + headers[product_col_index + 1:]
    if sum_index is not None:
        new_headers.insert(sum_index + 1, 'Счёт по Оплату')
    modified_table.append(new_headers)

    for row in table[1:]:
        new_row = row[:product_col_index + 1] + [''] + row[product_col_index + 1:]
        product_details = row[product_col_index]
        split_point = re.search(r' (ГОСТ|ОСТ)', product_details)
        if split_point:
            new_row[product_col_index] = product_details[:split_point.start()]
            new_row[product_col_index + 1] = product_details[split_point.start():].strip()
        if sum_index is not None:
            new_row.insert(sum_index + 1, invoice_number)
        modified_table.append(new_row)
    return modified_table

def save_tables_to_csv(tables, directory, prefix):
    file_paths = []
    for idx, table in enumerate(tables, start=1):
        filename = os.path.join(directory, f"{prefix}_{idx}.csv")
        df = pd.DataFrame(table[1:], columns=table[0])
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        file_paths.append(filename)
        print(f"Saved: {filename}")
    return file_paths

def create_pdf(item, index, output_dir):
    """Create a PDF file for a given item with the index number starting at 1."""
    pdf = FPDF(orientation='P', unit='mm', format=(119, 75))
    pdf.add_page()
    add_fonts_and_image(pdf)
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 6, 'Фабрика Технических Комплектующих', 0, 1, 'C')
    pdf.set_font('DejaVu', '', 8)
    pdf.cell(0, 6, 'ИНН: 6318048615, КПП: 780501001', 0, 1, 'C')
    pdf.cell(0, 6, '198095, Санкт-Петербург, Химический пер., д. 1', 0, 1, 'C')
    pdf.cell(0, 6, '+7 (905) 300-02-55   metgost.ru   zakaz@metgost.ru', 0, 1, 'C')
    pdf.ln(0.99)
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 5, f'Наименование: {item["Товары (работы, услуги)"]}', 0, 1)
    pdf.cell(0, 5, f'Стандарт: {item["ГОСТ/ОСТ"]}', 0, 1)
    pdf.cell(0, 5, f'Количество: {item["Количество"]} шт.', 0, 1)
    pdf.cell(0, 5, f'{item["Счёт по Оплату"]} Поз: {index}', 0, 1)
    pdf.set_line_width(1)
    pdf.rect(3, 3, 113, 69)
    pdf.line(5, 35, 114, 35)
    pdf.set_xy(5, 65)
    pdf.set_font('DejaVu', '', 5)
    pdf_output_path = os.path.join(output_dir, f'Generated_ФТК_{index}.pdf')
    pdf.output(pdf_output_path)
    return pdf_output_path

def create_pdf1(item, index, output_dir):
    """Create a PDF file for a given item with the index number starting at 1."""
    pdf = FPDF(orientation='P', unit='mm', format=(119, 75))
    pdf.add_page()
    add_fonts_and_image(pdf, logo="logo.png")
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 6, 'Промышленная Фурнитура и Тара', 0, 1, 'C')
    pdf.set_font('DejaVu', '', 8)
    pdf.cell(0, 6, 'ИНН: 7819030811, КПП: 780501001', 0, 1, 'C')
    pdf.cell(0, 6, '198207, Санкт-Петербург, Трамвайный пр-т, 6', 0, 1, 'C')
    pdf.cell(0, 6, '+7 (812) 983-70-83   metgost.ru   zakaz@metgost.ru', 0, 1, 'C')
    pdf.ln(0.99)
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 5, f'Наименование: {item["Товары (работы, услуги)"]}', 0, 1)
    pdf.cell(0, 5, f'Стандарт: {item["ГОСТ/ОСТ"]}', 0, 1)
    pdf.cell(0, 5, f'Количество: {item["Количество"]} шт.', 0, 1)
    pdf.cell(0, 5, f'{item["Счёт по Оплату"]} Поз: {index}', 0, 1)
    pdf.set_line_width(1)
    pdf.rect(3, 3, 113, 69)
    pdf.line(5, 35, 114, 35)
    pdf.image("frame1.png", x=119 - 25, y=75 - 25, w=20)
    pdf.set_xy(5, 65)
    pdf.set_font('DejaVu', '', 5)
    pdf_output_path = os.path.join(output_dir, f'Generated_ПФТ_{index}.pdf')
    pdf.output(pdf_output_path)
    return pdf_output_path

def add_fonts_and_image(pdf, logo="ftkframe.jpeg"):
    """Helper function to add fonts and images to the PDF."""
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.add_font('DejaVu', 'I', 'DejaVuSansCondensed-Oblique.ttf', uni=True)
    pdf.image(logo, x=3, y=3, w=20)

def merge_pdfs(pdf_files, output_filename):
    merger = PdfMerger()
    for pdf_file in pdf_files:
        merger.append(pdf_file)
    merger.write(output_filename)
    merger.close()
