"""Safe, deterministic CSV validation and profiling for the first V3 slice."""

import csv
import hashlib
import io
import re
from collections import defaultdict
from typing import Dict, List, Tuple

from .models import CSVAnalysisPlan, CSVAnalysisResult, CSVProfile


class CSVValidationError(ValueError):
    pass


def profile_csv(
    filename: str, content: bytes, max_bytes: int = 25 * 1024 * 1024
) -> CSVProfile:
    if not filename.lower().endswith(".csv"):
        raise CSVValidationError("Somente arquivos .csv são aceitos")
    if not content:
        raise CSVValidationError("O CSV está vazio")
    if len(content) > max_bytes:
        raise CSVValidationError("O CSV excede o limite de tamanho")
    text, encoding = _decode(content)
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames or any(
        not name or not name.strip() for name in reader.fieldnames
    ):
        raise CSVValidationError("O CSV precisa ter cabeçalho válido")
    columns = [name.strip() for name in reader.fieldnames]
    if len(set(columns)) != len(columns):
        raise CSVValidationError("O CSV possui colunas duplicadas")
    null_counts = {column: 0 for column in columns}
    numeric_columns = {column: True for column in columns}
    numeric_seen = {column: False for column in columns}
    row_count = 0
    warnings: List[str] = []
    for row in reader:
        row_count += 1
        for column in columns:
            value = (row.get(column) or "").strip()
            if not value:
                null_counts[column] += 1
            else:
                numeric_seen[column] = True
                if numeric_columns[column] and not _is_number(value):
                    numeric_columns[column] = False
    if row_count == 0:
        warnings.append("O CSV não possui linhas de dados")
    formula_cells = sum(
        1
        for row in csv.DictReader(io.StringIO(text), dialect=dialect)
        for value in row.values()
        if isinstance(value, str) and _is_formula_candidate(value)
    )
    if formula_cells:
        warnings.append(
            "Células com possível fórmula foram identificadas e devem ser "
            "tratadas como texto"
        )
    return CSVProfile(
        dataset_id="ds_" + hashlib.sha256(content).hexdigest()[:32],
        filename=filename,
        encoding=encoding,
        delimiter=dialect.delimiter,
        row_count=row_count,
        columns=columns,
        null_counts=null_counts,
        numeric_columns=[
            column
            for column, is_numeric in numeric_columns.items()
            if is_numeric and numeric_seen[column]
        ],
        warnings=warnings,
    )


def analyze_csv(
    filename: str, content: bytes, plan: CSVAnalysisPlan
) -> CSVAnalysisResult:
    """Run only allowlisted deterministic operations; never evaluates code/SQL."""
    profile = profile_csv(filename, content)
    text, _encoding = _decode(content)
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    _validate_plan(profile, plan)
    filtered = [
        row
        for row in rows
        if all(
            (row.get(key) or "").strip() == value for key, value in plan.filters.items()
        )
    ]
    if plan.operation == "count":
        values = [1.0 for _row in filtered]
    else:
        assert plan.column is not None
        values = [_number(row.get(plan.column, ""), plan.column) for row in filtered]
    warnings = list(profile.warnings)
    if plan.operation == "count":
        aggregate = float(len(values))
    elif plan.operation == "sum":
        aggregate = sum(values)
    elif plan.operation == "mean":
        aggregate = sum(values) / len(values) if values else 0.0
    elif plan.operation == "min":
        aggregate = min(values) if values else 0.0
    else:
        aggregate = max(values) if values else 0.0
    groups: Dict[str, float] = {}
    if plan.group_by:
        grouped: Dict[str, List[float]] = defaultdict(list)
        for row, numeric in zip(filtered, values):
            grouped[(row.get(plan.group_by) or "").strip()].append(numeric)
        for key, group_values in grouped.items():
            if plan.operation == "count":
                groups[key] = float(len(group_values))
            elif plan.operation == "sum":
                groups[key] = sum(group_values)
            elif plan.operation == "mean":
                groups[key] = sum(group_values) / len(group_values)
            elif plan.operation == "min":
                groups[key] = min(group_values)
            else:
                groups[key] = max(group_values)
    return CSVAnalysisResult(
        dataset_id=profile.dataset_id,
        operation=plan.operation,
        column=plan.column,
        value=aggregate if not plan.group_by else None,
        groups=groups,
        warnings=warnings,
    )


def _decode(content: bytes) -> Tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return content.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise CSVValidationError("Encoding do CSV não suportado; use UTF-8 ou Windows-1252")


def _is_number(value: str) -> bool:
    return bool(re.fullmatch(r"[-+]?\d+(?:[.,]\d+)?", value))


def _is_formula_candidate(value: str) -> bool:
    return value.startswith(("=", "@")) or (
        value.startswith(("+", "-")) and not _is_number(value)
    )


def _validate_plan(profile: CSVProfile, plan: CSVAnalysisPlan) -> None:
    if plan.operation != "count" and not plan.column:
        raise CSVValidationError("A operação exige uma coluna numérica")
    if plan.column and plan.column not in profile.columns:
        raise CSVValidationError("A coluna solicitada não existe no CSV")
    if plan.group_by and plan.group_by not in profile.columns:
        raise CSVValidationError("A coluna de agrupamento não existe no CSV")
    if plan.column and plan.column not in profile.numeric_columns:
        raise CSVValidationError("A coluna de análise não é numérica")
    unknown_filters = set(plan.filters) - set(profile.columns)
    if unknown_filters:
        raise CSVValidationError("O filtro referencia coluna inexistente")


def _number(raw: str, column: str) -> float:
    value = raw.strip().replace(",", ".")
    try:
        return float(value)
    except ValueError as exc:
        raise CSVValidationError(f"Valor não numérico na coluna {column}") from exc
