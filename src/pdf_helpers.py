import logging
import re
import datetime
from fpdf import FPDF
import pandas as pd
import Levenshtein

logging.basicConfig(format='%(asctime)s %(name)s %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

def prepare_pdf_document(highlights: list[str], title: str = "Your Notes And Highlights") -> FPDF:
    """
    Creates a PDF document from the highlights list.

    Parameters
    ----------
    highlights : list[str]
        List of text highlights.
    title : str, optional
        Title of the PDF document, by default "Your Notes And Highlights".

    Returns
    -------
    FPDF
        FPDF object with the document content.
    """
    df_highlights = create_df_from_highlights_list(highlights)

    pdf_file = FPDF()
    pdf_file.add_page()
    pdf_file.add_font("lisboa", "", "media/Lisboa.ttf", uni=True)
    pdf_file.set_font("lisboa", "", 22)
    pdf_file.set_margins(25, 40, 25)
    pdf_file = insert_line_break_in_pdf(pdf_file, 3)
    pdf_file.multi_cell(0, 8, title, align="C")
    pdf_file = insert_line_break_in_pdf(pdf_file, 2)

    page_number = 1
    for _, highlight_content in df_highlights.iterrows():
        preivous_height = pdf_file.y
        # create muti-cell pdf object and add text to it
        pdf_file.set_font("lisboa", "", 15)
        pdf_file.set_text_color(0, 0, 0)
        pdf_file.multi_cell(0, 7, highlight_content["highlight"], 0)

        pdf_file.set_font("lisboa", "", 11)
        pdf_file.set_text_color(77, 77, 77)
        pdf_file.multi_cell(0, 5, highlight_content["meta"], 0)
        pdf_file = insert_bar_separator_in_pdf(pdf_file)

        new_height = pdf_file.y
        if new_height < preivous_height:  # Check if the current content exceeds the page height
            page_number += 1
            pdf_file = add_page_number(pdf_file, page_number)
            pdf_file.set_y(new_height)

    return pdf_file

def insert_line_break_in_pdf(pdf_file: FPDF, num_breaks: int = 1) -> FPDF:
    """
    Inserts a line break in a pdf for num_breaks times
    """
    while num_breaks != 0:
        pdf_file.multi_cell(0, 5, "", 0)
        num_breaks -= 1

    return pdf_file


def insert_bar_separator_in_pdf(pdf_file: FPDF) -> FPDF:
    """
    Inserts a bar separator in a pdf, useful to separate highlights
    """
    pdf_file = insert_line_break_in_pdf(pdf_file)
    pdf_file.set_draw_color(191, 191, 191)
    pdf_file.line(40, pdf_file.y, 150, pdf_file.y)
    pdf_file = insert_line_break_in_pdf(pdf_file)

    return pdf_file


def extract_date_and_time(string: str):
    """Extracts the date and time from the string and returns a datetime object."""
    date_and_time_str = string.split("Added on ")[1]
    _, date_time_str = date_and_time_str.split(", ")
    date_time = datetime.datetime.strptime(date_time_str, "%d %B %Y %H:%M:%S")

    return date_time


def calculate_similarity(string1: str, string2: str)->float:
    if string1 is None or string2 is None:
        return 0
    distance = Levenshtein.distance(string1, string2)
    similarity = 1 - (distance / max(len(string1), len(string2)))
    return similarity


def filter_repeated_highlights(df_highlights: pd.DataFrame)-> pd.DataFrame:
    """Takes a dataframe with highlights and removes the repetaed highlights. The most recent highlight is kept.

    Parameters
    ----------
    df_highlights : pd.DataFrame
        Dataframe with the list of highlights and the columns ["highlight", "meta", "date"]
    """
    df_highlights["next_highlight"] = df_highlights["highlight"].shift(-1)
    df_highlights["correlaton"] = df_highlights.apply(lambda x: calculate_similarity(x["highlight"], x["next_highlight"]), axis=1)
    df_highlights["time_diff"] = df_highlights["date"].shift(-1) - df_highlights["date"]
    df_highlights["correlaton_greater"] = df_highlights["correlaton"] > 0.3
    df_highlights["time_diff_greater"] = df_highlights["time_diff"] < datetime.timedelta(minutes=1)
    df_highlights["to_remove"] = df_highlights["correlaton_greater"] & df_highlights["time_diff_greater"]
    logger.info(f"Total initial clippings: {len(df_highlights)}")
    df_highlights =  df_highlights[~df_highlights["to_remove"]]
    logger.info(f"Clippings after removing similar notes: {len(df_highlights)}")
    df_highlights.reset_index(drop=True, inplace=True)

    return df_highlights[["highlight", "meta", "date"]]

def create_df_from_highlights_list(higlights_list: list)-> pd.DataFrame:
    """Takes a list of highlights and creates a dataframe with the columns ["highlight", "meta", "date"]

    Parameters
    ----------
    higlights_list : List
        List containing the text of the highlights
    """
    filtered_highlights = [string for string in higlights_list if string != "..." and string != ""]

    meta_regex_pattern = r"(Your.*\| Added on)"

    highlights_meta = []
    highlights_date = []
    highlights_text = []
    for highlight_line in filtered_highlights:
        if re.search(meta_regex_pattern, highlight_line):
            highlights_meta.append(highlight_line)
            highlight_date = extract_date_and_time(highlight_line)
            highlights_date.append(highlight_date)
        else:
            highlights_text.append(highlight_line)
    df_highlights = pd.DataFrame({'highlight': highlights_text, 'meta': highlights_meta, 'date': highlights_date})
    df_highlights = filter_repeated_highlights(df_highlights)

    return df_highlights

def add_page_number(pdf_file: FPDF, page_number:int)->FPDF:
    """Adds a page number to a new page in a FPDF

    Parameters
    ----------
    pdf_file : FPDF
        File containing the pages of the pdf
    page_number : int
        Number of page to add
    """
    pdf_file.set_y(20)
    pdf_file.set_font("lisboa", "", 11)
    pdf_file.set_text_color(77, 77, 77)
    pdf_file.multi_cell(0, 10, f" - Page {page_number} - ", align="C")  # Add the page number to the new page
    return pdf_file
