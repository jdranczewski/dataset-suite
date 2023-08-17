from IPython.display import display, Markdown
import os

class MD:
    def __init__(self):
        self.text = ""

    def print(self, *text, end="\n\n"):
        self.text += " ".join(text) + end
    
    def show(self):
        display(Markdown(self.text))