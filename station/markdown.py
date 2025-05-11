import re

from station.graphics.format_label import FLabel
from resources import Style

HEADER_EX = r"^(#{1,6})\s+(.+)$"
STYLING_EX = r"(\*{1,2}|_{1,2})(\S.*?\S|\S)\1"
LIST_EX = r"^\s*[-+*]\s+(.+)$"


def markdown_label(text: str, font_name: str) -> FLabel:
    pass


def update_label_styling(label: FLabel, font_name: str):
    pass

def update_label_headings(label: FLabel, font_name: str):
    pass

def update_label_listings(label: FLabel, font_name: str):
    pass