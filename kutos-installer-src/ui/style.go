package ui

// AppCSS uygulamanın GTK3 CSS temasını içerir.
// Koyu KutOS renk paleti: zemin #09090b, vurgu #3b82f6
const AppCSS = `
* {
    font-family: "Inter", "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 14px;
}

window {
    background-color: #09090b;
    color: #fafafa;
}

/* ── Sidebar ─────────────────────────────────── */
.sidebar {
    background-color: #0f0f12;
    border-right: 1px solid #1e1e24;
    min-width: 220px;
    padding: 0;
}

.sidebar-logo {
    padding: 24px 24px 20px 24px;
    border-bottom: 1px solid #1e1e24;
    margin-bottom: 12px;
}

.logo-text {
    font-size: 22px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.5px;
}

.logo-accent {
    font-size: 22px;
    font-weight: 700;
    color: #3b82f6;
    letter-spacing: -0.5px;
}

.step-row {
    padding: 9px 20px;
    color: #52525b;
    font-size: 13px;
    border-left: 3px solid transparent;
    transition: all 150ms ease;
}

.step-row.active {
    color: #fafafa;
    background-color: rgba(59,130,246,0.08);
    border-left-color: #3b82f6;
}

.step-row.done {
    color: #4ade80;
    border-left-color: transparent;
}

.step-num {
    font-size: 11px;
    font-weight: 700;
    color: #52525b;
    background-color: #27272a;
    border-radius: 10px;
    padding: 2px 7px;
    margin-right: 10px;
}

.step-num.active-num {
    background-color: #3b82f6;
    color: #ffffff;
}

.step-num.done-num {
    background-color: #14532d;
    color: #4ade80;
}

/* ── İçerik alanı ────────────────────────────── */
.content-area {
    background-color: #09090b;
    padding: 52px 56px 32px 56px;
}

.page-title {
    font-size: 26px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}

.page-subtitle {
    font-size: 14px;
    color: #71717a;
    margin-bottom: 28px;
    line-height: 1.5;
}

/* ── Form elemanları ─────────────────────────── */
entry {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    color: #fafafa;
    padding: 9px 13px;
    min-height: 38px;
    caret-color: #3b82f6;
}

entry:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

.field-label {
    font-size: 12px;
    font-weight: 600;
    color: #a1a1aa;
    margin-bottom: 5px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}

/* ── Butonlar ────────────────────────────────── */
.btn-primary {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-weight: 600;
    font-size: 14px;
    min-height: 38px;
    transition: background-color 150ms ease;
}

.btn-primary:hover {
    background-color: #2563eb;
}

.btn-primary:disabled {
    background-color: #1e3a5f;
    color: #4b7aa8;
}

.btn-secondary {
    background-color: transparent;
    color: #a1a1aa;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 14px;
    min-height: 38px;
}

.btn-secondary:hover {
    background-color: #18181b;
    color: #fafafa;
    border-color: #3f3f46;
}

.btn-secondary:disabled {
    color: #3f3f46;
    border-color: #1e1e24;
}

/* ── Footer ──────────────────────────────────── */
.footer {
    background-color: #0c0c0f;
    border-top: 1px solid #1e1e24;
    padding: 14px 48px;
}

/* ── Liste (disk, timezone, keyboard) ────────── */
listbox {
    background-color: transparent;
    border: none;
}

listbox row {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    margin: 3px 0;
    padding: 11px 15px;
    color: #fafafa;
    transition: background-color 100ms ease;
}

listbox row:selected {
    background-color: rgba(59,130,246,0.12);
    border-color: #3b82f6;
}

listbox row:hover:not(:selected) {
    background-color: #1e1e28;
    border-color: #3f3f46;
}

/* ── Progress ────────────────────────────────── */
.log-view {
    background-color: #030305;
    border: 1px solid #1a1a20;
    border-radius: 8px;
    color: #4ade80;
    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", monospace;
    font-size: 12px;
    padding: 14px;
    line-height: 1.6;
}

progressbar {
    min-height: 6px;
}

progressbar trough {
    background-color: #18181b;
    border-radius: 3px;
    min-height: 6px;
}

progressbar progress {
    background-color: #3b82f6;
    border-radius: 3px;
    min-height: 6px;
}

/* ── Disk kartları ───────────────────────────── */
.disk-name {
    font-size: 14px;
    font-weight: 600;
    color: #fafafa;
}

.disk-meta {
    font-size: 12px;
    color: #71717a;
    margin-top: 1px;
}

/* ── Uyarı kutusu ────────────────────────────── */
.warning-box {
    background-color: #1c0a04;
    border: 1px solid #7c2d12;
    border-radius: 8px;
    padding: 11px 15px;
    color: #fb923c;
    font-size: 13px;
}

/* ── Özet satırları ──────────────────────────── */
.summary-key {
    font-size: 13px;
    font-weight: 600;
    color: #71717a;
    min-width: 170px;
}

.summary-val {
    font-size: 13px;
    color: #fafafa;
}

/* ── Checkbutton ─────────────────────────────── */
checkbutton {
    color: #d4d4d8;
    font-size: 13px;
}

checkbutton check {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 4px;
}

checkbutton:checked check {
    background-color: #3b82f6;
    border-color: #3b82f6;
}

/* ── ComboBox ────────────────────────────────── */
combobox button {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    color: #fafafa;
    padding: 8px 13px;
    min-height: 38px;
}

/* ── Arama kutusu ────────────────────────────── */
searchentry {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    color: #fafafa;
    padding: 8px 13px;
    min-height: 38px;
    margin-bottom: 10px;
}

searchentry:focus {
    border-color: #3b82f6;
}

/* ── Finish sayfası ikonu ────────────────────── */
.finish-icon {
    font-size: 64px;
    color: #4ade80;
    margin-bottom: 8px;
}

.finish-title {
    font-size: 28px;
    font-weight: 700;
    color: #fafafa;
}

.finish-sub {
    font-size: 15px;
    color: #71717a;
    line-height: 1.6;
}

/* ── Welcome bullet'ları ─────────────────────── */
.info-icon {
    font-size: 18px;
    margin-right: 12px;
}

.info-text {
    font-size: 14px;
    color: #d4d4d8;
}
`
