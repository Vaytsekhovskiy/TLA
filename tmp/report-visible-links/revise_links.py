"""Make the source addresses visible in the current Word report."""

import hashlib
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


WORK = Path(__file__).resolve().parent
REPORT = WORK.parents[1] / "experiment/REPORT.docx"
TASKS = ("ConfigParams", "Test1623", "Bug2750", "test10")
BENCHMARK = (
    "https://github.com/LUC-AI4FM/tla_benchmark/tree/dataset-release/dataset_release"
)


def visible_link(paragraph, address):
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), paragraph.part.relate_to(address, RT.HYPERLINK, is_external=True))
    run = paragraph.add_run(address)
    run.underline = True
    link.append(run._r)
    paragraph._p.append(link)


def link_line(anchor, label, address, *, keep_next=False):
    line = anchor.insert_paragraph_before()
    line.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = line.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.space_after = Pt(3)
    pf.keep_together = True
    pf.keep_with_next = keep_next
    line.add_run(label + "  ").bold = True
    visible_link(line, address)


def main():
    initial = REPORT.read_bytes()
    before = WORK / "REPORT-before.docx"
    before.write_bytes(initial)
    (WORK / "original.sha256").write_text(hashlib.sha256(initial).hexdigest(), encoding="ascii")
    doc = Document(before)
    old_paragraphs = []
    for name in TASKS:
        original = next(
            p for p in doc.paragraphs
            if p.text.startswith(name + ".") and len(p.hyperlinks) == 4
        )
        old_paragraphs.append(original)
    anchor = old_paragraphs[0]
    anchor.insert_paragraph_before("Источники на GitHub", style="Heading 2")
    link_line(anchor, "Репозиторий из задания", BENCHMARK, keep_next=True)
    anchor.insert_paragraph_before(
        "Репозиторий TLA+-Bench при проверке вернул HTTP 404. Для описаний приведены "
        "исходные ссылки GitHub и пути к файлам в локальной копии проекта. "
        "Файлы Gold и CFG на GitHub в репозитории Apalache совпадают с файлами набора."
    )
    for name, original in zip(TASKS, old_paragraphs):
        description, _, _, upstream = (link.url for link in original.hyperlinks)
        source_path = description.split("/dataset_release/", 1)[1]
        local_path = f"../dataset_release/dataset_release/{source_path}"
        local_file = (REPORT.parent / local_path).resolve()
        assert local_file.is_file(), local_file
        heading = anchor.insert_paragraph_before(name, style="Heading 3")
        heading.paragraph_format.first_line_indent = Cm(0)
        heading.paragraph_format.keep_with_next = True
        heading.paragraph_format.space_before = Pt(9)
        link_line(anchor, "Описание (GitHub)", description, keep_next=True)
        link_line(anchor, "Описание (локальная копия)", local_path, keep_next=True)
        link_line(anchor, "Gold (TLA+)", upstream, keep_next=True)
        link_line(anchor, "CFG (TLC)", upstream.removesuffix(".tla") + ".cfg")
    retired = next(
        p for p in doc.paragraphs
        if p.text.startswith("Материалы benchmark доступны в сохранённой локальной копии.")
    )
    for p in [*old_paragraphs, retired]:
        p._p.getparent().remove(p._p)
    active_relationships = {
        link.get(qn("r:id")) for link in doc._element.xpath(".//w:hyperlink[@r:id]")
    }
    for rel_id, relationship in list(doc.part.rels.items()):
        if relationship.reltype == RT.HYPERLINK and rel_id not in active_relationships:
            doc.part.drop_rel(rel_id)
    doc.save(WORK / "REPORT.docx")


if __name__ == "__main__":
    main()
