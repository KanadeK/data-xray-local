"""Privacy-safe JSON and self-contained HTML report writers."""

from __future__ import annotations

import html
import json
from pathlib import Path

from data_xray_local.domain.models import DataCategory, ScanReport, Severity

SEVERITY_LABEL = {
    Severity.LOW: "Low",
    Severity.MEDIUM: "Medium",
    Severity.HIGH: "High",
    Severity.CRITICAL: "Critical",
}

CATEGORY_LABEL = {
    DataCategory.EMAIL: "Email",
    DataCategory.PHONE: "Phone",
    DataCategory.ADDRESS: "Postal address",
    DataCategory.GOVERNMENT_ID: "Government ID",
    DataCategory.TOKEN: "Credential / token",
    DataCategory.PAYMENT_CARD: "Payment card",
    DataCategory.GPS_LOCATION: "GPS location",
    DataCategory.AUTHOR_METADATA: "Author metadata",
}


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def write_json_report(report: ScanReport, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json")
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def _summary_cards(report: ScanReport) -> str:
    items = (
        ("Files scanned", report.summary.files_scanned),
        ("Masked findings", report.summary.findings),
        ("High-risk files", report.summary.high_risk_files),
        ("Repeated exposures", report.summary.duplicate_groups),
    )
    return "".join(
        f'<article class="metric"><span>{_escape(label)}</span><strong>{value}</strong></article>'
        for label, value in items
    )


def _heatmap_rows(report: ScanReport) -> str:
    if not report.heatmap:
        return '<p class="empty">No detected exposure to plot.</p>'
    return "".join(
        (
            f'<article class="heat-row" data-severity="{cell.severity.value}">'
            f'<div class="heat-copy"><code>{_escape(cell.path)}</code>'
            f"<span>{cell.finding_count} finding(s) · "
            f"{_escape(', '.join(CATEGORY_LABEL[item] for item in cell.categories))}</span></div>"
            f'<div class="heat-track" aria-label="Risk score {cell.risk_score} out of 100">'
            f'<span class="heat-fill {cell.severity.value}" style="width:{cell.risk_score}%"></span>'
            f"</div><strong>{cell.risk_score}</strong></article>"
        )
        for cell in report.heatmap
    )


def _finding_rows(report: ScanReport) -> str:
    if not report.findings:
        return '<tr><td colspan="6" class="empty">No matches detected.</td></tr>'
    rows: list[str] = []
    for finding in report.findings:
        duplicate = finding.duplicate_group or "—"
        rows.append(
            f'<tr data-severity="{finding.severity.value}" '
            f'data-search="{_escape(finding.path.casefold())}">'
            f"<td><code>{_escape(finding.path)}</code></td>"
            f"<td>{_escape(finding.location)}</td>"
            f"<td>{_escape(CATEGORY_LABEL[finding.category])}</td>"
            f'<td><span class="badge {finding.severity.value}">'
            f"{SEVERITY_LABEL[finding.severity]}</span></td>"
            f"<td><code>{_escape(finding.masked_fragment)}</code></td>"
            f"<td>{_escape(duplicate)}</td></tr>"
        )
    return "".join(rows)


def _duplicate_cards(report: ScanReport) -> str:
    if not report.duplicate_exposures:
        return '<p class="empty">No sensitive value was repeated across multiple files.</p>'
    return "".join(
        (
            '<article class="duplicate-card">'
            f"<header><strong>{_escape(group.group_id)}</strong>"
            f"<span>{_escape(CATEGORY_LABEL[group.category])} · {group.count} matches</span></header>"
            f"<code>{_escape(group.masked_fragment)}</code>"
            f"<p>{_escape(' → '.join(group.paths))}</p></article>"
        )
        for group in report.duplicate_exposures
    )


def _recommendation_cards(report: ScanReport) -> str:
    if not report.recommendations:
        return '<p class="empty">No category-specific cleanup action was generated.</p>'
    return "".join(
        (
            f'<article class="recommendation {item.priority.value}">'
            f"<span>{_escape(SEVERITY_LABEL[item.priority])} priority · "
            f"{item.affected_files} file(s)</span>"
            f"<h3>{_escape(item.title)}</h3><p>{_escape(item.action)}</p></article>"
        )
        for item in report.recommendations
    )


def render_html_report(report: ScanReport) -> str:
    """Render a standalone report with no remote assets or runtime dependencies."""

    generated = report.generated_at.isoformat()
    warnings = "".join(f"<li>{_escape(warning)}</li>" for warning in report.warnings)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
  <title>Data XRay Local — {_escape(report.source_label)}</title>
  <style>
    :root {{
      color-scheme: dark;
      --ink: #e9f7f2; --muted: #8fa9a0; --panel: #101b1b; --line: #28403b;
      --bg: #071010; --green: #8fffc1; --cyan: #6de5e3; --amber: #ffd166;
      --red: #ff6b6b; --violet: #c6a8ff;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; background: radial-gradient(circle at 18% 0%, #15352f 0, var(--bg) 34rem);
      color: var(--ink); font: 15px/1.55 Inter, ui-sans-serif, system-ui, sans-serif; }}
    a {{ color: var(--cyan); }}
    code {{ color: var(--green); font: 0.9em ui-monospace, SFMono-Regular, Consolas, monospace;
      overflow-wrap: anywhere; }}
    .skip {{ position: fixed; left: 1rem; top: -5rem; z-index: 10; background: white; color: black;
      padding: .7rem 1rem; border-radius: .4rem; }}
    .skip:focus {{ top: 1rem; }}
    header.hero {{ padding: 4.5rem clamp(1.25rem, 5vw, 5rem) 3rem; border-bottom: 1px solid var(--line); }}
    .eyebrow {{ color: var(--green); letter-spacing: .18em; text-transform: uppercase; font-weight: 800; }}
    h1 {{ margin: .4rem 0; font-size: clamp(2.5rem, 8vw, 6.5rem); letter-spacing: -.065em;
      line-height: .93; max-width: 12ch; }}
    .lede {{ color: var(--muted); max-width: 65ch; font-size: 1.05rem; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px;
      background: var(--line); border: 1px solid var(--line); margin-top: 2.5rem; }}
    .metric {{ background: var(--panel); padding: 1.2rem; }}
    .metric span {{ color: var(--muted); display: block; }}
    .metric strong {{ display: block; font-size: 2.1rem; margin-top: .2rem; }}
    main {{ width: min(1180px, calc(100% - 2rem)); margin: 0 auto; padding: 2.5rem 0 5rem; }}
    section {{ margin: 4rem 0; }}
    h2 {{ font-size: clamp(1.7rem, 4vw, 2.7rem); letter-spacing: -.04em; margin-bottom: .5rem; }}
    .section-intro {{ color: var(--muted); margin-top: 0; max-width: 72ch; }}
    .heat-row {{ display: grid; grid-template-columns: minmax(220px, 1.8fr) minmax(140px, 2fr) 3ch;
      gap: 1rem; align-items: center; border-top: 1px solid var(--line); padding: .85rem 0; }}
    .heat-copy span {{ display: block; color: var(--muted); font-size: .85rem; }}
    .heat-track {{ background: #1b2927; height: .75rem; overflow: hidden; }}
    .heat-fill {{ display: block; height: 100%; }}
    .low {{ --accent: var(--cyan); }} .medium {{ --accent: var(--amber); }}
    .high {{ --accent: #ff9f43; }} .critical {{ --accent: var(--red); }}
    .heat-fill, .badge {{ background: var(--accent); }}
    .badge {{ color: #071010; display: inline-block; padding: .12rem .45rem; font-weight: 800;
      text-transform: uppercase; font-size: .72rem; letter-spacing: .05em; }}
    .filters {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: 1.4rem 0; }}
    button {{ appearance: none; border: 1px solid var(--line); background: var(--panel); color: var(--ink);
      padding: .55rem .8rem; cursor: pointer; font: inherit; }}
    button[aria-pressed="true"], button:hover {{ border-color: var(--green); color: var(--green); }}
    button:focus-visible, input:focus-visible, a:focus-visible {{ outline: 3px solid var(--cyan);
      outline-offset: 3px; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); }}
    table {{ width: 100%; border-collapse: collapse; min-width: 860px; }}
    th, td {{ padding: .8rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }}
    .duplicate-card, .recommendation {{ border: 1px solid var(--line); background: color-mix(in srgb, var(--panel), transparent 8%);
      padding: 1.15rem; }}
    .duplicate-card header {{ display: flex; justify-content: space-between; gap: 1rem; color: var(--muted); }}
    .duplicate-card p, .recommendation p {{ color: var(--muted); margin-bottom: 0; }}
    .recommendation {{ border-left: .35rem solid var(--accent); }}
    .recommendation span {{ color: var(--accent); text-transform: uppercase; font-size: .74rem;
      font-weight: 800; letter-spacing: .07em; }}
    .recommendation h3 {{ margin: .25rem 0; }}
    .warning {{ border: 1px solid #745c28; background: #241f13; padding: 1rem 1.3rem; }}
    .empty {{ color: var(--muted); border: 1px dashed var(--line); padding: 1rem; }}
    footer {{ color: var(--muted); border-top: 1px solid var(--line); padding: 2rem clamp(1rem, 5vw, 5rem); }}
    [hidden] {{ display: none !important; }}
    @media (max-width: 760px) {{
      .metrics, .grid {{ grid-template-columns: 1fr 1fr; }}
      .heat-row {{ grid-template-columns: 1fr 3ch; }}
      .heat-track {{ grid-column: 1 / -1; grid-row: 2; }}
    }}
    @media (max-width: 480px) {{ .metrics, .grid {{ grid-template-columns: 1fr; }} }}
    @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
    @media print {{ body {{ background: white; color: black; }} .filters {{ display: none; }}
      .metric, .duplicate-card, .recommendation {{ background: white; }} code {{ color: #075d43; }} }}
  </style>
</head>
<body>
  <a class="skip" href="#main">Skip to report</a>
  <header class="hero">
    <span class="eyebrow">Local privacy exposure map</span>
    <h1>See what the folder remembers.</h1>
    <p class="lede">Source <code>{_escape(report.source_label)}</code> · generated {_escape(generated)} ·
      outbound network {"blocked" if report.network_disabled else "guard not requested"}.
      Every displayed match is masked.</p>
    <div class="metrics" aria-label="Scan summary">{_summary_cards(report)}</div>
  </header>
  <main id="main">
    <aside class="warning" aria-label="Important scan warnings"><strong>Review boundary</strong>
      <ul>{warnings}</ul></aside>
    <section aria-labelledby="heatmap-title">
      <h2 id="heatmap-title">Risk heatmap</h2>
      <p class="section-intro">Files are ranked by severity, volume, and variety of detected exposure.</p>
      {_heatmap_rows(report)}
    </section>
    <section aria-labelledby="findings-title">
      <h2 id="findings-title">Masked findings</h2>
      <p class="section-intro">Locations are precise enough to fix the source. Values are never retained in full.</p>
      <div class="filters" role="group" aria-label="Filter findings by severity">
        <button type="button" data-filter="all" aria-pressed="true">All</button>
        <button type="button" data-filter="critical" aria-pressed="false">Critical</button>
        <button type="button" data-filter="high" aria-pressed="false">High</button>
        <button type="button" data-filter="medium" aria-pressed="false">Medium</button>
        <button type="button" data-filter="low" aria-pressed="false">Low</button>
      </div>
      <div class="table-wrap"><table>
        <thead><tr><th>File</th><th>Location</th><th>Category</th><th>Risk</th>
          <th>Masked fragment</th><th>Repeat group</th></tr></thead>
        <tbody id="finding-rows">{_finding_rows(report)}</tbody>
      </table></div>
    </section>
    <section aria-labelledby="duplicates-title">
      <h2 id="duplicates-title">Repeated exposure chains</h2>
      <p class="section-intro">The same sensitive value appearing in separate files creates extra cleanup paths.</p>
      <div class="grid">{_duplicate_cards(report)}</div>
    </section>
    <section aria-labelledby="actions-title">
      <h2 id="actions-title">Cleanup sequence</h2>
      <p class="section-intro">Actions are ordered by likely harm and number of affected files.</p>
      <div class="grid">{_recommendation_cards(report)}</div>
    </section>
  </main>
  <footer>Data XRay Local v{_escape(report.product_version)} · local heuristic review aid · MIT</footer>
  <script>
    const controls = document.querySelectorAll('[data-filter]');
    const rows = document.querySelectorAll('#finding-rows tr[data-severity]');
    controls.forEach((control) => control.addEventListener('click', () => {{
      const selected = control.dataset.filter;
      controls.forEach((item) => item.setAttribute('aria-pressed', String(item === control)));
      rows.forEach((row) => {{ row.hidden = selected !== 'all' && row.dataset.severity !== selected; }});
    }}));
  </script>
</body>
</html>
"""


def write_html_report(report: ScanReport, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_html_report(report), encoding="utf-8")
    return destination


def write_report_bundle(report: ScanReport, output_directory: Path) -> tuple[Path, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = write_json_report(report, output_directory / "data-xray-report.json")
    html_path = write_html_report(report, output_directory / "data-xray-report.html")
    return json_path, html_path
