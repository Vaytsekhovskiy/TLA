"""Build the explicitly illustrative Word report for variant 1."""

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiment"
sys.path.insert(0, str(EXPERIMENT))
from build_report import SOURCE, SUMMARY, TASKS, TITLE, make_docx, table


EXAMPLES = {
    "ConfigParams": {
        "prompt": "об инициализации x, y, z и w, строковом значении, множестве и различии двух model values",
        "iterations": [(1, 1), (2, 3), (1, 2), (2, 2)],
        "sany": "П2, ит. 1: ошибочное имя MyModelVal2. П4, ит. 1: лишняя запятая после последнего имени в CONSTANTS. П1 и П3 прошли SANY с первого ответа.",
        "tlc": "П2, ит. 2: в Inv проверялась принадлежность z значению MyModelValue2, которое не является множеством. П3, ит. 1: действие не задавало w′. П1 и П4 прошли TLC при первом запуске.",
        "graphs": [(2, 1, 1, True), (2, 1, 1, True), (4, 2, 2, False), (2, 1, 1, True)],
        "graph_analysis": "П1, П2 и П4 сохраняют единственное состояние Gold. В П3 появляются дополнительное состояние и уровень графа. Ослабленный Inv П3 проверяет целочисленность x, поэтому TLC допускает переход от x = 42 к x = 43.",
        "property_analysis": "В П3 переход x = 42 → x = 43 нарушает GoldSpec. У Gold переменная x неизменна. В П1, П2 и П4 GoldSpec и обратная проверка проходят при значениях констант из CFG. В П4 отсутствует проверка различия model values в Inv. На данном CFG значения различны, поэтому совпадение графов не подтверждает полноту Inv.",
    },
    "Test1623": {
        "prompt": "об обратном отсчёте от натурального числа N, уменьшении x на единицу и сохранении нуля",
        "iterations": [(2, 3), (1, 1), (1, 2), (2, 3), (2, 2)],
        "sany": "П1, ит. 1: операторы > и − недоступны без импорта арифметического модуля. П4, ит. 1: использован необъявленный Dec. П5, ит. 1: в предположении о N использовано неизвестное множество Natural. П2 и П3 приняты с первого ответа.",
        "tlc": "П1, ит. 2, и П3, ит. 1: deadlock при x = 0, поскольку Next определял переходы только для x > 0. П4, ит. 2: ветвь при x = 0 не определяла x′. П2 и П5 прошли TLC при первом запуске.",
        "graphs": [(6, 5, 5, True), (6, 5, 5, True), (5, 4, 4, False), (6, 5, 5, True), (6, 5, 5, True)],
        "graph_analysis": "П1, П2, П4 и П5 воспроизводят последовательность 4 → 3 → 2 → 1 → 0. В П3 выполняется скачок 2 → 0. Граф теряет состояние x = 1, один сгенерированный переход и один уровень глубины.",
        "property_analysis": "TLC выявляет нарушение GoldSpec в П3 на переходе 2 → 0. Обратная проверка также обнаруживает расхождение, поскольку кандидат не разрешает переход Gold 2 → 1. В остальных четырёх прогонах совпадают начальное состояние и переходы при N = 4.",
    },
    "Bug2750": {
        "prompt": "о буфере ограниченной ёмкости, действиях производителей и потребителей, множествах ожидания и пробуждении одного ожидающего процесса",
        "iterations": [(3, 5), (1, 2), (2, 3), (2, 4), (1, 3)],
        "sany": "П1, ит. 1: присваивание значения в CONSTANTS. П1, ит. 2: неизвестный оператор card. П3, ит. 1: неизвестный оператор SeqLen. П4, ит. 1: синтаксическая ошибка в EXCEPT. П2 и П5 прошли SANY с первого ответа.",
        "tlc": "П1, ит. 3: ветвь полного буфера не задавала buffer′. П1, ит. 4: нарушен Inv, все процессы оказались в ожидании. П2, ит. 1: deadlock в начальном состоянии. П3, ит. 2: действие записи не задавало waitC′. П4, ит. 2: множеству передавались операции над последовательностью, а на ит. 3 нарушался Inv. П5, ит. 1: чтение элемента пустого буфера, а на ит. 2 нарушался Inv.",
        "graphs": [(97, 36, 7, True), (2, 1, 1, True), (61, 24, 7, True), (97, 36, 7, True), (97, 36, 7, True)],
        "graph_analysis": "П1, П4 и П5 совпадают с Gold по трём метрикам. П2 сохраняет только начальное состояние. В П3 задан фиксированный приоритет пробуждения в пределах множества ожидающих. Убраны альтернативные переходы, поэтому остаётся 24 различных состояния вместо 36. Максимальная глубина остаётся равной 7.",
        "property_analysis": "Все пять кандидатов удовлетворяют GoldSpec. П2 реализует только stuttering, допустимый в Gold. П3 реализует подмножество переходов Gold. Обратная проверка выявляет потерю поведения в обоих случаях. Например, П2 не разрешает запись p1 в пустой буфер, а П3 при ожидании c1 и c2 разрешает пробуждение только c1. Для П1, П4 и П5 обратная проверка проходит.",
    },
    "test10": {
        "prompt": "о вычислении функций, вызовах с кортежами, записях, обновлениях EXCEPT и неизменном булевом состоянии",
        "iterations": [(2, 3), (2, 2), (1, 2), (3, 4)],
        "sany": "П1, ит. 1: оператор Assert не импортирован из TLC. П2, ит. 1: пропущен ! в EXCEPT. П4, ит. 1: неверная запись конструктора записи, на ит. 2 отсутствовал импорт арифметических операторов. П3 принят с первого ответа.",
        "tlc": "П1, ит. 2: Assert обнаружил неверный результат вызова с кортежем. П3, ит. 1: аргумент оказался вне DOMAIN функции. П4, ит. 3: Assert обнаружил неверное ожидаемое значение суммы. П2 прошёл TLC при первом запуске.",
        "graphs": [(2, 1, 1, True), (2, 1, 1, True), (2, 1, 1, True), (2, 1, 1, True)],
        "graph_analysis": "Во всех четырёх прогонах граф совпадает с Gold по трём метрикам. Единственное достижимое состояние x = TRUE сохраняется на каждом шаге.",
        "property_analysis": "В обоих направлениях включение поведения выполняется для всех прогонов. Проверка графа охватывает изменения x. При отдельном сопоставлении проверок в Inv для П1–П4 найдено соответственно 28, 21, 16 и 25 из 31 проверки Gold. Например, в П3 пропущены случаи вложенных обновлений EXCEPT. Совпадение графа здесь не подтверждает полноту регрессионных проверок.",
    },
}


