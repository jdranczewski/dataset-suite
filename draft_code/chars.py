import pyperclip
print(len(pyperclip.paste().replace("\n", " ")), end="")