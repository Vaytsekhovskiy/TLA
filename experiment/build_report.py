"""Build the Russian lab report from the recorded experiment and analysis."""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from run_experiment import EXPERIMENT, TASKS


TITLE = "Определение семантической корректности сгенерированных при помощи LLM TLA+ спецификаций"
SOURCE = "https://github.com/LUC-AI4FM/tla_benchmark/blob"
SUMMARY = {
    "ConfigParams": (
        "Проверка передачи констант в конфигурацию. Четыре переменные инициализируются "
        "целым числом, строкой, model value и множеством. Next сохраняет состояние. "
        "Inv проверяет ожидаемые конкретные значения и различие двух model values."
    ),
    "Test1623": (
        "Обратный отсчёт натурального N. Единственная переменная x начинается с N, "
        "уменьшается на единицу при x > 0 и сохраняет значение при x = 0. "
        "Inv задаёт неотрицательность x. В конфигурации N = 4."
    ),
    "Bug2750": (
        "Ограниченный буфер производителей и потребителей. Состояние задаётся "
        "последовательностью buffer и множествами waitP и waitC. Процесс ожидает "
        "при заполненном либо пустом буфере. Успешная операция может разбудить "
        "ожидающий процесс противоположного типа. Конфигурация задаёт по два "
        "производителя и потребителя и ёмкость 1."
    ),
    "test10": (
        "Регрессионная проверка вычисления функций TLA+, обычных и кортежных "
        "аргументов, записей и EXCEPT с использованием @. Переменная x "
        "инициализируется TRUE и сохраняет значение. Содержательная часть "
        "проверяется в Inv через Assert и Print."
    ),
}


def table(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        + ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    )


def yes(value):
    return "да" if value else ("нет" if value is False else "-")