def example_markdown():
    comparison = json.loads(
        (EXPERIMENT / "coder-comparison/results.json").read_text(encoding="utf-8")
    )
    metadata = json.loads(
        (EXPERIMENT / "coder-run/provenance.json").read_text(encoding="utf-8")
    )
    gold_metrics = {
        name: tuple(result["gold"]["metrics"][key] for key in ("total", "distinct", "depth"))
        for name, result in comparison.items()
    }
    successes = sum(len(task["iterations"]) for task in EXAMPLES.values())
    requests = sum(tlc for task in EXAMPLES.values() for _, tlc in task["iterations"])
    passed_gold = sum(
        passes for task in EXAMPLES.values() for *_, passes in task["graphs"]
    )
    blocks = [
        "# " + TITLE,
        "Вариант № 1. Учебный образец отчёта с условными результатами",
        "## 1 Введение",
        (
            "Цель работы — получить по естественно-языковым описаниям четыре спецификации TLA+, "
            "проверяемые SANY и TLC, и оценить их семантическое соответствие эталонам Gold. "
            "В учебном сценарии выбрана одна модель Qwen/Qwen2.5-Coder-7B-Instruct, GGUF Q4_K_M "
            "в Ollama. [Карточка модели](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)."
        ),
        (
            f"Пример включает {successes} условных успешных прогонов по четырём задачам. "
            "Номера итераций, ошибки, показатели и выводы о кандидатах смоделированы. "
            "Строки Gold содержат фактические значения из журналов проверки эталонов. "
            "При заполнении отчёта по собственному эксперименту заменяются таблицы и связанные "
            "с ними комментарии в разделах 3–5."
        ),
        "## 2 Набор данных",
        (
            "Набор включает две задачи уровня basic и две уровня intermediate. Для каждой задачи "
            "используются текстовое описание, эталонный модуль Gold и исходный CFG. "
            "Уровни, идентификаторы и типы описаний взяты из manifest.jsonl ветки dataset-release."
        ),
        table(
            ["ID", "Название", "Уровень", "Тип описания"],
            [[task[0], name, task[1], task[2]] for name, task in TASKS.items()],
        ),
    ]
    source_root = f"{SOURCE}/{metadata['checkout_commit']}/dataset_release"
    for name, (spec_id, _, kind) in TASKS.items():
        spec_link = f"{source_root}/specs/gold/{spec_id}_{name}"
        upstream = "tlaplus-suite" if name == "test10" else "tla"
        blocks.append(
            f"{name}. [Описание]({source_root}/descriptions/{kind}/{spec_id}.txt), "
            f"[Gold]({spec_link}.tla), [CFG]({spec_link}.cfg), "
            f"[исходный модуль Apalache](https://github.com/apalache-mc/apalache/blob/main/test/{upstream}/{name}.tla)."
        )
    blocks.extend([
        "Материалы benchmark доступны в сохранённой локальной копии. Ссылки на файлы привязаны к её коммиту.",
        "## 3 Генерация спецификаций при помощи LLM",
        (
            "Для генерации спецификаций при помощи LLM использовался следующий подход. "
            "Каждый прогон начинается с нового контекста. Одна итерация — один запрос и один "
            "ответ модели. SANY выполняется перед TLC. В графе «SANY прошёл» указана первая "
            "успешная итерация SANY. В графе «TLC прошёл» указана итерация, на которой текущий "
            "ответ прошёл обе проверки. Лимит — 10 итераций на прогон. Обозначения П1, П2 и далее "
            "нумеруются заново для каждой задачи."
        ),
    ])
    for name, task in EXAMPLES.items():
        assert len(task["iterations"]) == len(task["graphs"]) >= 4
        assert all(1 <= sany <= tlc <= 10 for sany, tlc in task["iterations"])
        blocks.extend([
            f"### Название задачи: {name}",
            (
                f"А) В промпте содержалась информация {task['prompt']}. "
                "Использовался zero-shot с исходным CFG. Пошаговое рассуждение "
                "(Chain of Thought) не запрашивалось. На каждой итерации для исправления "
                "модели передавались описание, CFG, её предыдущий ответ и свежий лог "
                "SANY либо TLC. Текст модуля Gold и подсказки по исправлению в запрос не включались."
            ),
            "Б) Во время генерации корректной спецификации LLM совершала следующие типы ошибок.",
            "Для SANY. " + task["sany"],
            "Для TLC. " + task["tlc"],
            "В) Для данной задачи приведены условные метрики по каждому прогону.",
            table(
                ["Прогон", "SANY прошёл на итерации", "TLC прошёл на итерации", "Всего итераций"],
                [[f"П{i}", sany, tlc, tlc] for i, (sany, tlc) in enumerate(task["iterations"], 1)],
            ),
        ])
    blocks.extend([
        "## 4 Проверка семантической корректности",
        (
            "Сравнение проводится для последнего ответа каждого прогона, который прошёл SANY и TLC. "
            "Для кандидата и Gold используются исходные значения констант из одного CFG. "
            "Total States — число сгенерированных состояний с повторами, включая начальное. "
            "Distinct States — число уникальных состояний. Max Depth — глубина обхода. "
            "Δ в таблицах — разность «кандидат минус Gold» для трёх метрик в указанном порядке."
        ),
        (
            "Для проверки поведения эталон подставляется в модуль сравнения через INSTANCE "
            "с сопоставлением переменных. Ниже показана форма для Bug2750. "
            "В остальных трёх эталонах оператор Spec отсутствует, поэтому GoldSpec задаётся "
            "формулой Gold!Init /\\ [][Gold!Next]_vars. В дополнительной обратной проверке "
            "кандидат подставляется в эталон для выявления пропущенных переходов."
        ),
        "Gold == INSTANCE Bug2750 WITH buffer <- buffer, waitP <- waitP, waitC <- waitC\n"
        "GoldSpec == Gold!Spec\n"
        "Строка в CFG — PROPERTY GoldSpec.",
    ])
    for name, task in EXAMPLES.items():
        gold = gold_metrics[name]
        rows = [["Gold", *gold, "0 / 0 / 0", "Эталон"]]
        for number, (*metrics, passes) in enumerate(task["graphs"], 1):
            assert metrics[0] >= metrics[1] >= metrics[2] >= 1
            deltas = (actual - reference for actual, reference in zip(metrics, gold))
            rows.append([
                f"П{number}", *metrics,
                " / ".join(f"{delta:+}" if delta else "0" for delta in deltas),
                "Да" if passes else "Нет",
            ])
        blocks.extend([
            f"### Название задачи: {name}",
            "Строка Gold содержит измеренные метрики. Остальные строки содержат условные значения.",
            table(
                ["Вариант", "Total States", "Distinct States", "Max Depth", "Δ Total / Distinct / Depth", "GoldSpec"],
                rows,
            ),
            "А) Анализ состояний сгенерированной и Gold спецификаций показал следующие результаты. "
            + task["graph_analysis"],
            "Б) При сравнении двух спецификаций было выяснено следующее. "
            + task["property_analysis"],
        ])
    blocks.extend([
        "## 5 Вывод",
        (
            f"В учебном сценарии {successes} из {successes} финальных кандидатов прошли SANY и TLC. "
            f"Всего смоделировано {requests} итераций. GoldSpec выполняется у {passed_gold} из {successes} "
            "кандидатов. ConfigParams и Test1623 содержат по одному контрпримеру, "
            "в котором TLC принимает кандидата по исходному CFG, а GoldSpec отвергает его переход."
        ),
        (
            "У Bug2750 два кандидата удовлетворяют GoldSpec, хотя пропускают допустимые переходы "
            "эталона. Это выявляет обратная проверка. У test10 совпадающий граф описывает булеву "
            "переменную и оставляет за рамками проверки полноту вычислений в Inv. "
            "У ConfigParams совпадение на заданном CFG также не гарантирует полноту Inv."
        ),
        (
            "Вероятные причины ошибок в этом сценарии — использование имён без импорта, "
            "пропуск присваиваний штрихованным переменным и слишком буквальная обработка описания. "
            "Фиксированный выбор ожидающего процесса в Bug2750 сужает недетерминизм, "
            "а краткое описание test10 допускает неполное восстановление тестовых случаев. "
            "Выводы о переходах относятся к конечным конфигурациям из CFG."
        ),
    ])
    return "\n\n".join(blocks) + "\n"


