import os

try:
    import win32com.client
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc_path = r'c:\Users\12277\.trae-cn\attachments\6a982af2d09b3824411c6fa9\e15b5a8c-9a6e-4ba1-991c-85fd0307b649_新建 DOC 文档.doc'
    doc = word.Documents.Open(doc_path)
    text = doc.Range().Text
    doc.Close()
    word.Quit()
    print(text)
except Exception as e:
    print(f"win32com error: {e}")
