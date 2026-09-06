"""Парсинг PLAN.md и LOG.md."""

import re


def parse_plan(text: str) -> tuple[list[str], list[str]]:
    """Возвращает (сделанные пункты, несделанные пункты).

    Считает только раздел «## Чеклист» — там недели курса; чекбоксы в теле
    документа это критерии приёмки проектов, они в прогресс не идут.
    """
    _, _, checklist = text.partition("## Чеклист")
    scope = checklist or text
    done = re.findall(r"^\s*- \[x\] (.+)$", scope, re.M | re.I)
    todo = re.findall(r"^\s*- \[ \] (.+)$", scope, re.M)
    return done, todo


def parse_log(text: str) -> list[dict[str, str]]:
    """Записи LOG.md в порядке файла. Шаблон («Неделя N») пропускается."""
    entries = []
    for chunk in re.split(r"^## ", text, flags=re.M)[1:]:
        title, _, body = chunk.partition("\n")
        if not title.startswith("Неделя") or "Неделя N" in title:
            continue
        fields = dict(re.findall(r"^- (\w[^:]*): ?(.*)$", body, re.M))
        entries.append({"title": title.strip(), **fields})
    return entries