def main():
    destination = Path(__file__).with_name("REPORT.docx")
    markdown = example_markdown()
    make_docx(markdown, destination)
    doc = Document(destination)
    title = doc.paragraphs[0]
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(8)
    label = doc.paragraphs[1]
    label.alignment = WD_ALIGN_PARAGRAPH.CENTER
    label.paragraph_format.first_line_indent = Cm(0)
    label.paragraph_format.space_after = Pt(8)
    for run in label.runs:
        run.bold = True
    footer = doc.sections[0].footer.paragraphs[0]
    footer.add_run("  •  Учебный образец с условными результатами")
    for grid in doc.tables:
        if grid.cell(0, 0).text == "Вариант":
            widths = (2.0, 2.5, 2.8, 2.4, 4.2, 2.6)
            for column, width in zip(grid.columns, widths):
                column.width = Cm(width)
                for cell in column.cells:
                    cell.width = Cm(width)
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith(("В) Для данной задачи", "Строка Gold содержит")):
            paragraph.paragraph_format.keep_with_next = True
        if paragraph.text.startswith("Gold =="):
            paragraph.paragraph_format.first_line_indent = Cm(0.75)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.keep_with_next = True
        if paragraph.text.startswith("GoldSpec =="):
            paragraph.paragraph_format.first_line_indent = Cm(0.75)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.core_properties.subject = "Вариант 1. Учебный образец с условными результатами"
    doc.save(destination)
    print(destination)


if __name__ == "__main__":
    main()