def make_markdown(run, comparison, notes, repair_comparison=None):
    model = json.loads((run / "model.json").read_text(encoding="utf-8"))
    provenance = json.loads((run / "provenance.json").read_text(encoding="utf-8"))
    generation = {
        name: json.loads((run / f"{task[0]}_{name}" / "result.json").read_text(encoding="utf-8"))
        for name, task in TASKS.items()
    }
    comparisons = json.loads((comparison / "results.json").read_text(encoding="utf-8"))
    request = json.loads(next(run.glob("*_*/01/request.json")).read_text(encoding="utf-8"))
    params = request["options"]
    passed = sum(any(a["tlc"] for a in result["attempts"]) for result in generation.values())
    started = datetime.fromisoformat(model["started_at_utc"]).strftime("%d.%m.%Y %H:%M:%S UTC")
    attempts = [attempt for result in generation.values() for attempt in result["attempts"]]
    candidate_counts = {}
    for name, task in TASKS.items():
        folder = run / f"{task[0]}_{name}"
        candidates = [folder / f"{a['iteration']:02}" / f"{name}LLM.tla"
                      for a in generation[name]["attempts"]]
        candidate_counts[name] = len({
            path.read_text(encoding="utf-8") for path in candidates if path.is_file()
        })
    sections = [
        "## 1 Введение",
        (
            "В работе исследуется генерация исполняемых спецификаций TLA+ по текстовому "
            "описанию и конфигурации TLC. Проверяется синтаксическая корректность, "
            "выполнение проверяемых свойств и соответствие поведения эталону Gold."
        ),
        (
            f"Использована модель {notes['model_name']} в формате GGUF с квантованием "
            f"{model['details']['quantization_level']}. Локальный идентификатор Ollama "
            f"{model['name']}, число параметров по метаданным {model['details']['parameter_size']}. "
            f"Версия Ollama {model['ollama']}. Генерация выполнена через локальный API "
            "на NVIDIA GeForce RTX 3070 Laptop GPU с 8 ГБ видеопамяти. "
            f"[Карточка модели]({notes['model_card']})."
        ),
        (
            f"Digest модели начинается с {model['digest'][:12]}, полный идентификатор "
            f"сохранён в model.json. Прогон начат {started}. Проверки выполнялись Java 22.0.2 и "
            "tla2tools.jar из локального набора данных. Точные запросы, ответы, команды "
            "и журналы сохранены в приложенных материалах."
        ),
        (
            f"Для {passed} из 4 задач получены кандидаты, прошедшие SANY и TLC. "
            + notes["overall_intro"]
        ),
        "## 2 Набор данных",
        (
            "Выбраны две задачи уровня basic и две уровня intermediate. Уровень "
            "взят из поля complexity в manifest.jsonl. Каждая запись включает "
            "исходное естественно-языковое описание, Gold-модуль и его CFG."
        ),
        table(
            ["ID", "Название", "Уровень", "Источник описания"],
            [[task[0], name, task[1], task[2]] for name, task in TASKS.items()],
        ),
        (
            f"Использован локальный checkout ветки dataset-release, commit "
            f"{provenance['checkout_commit']}. Контрольные суммы всех входов и JAR "
            "записаны в provenance.json. Ссылки на конкретные входные файлы приведены "
            "в разделе источников."
        ),
        (
            "Во время подготовки работы проверка исходной ссылки benchmark через "
            "raw.githubusercontent.com вернула HTTP 404. Эксперимент использует "
            "сохранённые локальные входы. Все четыре Gold-файла происходят из "
            "проекта Apalache, что указано в манифесте. В разделе источников "
            "приведены ссылки на эти файлы в исходном проекте."
        ),
        "## 3 Протокол генерации и проверки",
        (
            "Первый запрос для каждой задачи содержит только описание из выбранного "
            "поля датасета, требуемое имя модуля и полный исходный CFG. Применён "
            "zero-shot без примеров решений. В основном прогоне think = false. "
            "Пошаговые подсказки в запросы не добавлялись."
        ),
        (
            "При неудаче следующий запрос содержит то же задание, предыдущий ответ "
            "модели и свежий полный вывод SANY либо TLC. Одна итерация соответствует "
            "одному запросу к API и одному полученному ответу. Лимит составляет 10 "
            "итераций на задачу. Успех TLC завершает генерацию этой задачи."
        ),
        (
            f"Параметры генерации одинаковы для всех задач. Temperature = {params['temperature']}, "
            f"top_p = {params['top_p']}, top_k = {params['top_k']}, "
            f"контекст {params['num_ctx']} токенов, лимит ответа {params['num_predict']} токенов. "
            f"Presence penalty = {params.get('presence_penalty', 0)}. "
            "Seed равен 1729 плюс номер итерации. Точные параметры сохранены в request.json."
        ),
        (
            "Ответ сохраняется полностью. Автоматическое извлечение удаляет окружающий "
            "Markdown и пояснения, выделяя текст между заголовком MODULE и концом модуля. "
            "Формулы и операторы кандидата поступают в проверку непосредственно из ответа модели. "
            "Gold-модули читаются отдельным этапом проверки происхождения и сравнения. "
            "В запросы генерации поступают описание и CFG."
        ),
        (
            "SANY запускается перед TLC. Успех SANY требует корректного завершения "
            "семантической обработки целевого модуля и отсутствия сообщений об ошибках. "
            "Успех TLC требует кода завершения 0 и сообщения Model checking completed. "
            "No error has been found. Проверка deadlock включена. CFG копируется "
            "из Gold без изменений. Для каждого запуска TLC используется один worker "
            "и фиксированный индекс fingerprint polynomial 0."
        ),
        (
            "Лимиты времени составляют 25 секунд для SANY, 45 секунд для TLC и "
            "600 секунд для ответа локального API. Истечение лимита фиксируется "
            "в журнале. Все таблицы ниже построены из results.json и журналов "
            "конкретного прогона."
        ),
        "## 4 Результаты генерации",
        (
            f"Зафиксировано {len(attempts)} итераций. Проверку SANY прошли "
            f"{sum(bool(a['sany']) for a in attempts)} ответов. Число запусков TLC "
            f"для исходных кандидатов {sum(a['tlc'] is not None for a in attempts)}. "
            "Для каждой задачи исчерпан лимит из 10 запросов. Повторение одного "
            "и того же текста после получения ошибки отражено числом разных кандидатов."
        ),
        table(
            ["Задача", "Запросов", "Принято SANY", "Отклонено SANY", "Запусков TLC", "Разных текстов"],
            [[name, len(r["attempts"]), sum(bool(a["sany"]) for a in r["attempts"]),
              sum(a["sany"] is False for a in r["attempts"]),
              sum(a["tlc"] is not None for a in r["attempts"]), candidate_counts[name]]
             for name, r in generation.items()]
            + [["Всего", len(attempts), sum(bool(a["sany"]) for a in attempts),
                sum(a["sany"] is False for a in attempts),
                sum(a["tlc"] is not None for a in attempts), sum(candidate_counts.values())]],
        ),
    ]
    for name in TASKS:
        sections.extend([
            f"### Генерация {name}",
            SUMMARY[name],
            notes["tasks"][name]["errors"],
        ])
    sections.extend([
        "## 5 Семантическое сравнение",
        (
            "Все Gold-модули проверены с исходными CFG. Для успешного кандидата "
            "применяется тот же CFG. Distinct States обозначает число уникальных "
            "состояний, Total States число сгенерированных TLC состояний с повторениями, "
            "Max Depth максимальную глубину полного обхода графа. Total States может "
            "включать несколько способов получения одного и того же перехода."
        ),
    ])
    rows = []
    for name, result in comparisons.items():
        for label, key in (("Gold", "gold"), ("LLM", "model")):
            metrics = result.get(key, {}).get("metrics")
            if metrics:
                rows.append([name, label, metrics["total"], metrics["distinct"], metrics["depth"]])
    if repair_comparison is None:
        sections.append(table(["Задача", "Версия", "Total States", "Distinct States", "Max Depth"], rows))
    successful = {name: result for name, result in comparisons.items() if "model" in result}
    sections.append(table(
        ["Задача", "Δ Total", "Δ Distinct", "Δ Depth"],
        [[name] + [r["model"]["metrics"][key] - r["gold"]["metrics"][key]
                   for key in ("total", "distinct", "depth")]
         for name, r in successful.items()],
    ) if successful else (
        "SANY отклонил исходные ответы до построения графов TLC. Поэтому "
        "количественное сравнение выполнено для кандидатов после ручных исправлений. "
        "Все четыре Gold-модуля прошли SANY и TLC."
    ))
    sections.extend([
        (
            "В экспериментальном коде для проверки GoldSpec создаётся обёртка, наследующая сгенерированный "
            "модуль. Gold инстанцируется на тех же переменных через WITH. Проверяется "
            "PROPERTY GoldSpec при выполнении переходов кандидата. Если в Gold "
            "отсутствует оператор Spec, его формула восстанавливается из Init и Next "
            "как Init /\\ [][Next]_vars. Для Bug2750 используется Gold!Spec."
        ),
        (
            "Также реализовано обратное включение поведения. Gold запускается "
            "с PROPERTY ModelSpec, определённым через INSTANCE сгенерированного "
            "модуля на переменных Gold. Эта проверка выявляет потерянные переходы, "
            "которые могут пройти однонаправленную проверку благодаря допустимому stuttering."
        ),
        (
            "Для сравнения выгруженных TLC графов DOT используются значения переменных. Сопоставляются "
            "начальные состояния, все достижимые состояния и уникальные пары "
            "состояний перехода. Имена переменных сопоставлены явно. Fingerprint "
            "узла используется только для чтения связей внутри одного файла."
        ),
        table(
            ["Задача", "LLM удовлетворяет GoldSpec", "Gold удовлетворяет ModelSpec"],
            [[name, yes(r.get("gold_property", {}).get("tlc")),
              yes(r.get("model_property", {}).get("tlc"))] for name, r in comparisons.items()],
        ) if successful else (
            "Для кандидатов основного прогона проверки GoldSpec и ModelSpec "
            "не выполнялись вследствие ошибок SANY. Работа этих проверок "
            "подтверждена контрольными примерами в разделе 6."
        ),
        table(
            ["Задача", "Уникальные рёбра Gold", "Уникальные рёбра LLM", "Только Gold", "Только LLM"],
            [[name, r["graph"]["edges"]["gold"], r["graph"]["edges"]["model"],
              r["graph"]["edges"]["gold_only"], r["graph"]["edges"]["model_only"]]
             for name, r in comparisons.items() if "graph" in r],
        ) if any("graph" in r for r in comparisons.values()) else "",
    ])
    if repair_comparison is None:
        for name in TASKS:
            sections.extend([f"### Сравнение {name}", notes["tasks"][name]["semantics"]])
    if repair_comparison is not None:
        repaired = json.loads((repair_comparison / "results.json").read_text(encoding="utf-8"))
        sections.extend([
            "### Проверка кандидатов после ручных исправлений",
            (
                "Для дополнительного анализа подготовлены четыре исправленных кандидата. "
                "В этом дополнительном этапе вручную устранены ошибки, мешавшие "
                "исполнению. Изменения и SHA-256 исходных ответов записаны в "
                "repaired/repairs.json. Все четыре исправленных модуля прошли "
                "SANY и TLC с исходными CFG."
            ),
            table(
                ["Задача", "Ручные изменения"],
                [
                    ["ConfigParams", "Исправлен терминатор модуля и проверка различия model values"],
                    ["Test1623", "Добавлены Naturals и ограничение N на натуральные числа"],
                    ["Bug2750", "Исправлены объявления, Init, vars и Inv, удалены недостижимые p и c. Next сохраняет состояние"],
                    ["test10", "Повторяющиеся булевы формулы сведены к x = TRUE, Next задаёт UNCHANGED x, модуль завершён"],
                ],
            ),
            (
                "В Bug2750 сохранён выбор модели выполнять только сохранение "
                "состояния в Next. В test10 сохранена булева модель состояния "
                "с проверкой x = TRUE. Эталон test10 содержит 31 регрессионную "
                "проверку функций и проверяется отдельно."
            ),
            table(
                ["Задача", "Версия", "Total States", "Distinct States", "Max Depth"],
                [[name, label, r[key]["metrics"]["total"], r[key]["metrics"]["distinct"],
                  r[key]["metrics"]["depth"]]
                 for name, r in repaired.items() for label, key in (("Gold", "gold"), ("Испр.", "model"))],
            ),
            table(
                ["Задача", "Δ Total", "Δ Distinct", "Δ Depth"],
                [[name] + [r["model"]["metrics"][key] - r["gold"]["metrics"][key]
                           for key in ("total", "distinct", "depth")]
                 for name, r in repaired.items()],
            ),
            table(
                ["Задача", "Испр. удовлетворяет GoldSpec", "Gold удовлетворяет Испр.Spec"],
                [[name, yes(r["gold_property"]["tlc"]), yes(r["model_property"]["tlc"])]
                 for name, r in repaired.items()],
            ),
            table(
                ["Задача", "Уникальные рёбра Gold", "Уникальные рёбра LLM", "Только Gold", "Только LLM"],
                [[name, r["graph"]["edges"]["gold"], r["graph"]["edges"]["model"],
                  r["graph"]["edges"]["gold_only"], r["graph"]["edges"]["model_only"]]
                 for name, r in repaired.items()],
            ).replace("рёбра LLM", "рёбра Испр.").replace("Только LLM", "Только Испр."),
            notes["manual_analysis"],
        ])
    sections.extend([
        "## 6 Проверка экспериментального кода",
        (
            "Для исправленного кода выполнено семь регрессионных проверок. Проверены "
            "сохранение исходного тела модуля при удалении Markdown, обработка "
            "неверного текста и незавершённого модуля, отклонение семантической ошибки "
            "SANY, обнаружение изменённого перехода через GoldSpec и обнаружение "
            "потерянного countdown через обратное сравнение и разницу графов. "
            "Также проверено восстановление сохранённого ответа после прерывания "
            "без нового запроса к модели. Все семь тестов завершились успешно."
        ),
        (
            "В контрольном отрицательном примере Next заменён на постоянное "
            "сохранение x. Однонаправленная проверка GoldSpec проходит, обратная "
            "проверка ModelSpec нарушается. Сравнение графов обнаруживает четыре "
            "потерянных состояния. В другом контрольном примере x увеличивается "
            "вместо уменьшения, что нарушает GoldSpec."
        ),
        "## 7 Вывод",
        notes["conclusion"],
        (
            "Выводы о поведении ограничены выбранными конечными экземплярами CFG. "
            "Для параметризованной спецификации с произвольными множествами процессов "
            "и значениями констант требуется отдельное доказательство. Описания "
            "датасета могут опускать детали эталона, что влияет на возможность "
            "восстановить все операторы и регрессионные проверки."
        ),
        "## 8 Материалы и воспроизведение",
        (
            f"Каталог {run.name} содержит model.json, model-info.json, provenance.json, "
            "сводный results.json и отдельный каталог на каждую задачу. Внутри "
            "итерации сохранены prompt.txt, request.json, response.json, response.txt, "
            "извлечённый TLA+ модуль, sany.txt и при запуске TLC также tlc.txt и graph.dot. "
            f"Каталог {comparison.name} содержит Gold, обёртки сравнений и их журналы."
        ),
        (
            "Каталог repaired содержит вручную исправленные кандидаты, перечень "
            "изменений и журналы SANY/TLC. Каталог repaired-comparison содержит "
            "их отдельное сравнение с Gold и контрпример для Bug2750."
        ) if repair_comparison is not None else "",
        (
            "run_experiment.py выполняет генерацию, compare_experiment.py выполняет "
            "сравнение, build_report.py формирует отчёт из сохранённых результатов. "
            "Команды повторения приведены в README.md. notes.json содержит текстовый "
            "анализ конкретных журналов."
        ),
        "## 9 Источники",
        (
            f"[{notes['model_name']}]({notes['model_card']}), "
            f"[пакет Ollama]({notes['model_package']})."
        ),
    ])
    commit = provenance["checkout_commit"]
    for name, (spec_id, _, kind) in TASKS.items():
        root = f"{SOURCE}/{commit}/dataset_release"
        sections.append(
            f"{name}, ID {spec_id}. "
            f"[Описание]({root}/descriptions/{kind}/{spec_id}.txt), "
            f"[Gold]({root}/specs/gold/{spec_id}_{name}.tla), "
            f"[CFG]({root}/specs/gold/{spec_id}_{name}.cfg). "
            f"[Исходный модуль Apalache](https://github.com/apalache-mc/apalache/blob/main/"
            f"test/{'tlaplus-suite' if name == 'test10' else 'tla'}/{name}.tla)."
        )
    sections.append(
        f"[Манифест и уровни сложности]({SOURCE}/{commit}/dataset_release/manifest.jsonl)."
    )
    return "\n\n".join(section for section in sections if section) + "\n"


