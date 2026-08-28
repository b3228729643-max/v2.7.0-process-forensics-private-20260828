"""Read-only diagnostic for the official R95 PDF content stream."""
from pypdf import PdfReader
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, ByteStringObject, ContentStream, DecodedStreamObject, NameObject, RectangleObject
import copy
from pathlib import Path
import shutil
import subprocess
import numpy as np

import audit_p634_r95 as audit


def matrix(values):
    return np.array(
        [[float(values[0]), float(values[2]), float(values[4])], [float(values[1]), float(values[3]), float(values[5])], [0.0, 0.0, 1.0]]
    )


reader = PdfReader(str(audit.OFFICIAL_PDF))
page = reader.pages[audit.PAGE_INDEX]
stream = ContentStream(page.get_contents(), reader)
post = [np.eye(3)]
pre = [np.eye(3)]
for index, (operands, operator) in enumerate(stream.operations):
    if index == 718:
        print("post_concat", post[-1])
        print("pre_concat", pre[-1])
        break
    if operator == b"q":
        post.append(post[-1].copy())
        pre.append(pre[-1].copy())
    elif operator == b"Q":
        post.pop()
        pre.pop()
    elif operator == b"cm":
        transform = matrix(operands)
        post[-1] = post[-1] @ transform
        pre[-1] = transform @ pre[-1]

# T010:G01's official content run: this isolated replay must use the original
# R95 page's cloned resources, exact font /F93, text operators, text matrix,
# graphic CTM and the raw two-byte CID of the first character only.
snippet = ContentStream(None, reader)
snippet.operations = copy.deepcopy(stream.operations[718:736])
snippet.operations[11] = ([ArrayObject([ByteStringObject(b";\x1f")])], b"TJ")
snippet_data = snippet.get_data()
prefix = b"q\n1 0 0 1 286.05 355.611 cm\n"
suffix = b"\nQ\n"
out_stream = DecodedStreamObject()
out_stream.set_data(prefix + snippet_data + suffix)
writer = PdfWriter()
out_page = writer.add_page(page)
out_page[NameObject("/Contents")] = writer._add_object(out_stream)
out_page.cropbox = RectangleObject([1888 / audit.SCALE, page.mediabox.height - 1923 / audit.SCALE, 1929 / audit.SCALE, page.mediabox.height - 1879 / audit.SCALE])
import tempfile
with tempfile.TemporaryDirectory(prefix="fig_p634_replay_") as temp:
    scratch = Path(temp)
    probe_pdf = scratch / "pdf_content_replay_probe_T010_G01.pdf"
    with probe_pdf.open("wb") as f:
        writer.write(f)
    output = scratch / "pdf_content_replay_probe_T010_G01"
    subprocess.run(
        ["pdftocairo", "-png", "-singlefile", "-transp", "-r", "300", "-x", "1888", "-y", "1879", "-W", "41", "-H", "44", str(probe_pdf), str(output)],
        check=True,
    )
    shutil.copyfile(output.with_suffix(".png"), audit.ROOT / "pdf_content_replay_probe_T010_G01.png")
    cropbox_output = scratch / "pdf_content_replay_probe_T010_G01_cropbox"
    subprocess.run(
        ["pdftocairo", "-png", "-singlefile", "-transp", "-cropbox", "-r", "300", str(probe_pdf), str(cropbox_output)],
        check=True,
    )
    shutil.copyfile(cropbox_output.with_suffix(".png"), audit.ROOT / "pdf_content_replay_probe_T010_G01_cropbox.png")
print("wrote replay probe")
