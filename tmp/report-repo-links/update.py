"""Replace the source URLs in the current report without changing its analysis."""

import hashlib
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml.ns import qn


WORK = Path(__file__).resolve().parent
REPORT = WORK.parents[1] / "experiment/REPORT.docx"
REPO = "https://github.com/Vaytsekhovskiy/TLA"
TASKS = (
    (92, "ConfigParams"),
    (239, "Test1623"),
    (67, "Bug2750"),
    (352, "test10"),
)
BENCHMARK = "https://github.com/LUC-AI4FM/tla_benchmark"
SOURCE_NOTE = (
    "Тексты описаний из TLA+-Bench опубликованы в папках задач "
    "репозитория Vaytsekhovskiy/TLA. Файлы Gold и CFG на GitHub "
    "в репозитории Apalache совпадают с файлами набора."
)
PARTS = {"word/document.xml", "word/_rels/document.xml.rels"}


def set_address(paragraph, address):
    (link,) = paragraph.hyperlinks
    rel_id = paragraph.part.relate_to(address, RT.HYPERLINK, is_external=True)
    link._element.set(qn("r:id"), rel_id)
    first, *rest = link.runs
    first.text = address
    for run in rest:
        run._r.getparent().remove(run._r)


def main():
    snapshot = REPORT.read_bytes()
    before = WORK / "REPORT-before.docx"
    before.write_bytes(snapshot)
    (WORK / "original.sha256").write_text(hashlib.sha256(snapshot).hexdigest(), encoding="ascii")
    doc = Document(before)
    paragraphs = doc.paragraphs
    repo_paragraph = next(p for p in paragraphs if p.text.startswith("Репозиторий из задания"))
    repo_paragraph.runs[0].text = "Репозиторий эксперимента  "
    set_address(repo_paragraph, REPO)
    note = next(p for p in paragraphs if p.text.startswith("Репозиторий TLA+-Bench при проверке"))
    note.text = SOURCE_NOTE

    descriptions = [p for p in paragraphs if p.text.startswith("Описание (GitHub)")]
    for (task_id, name), p in zip(TASKS, descriptions, strict=True):
        old_url = p.hyperlinks[0].url
        assert old_url.startswith(BENCHMARK) and old_url.endswith(f"/{task_id}.txt"), old_url
        set_address(p, f"{REPO}/blob/main/experiment/coder-run/{task_id}_{name}/description.txt")

    local = [p for p in paragraphs if p.text.startswith("Описание (локальная копия)")]
    assert len(local) == len(TASKS)
    for p in local:
        p._p.getparent().remove(p._p)

    active_ids = {link.get(qn("r:id")) for link in doc._element.xpath(".//w:hyperlink[@r:id]")}
    for rel_id, relation in list(doc.part.rels.items()):
        if relation.reltype == RT.HYPERLINK and rel_id not in active_ids:
            doc.part.drop_rel(rel_id)
    edited = WORK / "edited.docx"
    doc.save(edited)
    with ZipFile(before) as original, ZipFile(edited) as changed, ZipFile(WORK / "REPORT.docx", "w") as final:
        for entry in original.infolist():
            package = changed if entry.filename in PARTS else original
            final.writestr(entry, package.read(entry.filename))


if __name__ == "__main__":
    main()