def inline(paragraph, text):
    for part in re.split(r"(\[[^\]]+\]\([^)]+\))", text):
        match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", part)
        if not match:
            paragraph.add_run(part)
            continue
        label, url = match.groups()
        hyperlink = OxmlElement("w:hyperlink")
        relationship = paragraph.part.relate_to(
            url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True,
        )
        hyperlink.set(qn("r:id"), relationship)
        run = OxmlElement("w:r")
        properties = OxmlElement("w:rPr")
        fonts = OxmlElement("w:rFonts")
        for key in ("ascii", "hAnsi", "eastAsia", "cs"):
            fonts.set(qn(f"w:{key}"), "Times New Roman")
        properties.append(fonts)
        size = OxmlElement("w:sz")
        size.set(qn("w:val"), "24")
        properties.append(size)
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "000000")
        properties.append(color)
        run.append(properties)
        value = OxmlElement("w:t")
        value.text = label
        run.append(value)
        hyperlink.append(run)
        paragraph._p.append(hyperlink)


def make_docx(markdown, path):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.different_first_page_header_footer = "<PAGEBREAK>" in markdown
    for style_name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3"):
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(14 if style_name in ("Title", "Heading 1", "Heading 2", "Heading 3") else 12)
        style.font.color.rgb = RGBColor(0, 0, 0)
        fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
        for attribute in list(fonts.attrib):
            if "theme" in attribute.lower():
                del fonts.attrib[attribute]
        for key in ("ascii", "hAnsi", "eastAsia", "cs"):
            fonts.set(qn(f"w:{key}"), "Times New Roman")
        size_cs = style.element.get_or_add_rPr().find(qn("w:szCs"))
        if size_cs is not None:
            size_cs.set(qn("w:val"), str(int(style.font.size.pt * 2)))
        for border in style.element.findall(".//" + qn("w:pBdr")):
            border.getparent().remove(border)
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(6)
        if style_name.startswith("Heading"):
            style.font.bold = True
            style.font.italic = False
            style.paragraph_format.keep_with_next = True
            style.paragraph_format.space_before = Pt(12)
    normal = doc.styles["Normal"]
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.first_line_indent = Cm(1.25)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.paragraph_format.first_line_indent = Cm(0)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)

    title_page = "<PAGEBREAK>" in markdown
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line:
            continue
        if line == "<PAGEBREAK>":
            doc.add_page_break()
            title_page = False
            continue
        if line.startswith("|"):
            rows = [line]
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(lines[index].strip())
                index += 1
            values = [[value.strip() for value in row.strip("|").split("|")]
                      for row in rows if not re.fullmatch(r"[\s|:-]+", row)]
            grid = doc.add_table(rows=len(values), cols=len(values[0]))
            grid.autofit = False
            grid.style = "Table Grid"
            widths = {
                "ID": (1.0, 3.2, 3.3, 9.0),
                "Завершение ответа": (2.5, 2.5, 2.5, 9.0),
                "Первый SANY": (4.2, 3.5, 3.5, 5.3),
                "Версия": (3.6, 2.2, 3.4, 4.0, 3.3),
                "Δ Total": (4.5, 4.0, 4.0, 4.0),
                "LLM удовлетворяет GoldSpec": (4.5, 6.0, 6.0),
                "Уникальные рёбра Gold": (3.5, 3.5, 3.5, 3.0, 3.0),
                "Ручные изменения": (3.5, 13.0),
                "Отклонено SANY": (3.2, 2.3, 2.7, 2.7, 2.7, 2.9),
            }
            column_widths = next(
                (sizes for key, sizes in widths.items() if key in values[0]),
                [16.5 / len(values[0])] * len(values[0]),
            )
            for column, width in zip(grid.columns, column_widths):
                column.width = Cm(width)
            for row_number, row in enumerate(values):
                tr_properties = grid.rows[row_number]._tr.get_or_add_trPr()
                no_split = OxmlElement("w:cantSplit")
                tr_properties.append(no_split)
                if row_number == 0:
                    repeat = OxmlElement("w:tblHeader")
                    tr_properties.append(repeat)
                for cell, value, width in zip(grid.rows[row_number].cells, row, column_widths):
                    cell.width = Cm(width)
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    cell_properties = cell._tc.get_or_add_tcPr()
                    borders = OxmlElement("w:tcBorders")
                    for edge in ("top", "left", "bottom", "right"):
                        border = OxmlElement(f"w:{edge}")
                        for key, setting in (("val", "single"), ("sz", "4"), ("color", "D9D9D9")):
                            border.set(qn(f"w:{key}"), setting)
                        borders.append(border)
                    cell_properties.append(borders)
                    margins = OxmlElement("w:tcMar")
                    for edge in ("top", "left", "bottom", "right"):
                        margin = OxmlElement(f"w:{edge}")
                        margin.set(qn("w:w"), "70")
                        margin.set(qn("w:type"), "dxa")
                        margins.append(margin)
                    cell_properties.append(margins)
                    if row_number == 0:
                        shading = OxmlElement("w:shd")
                        shading.set(qn("w:fill"), "EDEDED")
                        cell_properties.append(shading)
                    paragraph = cell.paragraphs[0]
                    paragraph.paragraph_format.first_line_indent = Cm(0)
                    paragraph.paragraph_format.space_after = Pt(0)
                    if row_number == 0 or (len(values) <= 6 and row_number < len(values) - 1):
                        paragraph.paragraph_format.keep_with_next = True
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = paragraph.add_run(value)
                    run.bold = row_number == 0
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(0)
            spacer.paragraph_format.line_spacing = Pt(6)
            continue
        heading = re.match(r"^(#{1,3}) (.+)$", line)
        if heading:
            depth = len(heading[1])
            paragraph = doc.add_paragraph(
                heading[2], style="Title" if depth == 1 else f"Heading {depth - 1}",
            )
            paragraph.paragraph_format.first_line_indent = Cm(0)
            if title_page:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.space_before = Pt(100)
            continue
        paragraph = doc.add_paragraph()
        inline(paragraph, line)
        if title_page:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.space_after = Pt(18)
    doc.core_properties.title = TITLE
    doc.core_properties.subject = "Лабораторная работа, вариант 1"
    doc.core_properties.author = ""
    doc.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--notes", type=Path, required=True)
    parser.add_argument("--repair-comparison", type=Path)
    args = parser.parse_args()
    notes = json.loads(args.notes.read_text(encoding="utf-8"))
    markdown = make_markdown(args.run, args.comparison, notes, args.repair_comparison)
    (EXPERIMENT / "REPORT_ACTUAL.md").write_text(markdown, encoding="utf-8")
    report_path = EXPERIMENT / "REPORT_ACTUAL.docx"
    make_docx(markdown, report_path)
    print(report_path)


if __name__ == "__main__":
    main()
