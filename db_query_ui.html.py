<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>L5 AST Engine (Raw DB Mode)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: { extend: { fontFamily: { sans: ['Inter', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] }, colors: { gray: { 950: '#050505', 900: '#0a0a0a', 800: '#141414', 700: '#262626' }, blue: { 500: '#0066cc' } } } }
        }
    </script>
    <style>
        body { background-color: #050505; color: #e5e5e5; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #404040; border-radius: 2px; }
        input, select, textarea { background: #0a0a0a; border: 1px solid #262626; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; width: 100%; outline: none; transition: border-color 0.2s;}
        input:focus, select:focus, textarea:focus { border-color: #0066cc; box-shadow: 0 0 0 1px #0066cc; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; }
        th { background: #0a0a0a; position: sticky; top: 0; z-index: 10; font-size: 0.7rem; color: #a3a3a3; padding: 8px 12px; text-align: left; border-bottom: 1px solid #262626; text-transform: uppercase; letter-spacing: 0.05em; }
        td { padding: 8px 12px; border-bottom: 1px solid #141414; font-size: 0.75rem; white-space: nowrap; font-variant-numeric: tabular-nums; }
        tr:hover td { background: #0a0a0a; }
        .section-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; color: #737373; font-weight: 700; display: flex; align-items: center; gap: 4px; margin-bottom: 6px;}
        .loader { border: 2px solid #262626; border-top-color: #0066cc; border-radius: 50%; width: 12px; height: 12px; animation: spin 0.8s linear infinite; display: inline-block; }
        @keyframes spin { to { transform: rotate(360deg); } }
        ::-webkit-calendar-picker-indicator { filter: invert(1); cursor: pointer; }
        .tab-btn { padding: 8px 16px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #666; border-bottom: 2px solid transparent; transition: all 0.2s; }
        .tab-btn.active { color: #fff; border-bottom-color: #0066cc; }

        /* Collapsible styling */
        details > summary { list-style: none; }
        details > summary::-webkit-details-marker { display: none; }

        /* Command Palette */
        #cmd-palette { backdrop-filter: blur(4px); }
    </style>
</head>
<body class="h-screen w-screen overflow-hidden flex flex-col">
    <!-- COMMAND PALETTE (Ctrl+K) -->
    <div id="cmd-palette" class="fixed inset-0 z-[100] hidden flex items-start justify-center pt-[15vh] bg-black/50">
        <div class="bg-gray-950 border border-gray-800 rounded-lg shadow-2xl w-[500px] overflow-hidden">
            <div class="flex items-center px-4 py-3 border-b border-gray-800">
                <i data-lucide="search" class="w-4 h-4 text-gray-500 mr-3"></i>
                <input type="text" id="cmd-input" placeholder="Search tables or columns (Ctrl+K)..." class="w-full bg-transparent border-none text-sm p-0 focus:ring-0 focus:shadow-none placeholder-gray-600">
                <button id="cmd-close" class="text-gray-500 hover:text-white"><i data-lucide="x" class="w-4 h-4"></i></button>
            </div>
            <div id="cmd-results" class="max-h-[300px] overflow-y-auto custom-scrollbar p-2"></div>
        </div>
    </div>

    <header class="h-12 border-b border-gray-800 bg-gray-900 flex items-center justify-between px-4 z-20 shadow-md">
        <div class="flex items-center gap-3">
            <i data-lucide="cpu" class="w-4 h-4 text-blue-500"></i>
            <div class="border-l border-gray-800 pl-3 flex items-center gap-2">
                <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)] animate-pulse"></div>
                <h1 class="text-xs font-semibold tracking-widest uppercase text-gray-300">Raw DB Engine</h1>
            </div>
        </div>
        <div class="flex items-center gap-4 text-[10px] text-gray-500 font-mono">
            <span class="flex items-center gap-1"><i data-lucide="command" class="w-3 h-3"></i> Cmd Palette: Ctrl+K</span>
            <span class="flex items-center gap-1"><i data-lucide="arrow-left-right" class="w-3 h-3"></i> Tabs: ←/→</span>
            <span class="flex items-center gap-1 text-blue-400 ml-4"><i data-lucide="zap" class="w-3 h-3"></i> Exec: Ctrl+Enter</span>
        </div>
    </header>

    <div class="flex flex-1 overflow-hidden relative">
        <!-- BUILDER SIDEBAR -->
        <aside class="w-[440px] bg-gray-950 border-r border-gray-800 flex flex-col h-full z-10 shadow-xl">
            <div class="flex border-b border-gray-800 bg-gray-900 px-2 pt-2 gap-2">
                <button data-action="set-sidebar-tab" data-tab="basic" class="tab-btn active" id="tab-basic">BASIC</button>
                <button data-action="set-sidebar-tab" data-tab="advanced" class="tab-btn" id="tab-advanced">ADVANCED</button>
                <button data-action="set-sidebar-tab" data-tab="raw" class="tab-btn" id="tab-raw">RAW SQL</button>
            </div>
            <div class="p-3 border-b border-gray-800 bg-gray-900/50 flex justify-between items-center">
                <span class="text-[9px] text-gray-500 font-mono uppercase tracking-widest" id="current-tab-desc">SELECT • FROM • WHERE • GROUP BY</span>
                <div class="flex gap-2">
                    <button id="btn-explain" class="bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 px-3 py-1.5 rounded text-[10px] font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50">
                        <i data-lucide="activity" class="w-3 h-3"></i> PLAN
                    </button>
                    <button id="btn-execute" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-[11px] font-medium flex items-center gap-2 transition-colors disabled:opacity-50 shadow-lg shadow-blue-900/20">
                        <i data-lucide="play" class="w-3 h-3"></i> EXECUTE
                    </button>
                </div>
            </div>
            <div id="builder-ui" class="p-4 overflow-y-auto custom-scrollbar flex-1 space-y-4">
                <!-- UI injected here -->
            </div>

            <!-- LIVE COMPILED SQL PREVIEW TERMINAL (SIDEBAR) -->
            <div class="h-32 border-t border-gray-800 bg-[#0a0a0a] flex flex-col shadow-[0_-10px_20px_-5px_rgba(0,0,0,0.5)] z-20">
                <div class="px-3 py-1.5 border-b border-gray-800 bg-gray-900 flex justify-between items-center">
                    <span class="text-[9px] text-blue-400 font-mono uppercase tracking-widest flex items-center gap-1.5">
                        <i data-lucide="terminal" class="w-3 h-3"></i> Query Compiler
                    </span>
                    <button onclick="navigator.clipboard.writeText(document.getElementById('live-sql-preview').innerText)" class="text-gray-500 hover:text-white transition-colors" title="Copy SQL">
                        <i data-lucide="copy" class="w-3 h-3"></i>
                    </button>
                </div>
                <div class="flex-1 overflow-auto custom-scrollbar p-3">
                    <code id="live-sql-preview" class="text-[9px] font-mono text-gray-300 leading-relaxed whitespace-pre-wrap break-all block"></code>
                </div>
            </div>
        </aside>

        <!-- MAIN RESULTS -->
        <main class="flex-1 flex flex-col h-full bg-[#050505] relative">
            <div class="h-12 border-b border-gray-800 bg-gray-900 flex items-center justify-between px-4 z-10">
                <div class="flex gap-4 h-full pt-2">
                    <button data-action="set-main-tab" data-tab="data" class="tab-btn active" id="main-tab-data">DATA GRID</button>
                    <button data-action="set-main-tab" data-tab="analytics" class="tab-btn" id="main-tab-analytics">ANALYTICS</button>
                    <button data-action="set-main-tab" data-tab="telemetry" class="tab-btn" id="main-tab-telemetry">TELEMETRY & LOGS</button>
                </div>
                <div class="flex gap-6 text-[10px] text-gray-400 font-mono uppercase tracking-wider items-center">
                    <div class="flex items-center gap-2"><i data-lucide="rows" class="w-3 h-3 text-gray-500"></i> Rows: <span id="m-rows" class="text-white">0</span></div>
                    <div class="flex items-center gap-2"><i data-lucide="columns" class="w-3 h-3 text-gray-500"></i> Cols: <span id="m-cols" class="text-white">0</span></div>
                    <div class="flex items-center gap-2"><i data-lucide="clock" class="w-3 h-3 text-gray-500"></i> Exec: <span id="m-time" class="text-white">0.00ms</span></div>
                    <div class="w-px h-4 bg-gray-700 mx-1"></div>
                    <button id="btn-export" class="text-[10px] text-gray-400 hover:text-white flex items-center gap-1 transition-colors hidden">
                        <i data-lucide="download" class="w-3 h-3"></i> CSV
                    </button>
                </div>
            </div>

            <div id="view-data" class="flex-1 flex flex-col overflow-hidden relative">
                <!-- SYSTEM GENERATED SQL DIRECTLY ON DASHBOARD -->
                <div class="bg-[#0a0a0a] border-b border-gray-800 p-4 shrink-0 shadow-sm relative group">
                    <span class="text-[9px] text-blue-500 font-mono uppercase tracking-widest absolute top-3 right-4 flex items-center gap-1.5 opacity-50 group-hover:opacity-100 transition-opacity"><i data-lucide="code-2" class="w-3 h-3"></i> System Generated SQL</span>
                    <code id="main-sql-preview" class="text-[10px] font-mono text-gray-300 leading-relaxed whitespace-pre-wrap break-all block h-16 overflow-y-auto custom-scrollbar">-- Execute query to view generated AST payload</code>
                </div>

                <div class="flex-1 overflow-auto custom-scrollbar relative">
                    <div id="grid-empty" class="absolute inset-0 flex items-center justify-center flex-col text-gray-700 gap-3">
                        <i data-lucide="cpu" class="w-10 h-10 opacity-20"></i>
                        <p class="text-xs uppercase tracking-widest font-semibold text-gray-600">Execute Query to View Data</p>
                    </div>
                    <table id="grid-table" class="hidden">
                        <thead id="grid-head"></thead>
                        <tbody id="grid-body"></tbody>
                    </table>
                </div>
            </div>

            <div id="view-analytics" class="flex-1 overflow-auto custom-scrollbar relative hidden p-6">
                <div id="analytics-content"></div>
            </div>

            <div id="view-telemetry" class="flex-1 overflow-auto custom-scrollbar relative hidden p-6 bg-[#0a0a0a]">
                <div id="telemetry-content" class="font-mono text-[11px] text-gray-300 space-y-4">
                    <div class="text-center mt-20 text-gray-600"><i data-lucide="activity" class="w-10 h-10 mx-auto mb-3 opacity-20"></i><p>Run EXPLAIN PLAN to view telemetry and audit logs.</p></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // --- STATE MANAGEMENT ---
        const state = {
            sidebarTab: 'basic', mainTab: 'data',
            tables: [], columns: [], dateCols: [], numCols: [], joinSchemas: {},
            payload: {
                ctes: [], from: '', select: [], joins: [], where: [],
                group_by: [], group_mod: '', having: [], qualify: '', order_by: [],
                limit: null, offset: null, distinct: false, sample: '', set_op: { type: 'NONE', table: '' },
                raw_sql: ''
            },
            results: [], resultCols: [], stats: [], telemetry: {}
        };

        const AGGS = ['NONE', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT', 'COUNT DISTINCT'];
        const OPS = ['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN', 'NOT IN', 'IS NULL', 'IS NOT NULL'];
        const JOINS = ['LEFT JOIN', 'INNER JOIN', 'RIGHT JOIN', 'FULL OUTER JOIN', 'CROSS JOIN', 'LATERAL'];

        // --- API ---
        async function apiGet(path) { const r = await fetch(`/api${path}`); if (!r.ok) throw new Error("API Error"); return r.json(); }

        async function init() {
            try {
                state.tables = (await apiGet('/metadata/tables')).tables || [];
                if (state.tables.length > 0) await loadTable(state.tables[0]);
            } catch (e) {
                document.getElementById('builder-ui').innerHTML = `<div class="text-xs text-red-500 font-mono bg-red-950/20 p-3 rounded">CRITICAL ERROR: Backend Unreachable</div>`;
            }
        }

        async function loadTable(table) {
            state.payload.from = table;
            const data = await apiGet(`/metadata/schema/${table}`);
            state.columns = (data.schema || []).map(s => s.column_name);
            state.dateCols = (data.schema || []).filter(s => ['DATE', 'TIMESTAMP'].some(t => String(s.column_type).toUpperCase().includes(t))).map(s => s.column_name);
            state.numCols = (data.schema || []).filter(s => ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'REAL'].some(t => String(s.column_type).toUpperCase().includes(t))).map(s => s.column_name);

            state.payload.select = [];
            state.payload.joins = []; state.payload.where = []; state.payload.group_by = []; state.payload.order_by = [];
            render();
        }

        async function fetchJoinSchema(table) {
            if(state.joinSchemas[table]) return;
            const data = await apiGet(`/metadata/schema/${table}`);
            state.joinSchemas[table] = (data.schema || []).map(s => s.column_name);
            render();
        }

        // --- BIDIRECTIONAL AST ROUND-TRIPPING ---
        let parseTimeout;
        async function parseRawSqlToAST() {
            if(!state.payload.raw_sql || !state.payload.raw_sql.trim()) return;
            try {
                const res = await fetch('/api/query/parse', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({sql: state.payload.raw_sql, is_explain: false})});
                const data = await res.json();
                if(data && data.status === 'success' && data.ui_state) {
                    const ui = data.ui_state;
                    if(ui.from) state.payload.from = ui.from;
                    state.payload.select = ui.select || [];
                    state.payload.where = ui.where || [];
                    state.payload.group_by = ui.group_by || [];
                    state.payload.order_by = ui.order_by || [];
                    state.payload.limit = ui.limit;
                    state.payload.distinct = ui.distinct;
                    render();
                }
            } catch(e) { console.error("AST Parse failed", e); }
        }

        function escapeHTML(str) { return String(str || '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m])); }

        function render() {
            let html = '';
            const p = state.payload;
            if (!p) return;

            if (state.sidebarTab === 'raw') {
                html += `<div class="pt-2">
                    <div class="flex justify-between items-center mb-2">
                        <span class="section-label text-blue-400">RAW SQL (AST PARSED)</span>
                    </div>
                    <p class="text-[9px] text-gray-500 mb-2 leading-relaxed">Write standard SQL. The engine will parse it into a sqlglot AST, validate security policies, and synchronize with the visual builder.</p>
                    <textarea data-action="update-raw-sql" class="w-full h-64 bg-gray-950 border border-gray-800 text-blue-300 font-mono text-[10px] p-2 custom-scrollbar" placeholder="SELECT * FROM ...">${escapeHTML(p.raw_sql || buildSQLString())}</textarea>
                </div>`;
            } else if (state.sidebarTab === 'basic') {

                // FROM
                html += `<div class="flex gap-2">
                    <div class="w-2/3"><span class="section-label text-blue-400">FROM</span>
                        <select data-action="set-from" class="bg-gray-900 border-gray-700 font-medium">
                            ${(state.tables || []).map(t => `<option ${t === p.from ? 'selected' : ''}>${t}</option>`).join('')}
                        </select>
                    </div>
                    <div class="w-1/3"><span class="section-label text-blue-400">SAMPLE %</span>
                        <input type="number" data-action="set-sample" placeholder="e.g. 10" value="${p.sample || ''}" class="bg-gray-900 border border-gray-800 rounded text-[10px] px-2 py-1.5 text-white">
                    </div>
                </div>`;

                // SELECT
                html += `<div class="pt-3">
                    <div class="flex justify-between items-center mb-1">
                        <span class="section-label text-blue-400">SELECT</span>
                        <button data-action="add-select" class="text-[9px] bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded text-gray-300">+ SELECT</button>
                    </div>
                    <div class="space-y-1.5">
                        ${(!p.select || p.select.length === 0) ? `<div class="text-[9px] text-gray-600 italic p-2 border border-gray-800 border-dashed rounded text-center">SELECT *</div>` : ''}
                        ${(p.select || []).map((s, i) => `
                            <div class="flex gap-1 items-center bg-gray-900 border border-gray-800 p-1 rounded relative pr-6">
                                <button data-action="rm-select" data-idx="${i}" class="absolute right-1.5 text-gray-600 hover:text-red-400"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
                                ${s.is_expr ?
                                    `<input type="text" data-action="update-select" data-idx="${i}" data-field="col" placeholder="Expression" value="${escapeHTML(s.col)}" class="w-[45%] text-[9px] border-none bg-gray-950 py-1 font-mono text-blue-200">` :
                                    `<select data-action="update-select" data-idx="${i}" data-field="col" class="w-[45%] text-[9px] border-none bg-gray-950 py-1 text-blue-200"><option value="*">*</option>${(state.columns || []).map(c => `<option value="${c}" ${s.col === c ? 'selected' : ''}>${c}</option>`).join('')}</select>`
                                }
                                <select data-action="update-select" data-idx="${i}" data-field="agg" class="w-[25%] text-[9px] border-none bg-gray-950 py-1">${AGGS.map(a => `<option ${s.agg === a ? 'selected' : ''}>${a}</option>`).join('')}</select>
                                <input type="text" data-action="update-select" data-idx="${i}" data-field="alias" placeholder="AS" value="${escapeHTML(s.alias)}" class="w-[30%] text-[9px] border-none bg-gray-950 py-1 px-2">
                            </div>
                            <div class="text-right"><button data-action="toggle-expr" data-idx="${i}" class="text-[8px] text-gray-500 hover:text-blue-400">Toggle AST Expr</button></div>
                        `).join('')}
                    </div>
                </div>`;

                // WHERE
                html += `<div class="pt-3">
                    <div class="flex justify-between items-center mb-1">
                        <span class="section-label text-blue-400">WHERE</span>
                        <button data-action="add-where" class="text-[9px] bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded text-gray-300">+ WHERE</button>
                    </div>
                    <div class="space-y-1.5">
                        ${(p.where || []).map((w, i) => {
                            const isDate = (state.dateCols || []).includes(w.col);
                            const hideVal = ['IS NULL', 'IS NOT NULL'].includes(w.op);
                            return `
                            <div class="flex items-center gap-1 bg-gray-900 border border-gray-800 p-1.5 rounded relative pr-5">
                                <button data-action="rm-where" data-idx="${i}" class="absolute right-1 text-gray-600 hover:text-red-400"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
                                ${i > 0 ? `<select data-action="update-where" data-idx="${i}" data-field="logic" class="w-12 text-[8px] text-gray-400 bg-gray-950"><option ${w.logic==='AND'?'selected':''}>AND</option><option ${w.logic==='OR'?'selected':''}>OR</option></select>` : ''}
                                <select data-action="update-where" data-idx="${i}" data-field="col" class="flex-1 text-[10px] bg-gray-950">${(state.columns || []).map(c => `<option ${w.col === c ? 'selected' : ''}>${c}</option>`).join('')}</select>
                                <select data-action="update-where" data-idx="${i}" data-field="op" class="w-[60px] text-[9px] bg-gray-950">${OPS.map(o => `<option ${w.op === o ? 'selected' : ''}>${o}</option>`).join('')}</select>
                                ${hideVal ? `<div class="flex-1"></div>` : (isDate ?
                                    `<input type="date" data-action="update-where" data-idx="${i}" data-field="val" value="${escapeHTML(w.val)}" class="flex-1 text-[10px] bg-blue-900/20 text-blue-200 border-blue-900/50 [color-scheme:dark]">` :
                                    `<input type="text" data-action="update-where" data-idx="${i}" data-field="val" placeholder="Val" value="${escapeHTML(w.val)}" class="flex-1 text-[10px] bg-gray-950 px-2">`
                                )}
                            </div>
                        `}).join('')}
                    </div>
                </div>`;

                // GROUP BY
                html += `<details class="pt-3 group"><summary class="flex justify-between items-center cursor-pointer outline-none"><span class="section-label text-blue-400 m-0 hover:text-blue-300">GROUP BY <i data-lucide="chevron-down" class="w-3 h-3 inline transition-transform group-open:rotate-180"></i></span></summary>
                    <div class="mt-2 space-y-2 border-l border-gray-800 pl-2">
                        <div class="flex gap-2">
                            <select data-action="set-group-mod" class="text-[9px] bg-gray-900 border border-gray-800 rounded px-2"><option value="" ${p.group_mod===''?'selected':''}>Standard</option><option value="ROLLUP" ${p.group_mod==='ROLLUP'?'selected':''}>ROLLUP</option><option value="CUBE" ${p.group_mod==='CUBE'?'selected':''}>CUBE</option></select>
                            <button data-action="add-group" class="text-[9px] bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded text-gray-300">+ GROUP BY</button>
                        </div>
                        <div class="space-y-1.5">
                            ${(p.group_by || []).map((g, i) => `
                                <div class="flex gap-1 items-center bg-gray-900 p-1 rounded relative">
                                    <select data-action="update-group" data-idx="${i}" data-field="col" class="w-full text-[9px] bg-gray-950 border-none py-1"><option value="">Col...</option>${(state.columns || []).map(c => `<option ${g.col === c ? 'selected' : ''}>${c}</option>`).join('')}</select>
                                    <button data-action="rm-group" data-idx="${i}" class="text-gray-600 hover:text-red-400 absolute right-2"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </details>`;

                // ORDER BY, LIMIT, OFFSET
                html += `<details class="pt-3 group" open><summary class="flex justify-between items-center cursor-pointer outline-none"><span class="section-label text-blue-400 m-0 hover:text-blue-300">ORDER BY / LIMIT <i data-lucide="chevron-down" class="w-3 h-3 inline transition-transform group-open:rotate-180"></i></span></summary>
                    <div class="mt-2 grid grid-cols-2 gap-4 border-l border-gray-800 pl-2">
                        <div>
                            <button data-action="add-order" class="text-[9px] bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded text-gray-300 mb-1">+ ORDER BY</button>
                            <div class="space-y-1 mb-3">
                                ${(p.order_by || []).map((o, i) => `
                                    <div class="flex gap-1 items-center bg-gray-900 p-1 rounded">
                                        <select data-action="update-order" data-idx="${i}" data-field="col" class="w-2/3 text-[9px] bg-gray-950 border-none py-1">${(state.columns || []).map(c => `<option ${o.col === c ? 'selected' : ''}>${c}</option>`).join('')}</select>
                                        <select data-action="update-order" data-idx="${i}" data-field="dir" class="w-1/3 text-[9px] bg-gray-950 border-none py-1"><option ${o.dir==='ASC'?'selected':''}>ASC</option><option ${o.dir==='DESC'?'selected':''}>DESC</option></select>
                                        <button data-action="rm-order" data-idx="${i}" class="text-gray-600 hover:text-red-400"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="flex gap-2">
                            <div class="w-1/2">
                                <span class="text-[9px] text-gray-500 mb-1 block">LIMIT</span>
                                <input type="number" data-action="set-limit" placeholder="-" value="${p.limit === null ? '' : p.limit}" class="w-full text-[10px] bg-gray-900 px-2 py-1 text-white">
                            </div>
                            <div class="w-1/2">
                                <span class="text-[9px] text-gray-500 mb-1 block">OFFSET</span>
                                <input type="number" data-action="set-offset" placeholder="-" value="${p.offset === null ? '' : p.offset}" class="w-full text-[10px] bg-gray-900 px-2 py-1 text-white">
                            </div>
                        </div>
                    </div>
                </details>`;

            } else if (state.sidebarTab === 'advanced') {
                html += `<div class="mb-4"><label class="flex items-center gap-2 text-[10px] text-blue-400 font-bold bg-blue-900/10 border border-blue-900/30 p-2 rounded cursor-pointer w-max"><input type="checkbox" data-action="toggle-distinct" ${p.distinct ? 'checked' : ''} class="w-3 h-3"> DISTINCT</label></div>`;

                // WITH (CTEs)
                html += `<details class="pt-3 group"><summary class="flex justify-between items-center cursor-pointer outline-none"><span class="section-label text-purple-400 m-0 hover:text-purple-300">WITH <i data-lucide="chevron-down" class="w-3 h-3 inline transition-transform group-open:rotate-180"></i></span></summary>
                    <div class="mt-2 space-y-1.5 border-l border-gray-800 pl-2">
                        <button data-action="add-cte" class="text-[9px] bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded text-gray-300">+ WITH</button>
                        ${(p.ctes || []).map((c, i) => `
                            <div class="bg-gray-900 border border-gray-800 p-2 rounded relative">
                                <button data-action="rm-cte" data-idx="${i}" class="absolute top-1 right-1 text-gray-600 hover:text-red-400"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
                                <input type="text" data-action="update-cte" data-idx="${i}" data-field="name" placeholder="Alias (e.g. cte1)" value="${escapeHTML(c.name)}" class="w-1/2 text-[10px] bg-gray-950 border-none mb-1 font-bold text-purple-300">
                                <input type="text" data-action="update-cte" data-idx="${i}" data-field="sql" placeholder="Subquery SQL AST" value="${escapeHTML(c.sql)}" class="w-full text-[9px] bg-gray-950 border-none mt-1 font-mono text-gray-400">
                            </div>
                        `).join('')}
                    </div>
                </details>`;

                // JOIN
                html += `<details class="pt-3 group" open><summary class="flex justify-between items-center cursor-pointer outline-none"><span class="section-label text-purple-400 m-0 hover:text-purple-300">JOIN <i data-lucide="chevron-down" class="w-3 h-3 inline transition-transform group-open:rotate-180"></i></span></summary>
                    <div class="mt-2 space-y-1.5 border-l border-gray-800 pl-2">
                        <button data-action="add-join" class="text-[9px] bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded text-gray-300">+ JOIN</button>
                        ${(p.joins || []).map((j, i) => {
                            const tCols = state.joinSchemas[j.table] || [];
                            return `
                            <div class="bg-gray-900 border border-gray-800 p-1.5 rounded space-y-1.5 relative">
                                <button data-action="rm-join" data-idx="${i}" class="absolute top-1 right-1 text-gray-600 hover:text-red-400"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
                                <div class="flex gap-1 pr-4">
                                    <select data-action="update-join" data-idx="${i}" data-field="type" class="w-[40%] text-[9px] font-bold text-purple-400 bg-gray-950 border-none">${JOINS.map(t => `<option ${j.type === t ? 'selected' : ''}>${t}</option>`).join('')}</select>
                                    <select data-action="update-join" data-idx="${i}" data-field="table" class="w-[60%] text-[9px] bg-gray-950 border-none"><option value="">Target...</option>${(state.tables || []).filter(t=>t!==p.from).map(t => `<option ${j.table === t ? 'selected' : ''}>${t}</option>`).join('')}</select>
                                </div>
                                <div class="flex items-center gap-1 bg-gray-950 p-1 rounded border border-gray-800">
                                    <span class="text-[8px] text-gray-500 mx-1">ON</span>
                                    <select data-action="update-join" data-idx="${i}" data-field="leftCol" class="w-[45%] text-[9px] bg-gray-900 border-none"><option value="">L.Col</option>${(state.columns || []).map(c => `<option ${j.leftCol === c ? 'selected' : ''}>${c}</option>`).join('')}</select>
                                    <span class="text-[10px] text-gray-500">=</span>
                                    <select data-action="update-join" data-idx="${i}" data-field="rightCol" class="w-[45%] text-[9px] bg-gray-900 border-none"><option value="">R.Col</option>${tCols.map(c => `<option ${j.rightCol === c ? 'selected' : ''}>${c}</option>`).join('')}</select>
                                </div>
                            </div>
                        `}).join('')}
                    </div>
                </details>`;

                // HAVING
                html += `<details class="pt-3 group"><summary class="flex justify-between items-center cursor-pointer outline-none"><span class="section-label text-purple-400 m-0 hover:text-purple-300">HAVING <i data-lucide="chevron-down" class="w-3 h-3 inline transition-transform group-open:rotate-180"></i></span></summary>
                    <div class="mt-2 space-y-1.5 border-l border-gray-800 pl-2">
                        <button data-action="add-having" class="text-[9px] bg-gray-800 hover:bg-gray-700 px-2 py-0.5 rounded text-gray-300">+ HAVING</button>
                        ${(p.having || []).map((h, i) => `
                            <div class="flex items-center gap-1 bg-gray-900 border border-gray-800 p-1.5 rounded relative pr-5">
                                <button data-action="rm-having" data-idx="${i}" class="absolute right-1 text-gray-600 hover:text-red-400"><i data-lucide="x" class="w-3.5 h-3.5"></i></button>
                                ${i > 0 ? `<select data-action="update-having" data-idx="${i}" data-field="logic" class="w-12 text-[8px] text-gray-400 bg-gray-950"><option ${h.logic==='AND'?'selected':''}>AND</option><option ${h.logic==='OR'?'selected':''}>OR</option></select>` : ''}
                                <select data-action="update-having" data-idx="${i}" data-field="agg" class="w-16 text-[9px] bg-gray-950">${['SUM','AVG','MIN','MAX','COUNT'].map(a => `<option ${h.agg===a?'selected':''}>${a}</option>`).join('')}</select>
                                <select data-action="update-having" data-idx="${i}" data-field="col" class="flex-1 text-[9px] bg-gray-950">${(state.columns || []).map(c => `<option ${h.col === c ? 'selected' : ''}>${c}</option>`).join('')}</select>
                                <select data-action="update-having" data-idx="${i}" data-field="op" class="w-10 text-[9px] bg-gray-950"><option ${h.op==='>'?'selected':''}>></option><option ${h.op==='<'?'selected':''}>&lt;</option><option ${h.op==='='?'selected':''}>=</option><option ${h.op==='>='?'selected':''}>&gt;=</option><option ${h.op==='<='?'selected':''}>&lt;=</option></select>
                                <input type="text" data-action="update-having" data-idx="${i}" data-field="val" placeholder="Val" value="${escapeHTML(h.val)}" class="w-16 text-[10px] bg-gray-950 px-1">
                            </div>
                        `).join('')}
                    </div>
                </details>`;

                // QUALIFY
                html += `<div class="pt-3 border-t border-gray-800/50 mt-3">
                    <span class="section-label text-purple-400 mb-2">QUALIFY</span>
                    <input type="text" data-action="update-qualify" placeholder="e.g. ROW_NUMBER() OVER(PARTITION BY x) = 1" value="${escapeHTML(p.qualify)}" class="w-full text-[10px] bg-gray-900 border border-gray-800 px-2 py-1.5 font-mono text-blue-300">
                </div>`;

                // UNION
                html += `<div class="pt-3 border-t border-gray-800/50 mt-3 grid grid-cols-2 gap-2">
                    <div>
                        <span class="section-label text-purple-400 mb-2">UNION / SET OPS</span>
                        <div class="flex flex-col gap-1 bg-gray-900 p-1.5 rounded border border-gray-800">
                            <select data-action="update-setop" data-field="type" class="w-full text-[9px] bg-gray-950 font-bold text-purple-400 mb-1">
                                ${['NONE', 'UNION', 'UNION ALL', 'INTERSECT', 'EXCEPT'].map(s => `<option ${(p.set_op && p.set_op.type===s)?'selected':''}>${s}</option>`).join('')}
                            </select>
                            <select data-action="update-setop" data-field="table" class="w-full text-[9px] bg-gray-950 ${(p.set_op && p.set_op.type==='NONE')?'opacity-30':''}">
                                <option value="">Table...</option>${(state.tables || []).filter(t=>t!==p.from).map(t => `<option ${(p.set_op && p.set_op.table===t)?'selected':''}>${t}</option>`).join('')}
                            </select>
                        </div>
                    </div>
                </div>`;
            }

            document.getElementById('builder-ui').innerHTML = html;
            lucide.createIcons();
            updateLivePreview();
        }

        // --- AST SQL STRING COMPILER (DEFENSIVE RE-WRITE) ---
        function buildSQLString() {
            const p = state.payload;
            if (!p) return "";
            if (state.sidebarTab === 'raw') return p.raw_sql || "";

            if (!p.from) return "";
            let sql = "";

            if (p.ctes && Array.isArray(p.ctes) && p.ctes.length > 0) {
                const ctes = p.ctes.filter(c => c && c.name && c.sql).map(c => `${c.name} AS (${c.sql})`).join(", ");
                if(ctes) sql += `WITH ${ctes} \n`;
            }

            sql += p.distinct ? "SELECT DISTINCT \n  " : "SELECT \n  ";

            const selects = [];
            if (p.select && Array.isArray(p.select)) {
                p.select.forEach(s => {
                    if (!s) return;
                    let expr = s.col === '*' ? '*' : `"${s.col}"`;
                    if (s.is_expr) expr = s.col;
                    if (s.agg && s.agg !== 'NONE') expr = s.agg === 'COUNT DISTINCT' ? `COUNT(DISTINCT "${s.col}")` : `${s.agg}(${expr})`;
                    if (s.alias) expr += ` AS "${s.alias}"`;
                    selects.push(expr);
                });
            }
            sql += selects.length ? selects.join(",\n  ") : "*";

            sql += `\nFROM "${p.from}"`;
            if (p.sample) sql += ` USING SAMPLE ${p.sample}% (bernoulli)`;

            if (p.joins && Array.isArray(p.joins)) {
                p.joins.forEach(j => {
                    if(j && j.table && j.leftCol && j.rightCol) sql += `\n${j.type || 'LEFT JOIN'} "${j.table}" ON "${p.from}"."${j.leftCol}" = "${j.table}"."${j.rightCol}"`;
                });
            }

            if (p.where && Array.isArray(p.where)) {
                const where = p.where.map((w, i) => {
                    if (!w || !w.col || (!w.val && w.op && !w.op.includes('NULL'))) return null;
                    let prefix = i > 0 ? `${w.logic || 'AND'} ` : "";
                    let op = w.op || '=';
                    let safeVal = isNaN(w.val) && !op.includes('IN') ? `'${String(w.val).replace(/'/g,"''")}'` : w.val;
                    if (op.includes('IN')) safeVal = `(${w.val})`;
                    return op.includes('NULL') ? `${prefix}"${w.col}" ${op}` : `${prefix}"${w.col}" ${op} ${safeVal}`;
                }).filter(Boolean).join(" ");
                if (where) sql += `\nWHERE ${where}`;
            }

            if (p.group_by && Array.isArray(p.group_by)) {
                const groups = p.group_by.map(g => g && g.col ? `"${g.col}"` : "").filter(c => c && c !== '""');
                if (groups.length) {
                    if (p.group_mod) sql += `\nGROUP BY ${p.group_mod}(${groups.join(', ')})`;
                    else sql += `\nGROUP BY ${groups.join(', ')}`;
                }
            }

            if (p.having && Array.isArray(p.having)) {
                const having = p.having.map((h, i) => {
                    if (!h || !h.col || (!h.val && h.op && !h.op.includes('NULL'))) return null;
                    let prefix = i > 0 ? `${h.logic || 'AND'} ` : "";
                    let op = h.op || '=';
                    let safeVal = isNaN(h.val) ? `'${String(h.val).replace(/'/g,"''")}'` : h.val;
                    return `${prefix}${h.agg || 'SUM'}("${h.col}") ${op} ${safeVal}`;
                }).filter(Boolean).join(" ");
                if (having) sql += `\nHAVING ${having}`;
            }

            if (p.qualify) sql += `\nQUALIFY ${p.qualify}`;

            if (p.order_by && Array.isArray(p.order_by)) {
                const orders = p.order_by.map(o => o && o.col ? `"${o.col}" ${o.dir || 'ASC'}` : "").filter(Boolean);
                if (orders.length) sql += `\nORDER BY ${orders.join(', ')}`;
            }

            if (p.limit !== null && p.limit !== undefined && p.limit !== "") sql += `\nLIMIT ${p.limit}`;
            if (p.offset !== null && p.offset !== undefined && p.offset !== "") sql += `\nOFFSET ${p.offset}`;
            if (p.set_op && p.set_op.type && p.set_op.type !== 'NONE' && p.set_op.table) sql += `\n${p.set_op.type} SELECT * FROM "${p.set_op.table}"`;

            return sql;
        }

        // --- REAL-TIME LIVE PREVIEW UPDATER ---
        function updateLivePreview() {
            try {
                const sql = buildSQLString();
                const elSidebar = document.getElementById('live-sql-preview');
                const elMain = document.getElementById('main-sql-preview');
                if (elSidebar) elSidebar.innerText = sql;
                if (elMain) elMain.innerText = sql;
            } catch(e) { console.error("Live preview engine bypassed an incomplete AST node."); }
        }

        // --- EVENT DELEGATION LOOP ---
        document.addEventListener('click', e => {
            const btn = e.target.closest('button[data-action]'); if(!btn) return;
            const action = btn.dataset.action; const idx = btn.dataset.idx;

            if (action === 'set-sidebar-tab') {
                document.querySelectorAll('.tab-btn[data-action="set-sidebar-tab"]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.sidebarTab = btn.dataset.tab;
                const descs = { 'basic': "SELECT • FROM • WHERE • GROUP BY", 'advanced': "WITH • JOIN • HAVING • QUALIFY", 'raw': "BYPASS UI (AST PARSER)" };
                document.getElementById('current-tab-desc').innerText = descs[state.sidebarTab];
                render();
            }

            if (action === 'set-main-tab') {
                document.querySelectorAll('.tab-btn[data-action="set-main-tab"]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.mainTab = btn.dataset.tab;

                document.getElementById('view-data').classList.add('hidden');
                document.getElementById('view-analytics').classList.add('hidden');
                document.getElementById('view-telemetry').classList.add('hidden');

                document.getElementById(`view-${state.mainTab}`).classList.remove('hidden');
                if(state.mainTab === 'analytics') renderAnalytics();
                if(state.mainTab === 'telemetry') fetchAuditLogs();
            }

            if (action === 'add-select') { state.payload.select.push({ col: state.columns[0]||'*', agg: 'NONE', alias: '', is_expr: false}); render(); }
            if (action === 'add-join') { state.payload.joins.push({ type: 'LEFT JOIN', table: '', leftCol: '', rightCol: '' }); render(); }
            if (action === 'add-where') { state.payload.where.push({ logic: 'AND', col: state.columns[0]||'', op: '=', val: '' }); render(); }
            if (action === 'add-group') { state.payload.group_by.push({ col: state.columns[0]||'' }); render(); }
            if (action === 'add-having') { state.payload.having.push({ logic: 'AND', agg: 'SUM', col: state.columns[0]||'', op: '>', val: '' }); render(); }
            if (action === 'add-order') { state.payload.order_by.push({ col: state.columns[0]||'', dir: 'ASC' }); render(); }
            if (action === 'add-cte') { state.payload.ctes.push({ name: '', sql: '' }); render(); }

            if (action === 'rm-select') { state.payload.select.splice(idx, 1); render(); }
            if (action === 'rm-join') { state.payload.joins.splice(idx, 1); render(); }
            if (action === 'rm-where') { state.payload.where.splice(idx, 1); render(); }
            if (action === 'rm-group') { state.payload.group_by.splice(idx, 1); render(); }
            if (action === 'rm-having') { state.payload.having.splice(idx, 1); render(); }
            if (action === 'rm-order') { state.payload.order_by.splice(idx, 1); render(); }
            if (action === 'rm-cte') { state.payload.ctes.splice(idx, 1); render(); }

            if (action === 'toggle-expr') { state.payload.select[idx].is_expr = !state.payload.select[idx].is_expr; render(); }
        });

        let typingTimer;
        document.getElementById('builder-ui').addEventListener('change', async (e) => {
            const action = e.target.dataset.action; if (!action) return;
            const idx = e.target.dataset.idx; const field = e.target.dataset.field; const val = e.target.value;

            if (action === 'set-from') await loadTable(val);
            if (action === 'update-select') state.payload.select[idx][field] = val;
            if (action === 'update-join') {
                state.payload.joins[idx][field] = val;
                if(field === 'table' && val !== '') await fetchJoinSchema(val);
            }
            if (action === 'update-where') { state.payload.where[idx][field] = val; if(field==='col') { state.payload.where[idx].val = ''; render(); return; }}
            if (action === 'update-group') state.payload.group_by[idx][field] = val;
            if (action === 'set-group-mod') state.payload.group_mod = val;
            if (action === 'update-having') state.payload.having[idx][field] = val;
            if (action === 'update-order') state.payload.order_by[idx][field] = val;
            if (action === 'toggle-distinct') state.payload.distinct = e.target.checked;
            if (action === 'update-cte') state.payload.ctes[idx][field] = val;
            if (action === 'update-setop') state.payload.set_op[field] = val;

            updateLivePreview();
        });

        document.getElementById('builder-ui').addEventListener('input', (e) => {
            const action = e.target.dataset.action; if (!action) return;
            const idx = e.target.dataset.idx; const field = e.target.dataset.field; const val = e.target.value;

            if (action === 'update-select') state.payload.select[idx][field] = val;
            if (action === 'update-join') state.payload.joins[idx][field] = val;
            if (action === 'update-where') state.payload.where[idx][field] = val;
            if (action === 'update-having') state.payload.having[idx][field] = val;
            if (action === 'update-qualify') state.payload.qualify = val;
            if (action === 'update-cte') state.payload.ctes[idx][field] = val;
            if (action === 'set-limit') state.payload.limit = val === '' ? null : parseInt(val);
            if (action === 'set-offset') state.payload.offset = val === '' ? null : parseInt(val);
            if (action === 'set-sample') state.payload.sample = val;
            if (action === 'update-raw-sql') {
                state.payload.raw_sql = val;
                clearTimeout(typingTimer);
                typingTimer = setTimeout(parseRawSqlToAST, 800);
            }

            updateLivePreview();
        });

        // --- COMMAND PALETTE (Ctrl+K) ---
        const cmdPalette = document.getElementById('cmd-palette');
        const cmdInput = document.getElementById('cmd-input');
        const cmdResults = document.getElementById('cmd-results');

        function toggleCommandPalette() {
            if (cmdPalette.classList.contains('hidden')) {
                cmdPalette.classList.remove('hidden');
                cmdInput.value = '';
                cmdInput.focus();
                renderCmdResults('');
            } else {
                cmdPalette.classList.add('hidden');
            }
        }

        function renderCmdResults(query) {
            const q = String(query || '').toLowerCase();
            const items = [
                ...(state.tables || []).map(t => ({ type: 'Table', val: t, icon: 'database' })),
                ...(state.columns || []).map(c => ({ type: 'Column', val: c, icon: 'columns' }))
            ].filter(item => item && item.val && item.val.toLowerCase().includes(q)).slice(0, 10);

            cmdResults.innerHTML = items.map(item => `
                <div class="flex items-center justify-between p-2 hover:bg-gray-900 cursor-pointer rounded border-b border-gray-800/50" onclick="alert('In a full app, this would append ${item.val} to the AST')">
                    <div class="flex items-center gap-2"><i data-lucide="${item.icon}" class="w-3.5 h-3.5 text-gray-500"></i><span class="text-[11px] text-gray-300 font-mono">${item.val}</span></div>
                    <span class="text-[9px] text-blue-500 uppercase">${item.type}</span>
                </div>
            `).join('');
            lucide.createIcons();
        }

        cmdInput.addEventListener('input', e => renderCmdResults(e.target.value));
        document.getElementById('cmd-close').addEventListener('click', toggleCommandPalette);

        // --- SHORTCUTS ---
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); toggleCommandPalette(); return; }
            if (e.key === 'Escape') { cmdPalette.classList.add('hidden'); return; }

            const activeTag = document.activeElement ? document.activeElement.tagName.toUpperCase() : '';
            if (['INPUT', 'SELECT', 'TEXTAREA'].includes(activeTag)) return;

            if (e.key === 'ArrowRight') { e.preventDefault();
                if(state.sidebarTab === 'basic') document.getElementById('tab-advanced').click();
                else if(state.sidebarTab === 'advanced') document.getElementById('tab-raw').click();
            }
            else if (e.key === 'ArrowLeft') { e.preventDefault();
                if(state.sidebarTab === 'raw') document.getElementById('tab-advanced').click();
                else if(state.sidebarTab === 'advanced') document.getElementById('tab-basic').click();
            }
            else if (e.key === 'ArrowDown') { e.preventDefault(); document.getElementById('main-tab-analytics').click(); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); document.getElementById('main-tab-data').click(); }
            else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); document.getElementById('btn-execute').click(); }
        });

        // --- FORMATTING ---
        const inrFormatter = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 });
        const numFormatter = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 });
        function formatData(col, val) {
            if (val === null || val === undefined) return '<span class="text-gray-700 italic">null</span>';
            if (typeof val === 'number') {
                const n = String(col).toLowerCase();
                if (n.includes('price') || n.includes('amount') || n.includes('revenue') || n.includes('cost') || n.includes('margin')) return inrFormatter.format(val);
                return numFormatter.format(val);
            }
            if (typeof val === 'string' && val.match(/^\d{4}-\d{2}-\d{2}T/)) return val.split('T')[0];
            return String(val);
        }

        // --- ANALYTICS ---
        function computeAnalytics() {
            const stats = [];
            if (!state.resultCols || !Array.isArray(state.resultCols)) return;

            state.resultCols.forEach(col => {
                if (!state.results || !Array.isArray(state.results)) return;
                const vals = state.results.map(r => r[col]).filter(v => typeof v === 'number' && !isNaN(v));
                if (vals.length > 0) {
                    const sum = vals.reduce((a, b) => a + b, 0);
                    const avg = sum / vals.length;
                    const min = Math.min(...vals);
                    const max = Math.max(...vals);
                    const variance = vals.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / vals.length;
                    const stdDev = Math.sqrt(variance);
                    stats.push({ col, count: vals.length, sum, avg, min, max, stdDev });
                }
            });
            state.stats = stats;
        }

        function renderAnalytics() {
            const el = document.getElementById('analytics-content');
            if (!state.results || state.results.length === 0) {
                el.innerHTML = `<div class="flex flex-col items-center justify-center text-gray-600 mt-20"><i data-lucide="bar-chart-3" class="w-12 h-12 mb-4 opacity-20"></i><p class="text-xs uppercase tracking-widest">Execute Query to generate analytics</p></div>`;
                lucide.createIcons(); return;
            }
            if (!state.stats || state.stats.length === 0) {
                el.innerHTML = `<div class="p-4 text-gray-500 text-xs text-center border border-gray-800 border-dashed rounded mt-10">No numeric columns found.</div>`;
                return;
            }

            el.innerHTML = `
                <div class="mb-4">
                    <h3 class="text-[12px] text-blue-400 font-bold uppercase tracking-widest mb-1"><i data-lucide="activity" class="w-3 h-3 inline"></i> Descriptive Statistics</h3>
                </div>
                <div class="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden shadow-xl">
                    <table class="w-full text-left">
                        <thead class="bg-gray-950 border-b border-gray-800">
                            <tr>
                                <th class="p-3 text-[9px] font-bold text-gray-400 uppercase tracking-widest">Metric / Field</th>
                                <th class="p-3 text-[9px] font-bold text-gray-400 uppercase tracking-widest text-right">Sum (Σ)</th>
                                <th class="p-3 text-[9px] font-bold text-gray-400 uppercase tracking-widest text-right">Mean (μ)</th>
                                <th class="p-3 text-[9px] font-bold text-gray-400 uppercase tracking-widest text-right">Std Dev (σ)</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800/50">
                            ${state.stats.map(s => `
                                <tr class="hover:bg-gray-800/30 transition-colors">
                                    <td class="p-3 text-[11px] font-bold text-blue-300 font-mono">${s.col}</td>
                                    <td class="p-3 text-[11px] text-white font-mono text-right">${formatData(s.col, s.sum)}</td>
                                    <td class="p-3 text-[11px] text-white font-mono text-right">${formatData(s.col, s.avg)}</td>
                                    <td class="p-3 text-[11px] text-yellow-500 font-mono text-right">${formatData(s.col, s.stdDev)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>`;
            lucide.createIcons();
        }

        async function fetchAuditLogs() {
            try {
                const res = await apiGet('/metadata/audit');
                const logs = res.audit_log || [];
                const el = document.getElementById('telemetry-content');
                el.innerHTML = `
                    <div class="mb-4 flex gap-4 border-b border-gray-800 pb-4">
                        <div class="bg-gray-900 p-2 rounded border border-gray-800 flex-1"><span class="text-[9px] text-gray-500 uppercase block mb-1">AST Parse Time</span><span class="text-white text-sm font-bold">${state.telemetry?.parse_ms || 0} ms</span></div>
                        <div class="bg-gray-900 p-2 rounded border border-gray-800 flex-1"><span class="text-[9px] text-gray-500 uppercase block mb-1">Policy Govern.</span><span class="text-green-400 text-sm font-bold">${state.telemetry?.policy_ms || 0} ms</span></div>
                    </div>
                    <h3 class="text-[12px] text-purple-400 font-bold uppercase tracking-widest mb-2"><i data-lucide="shield-check" class="w-3 h-3 inline"></i> Governance & Audit Log</h3>
                    <div class="space-y-2">
                        ${logs.map(l => `<div class="bg-gray-950 p-2 border border-gray-800 rounded text-[9px] font-mono"><span class="text-blue-400">[${new Date(l.time*1000).toLocaleTimeString()}]</span> <span class="text-yellow-400">${l.event}</span>: <span class="text-gray-400">${escapeHTML(l.details)}</span></div>`).join('')}
                    </div>
                `;
                lucide.createIcons();
            } catch(e) { console.error(e); }
        }

        function renderTelemetry(data) {
            state.telemetry = data.telemetry || {};
            const el = document.getElementById('telemetry-content');
            if (data.type === 'explain') {
                el.innerHTML = `
                    <div class="mb-4 flex gap-4 border-b border-gray-800 pb-4">
                        <div class="bg-gray-900 p-2 rounded border border-gray-800 flex-1"><span class="text-[9px] text-gray-500 uppercase block mb-1">AST Parse Time</span><span class="text-white text-sm font-bold">${state.telemetry.parse_ms || 0} ms</span></div>
                        <div class="bg-gray-900 p-2 rounded border border-gray-800 flex-1"><span class="text-[9px] text-gray-500 uppercase block mb-1">Policy Govern.</span><span class="text-green-400 text-sm font-bold">${state.telemetry.policy_ms || 0} ms</span></div>
                    </div>
                    <h3 class="text-[12px] text-purple-400 font-bold uppercase tracking-widest mb-2"><i data-lucide="git-merge" class="w-3 h-3 inline"></i> Optimizer Graph</h3>
                    <pre class="bg-gray-950 p-4 border border-gray-800 rounded overflow-x-auto text-blue-300 text-[10px] leading-relaxed custom-scrollbar">${escapeHTML(data.plan)}</pre>
                `;
            }
            lucide.createIcons();
        }

        // --- EXECUTION PIPELINE ---
        async function triggerPipeline(isExplain = false) {
            const btnId = isExplain ? 'btn-explain' : 'btn-execute';
            const btn = document.getElementById(btnId);
            const originalText = btn.innerHTML;
            btn.innerHTML = `<span class="loader border-t-white w-3 h-3"></span>`;
            btn.disabled = true;

            try {
                const rawSql = buildSQLString();

                // Safely update the main dashboard preview before execution
                const mainSqlPreview = document.getElementById('main-sql-preview');
                if (mainSqlPreview) mainSqlPreview.innerText = rawSql;

                const res = await fetch('/api/query/compile_and_execute', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sql: rawSql, is_explain: isExplain })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Compiler Pipeline failed");

                if (isExplain) {
                    document.getElementById('main-tab-telemetry').click();
                    renderTelemetry(data);
                } else {
                    state.telemetry = data.telemetry || {};

                    // Safely update UI Metrics
                    const elRows = document.getElementById('m-rows');
                    if (elRows) elRows.innerText = (data.row_count || 0).toLocaleString('en-IN');

                    const elCols = document.getElementById('m-cols');
                    if (elCols) elCols.innerText = data.columns ? data.columns.length : 0;

                    const elTime = document.getElementById('m-time');
                    if (elTime && state.telemetry.execution_ms) elTime.innerText = (state.telemetry.execution_ms / 1000).toFixed(3) + 's';

                    // Safely inject returned formatted SQL
                    if (mainSqlPreview && data.sql) mainSqlPreview.innerText = data.sql;

                    state.results = data.rows || [];
                    state.resultCols = data.columns || [];

                    document.getElementById('grid-empty').classList.add('hidden');
                    document.getElementById('grid-table').classList.remove('hidden');
                    document.getElementById('btn-export').classList.remove('hidden');

                    if (state.resultCols.length > 0) {
                        document.getElementById('grid-head').innerHTML = `<tr>${state.resultCols.map(c => `<th class="px-3 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm">${c}</th>`).join('')}</tr>`;
                        document.getElementById('grid-body').innerHTML = state.results.slice(0, 1000).map(row =>
                            `<tr class="hover:bg-gray-900/50 transition-colors">${state.resultCols.map(c => `<td class="px-3 py-2 border-r border-gray-800/30 last:border-0 text-[11px] text-gray-300 font-mono tracking-tight">${formatData(c, row[c])}</td>`).join('')}</tr>`
                        ).join('');
                    } else {
                        document.getElementById('grid-head').innerHTML = '';
                        document.getElementById('grid-body').innerHTML = '';
                    }

                    computeAnalytics();
                    if (state.mainTab === 'analytics') renderAnalytics();
                }
            } catch (e) {
                if (!isExplain) {
                    document.getElementById('grid-empty').classList.remove('hidden');
                    document.getElementById('grid-table').classList.add('hidden');
                    document.getElementById('grid-empty').innerHTML = `<i data-lucide="shield-alert" class="w-10 h-10 text-red-500 mb-2 opacity-80"></i><p class="text-[11px] text-red-400 font-mono max-w-lg text-center break-words px-8">${e.message}</p>`;
                    lucide.createIcons();
                } else alert(e.message);
            } finally {
                btn.innerHTML = originalText; btn.disabled = false;
            }
        }

        document.getElementById('btn-execute').addEventListener('click', () => triggerPipeline(false));
        document.getElementById('btn-explain').addEventListener('click', () => triggerPipeline(true));
        document.getElementById('btn-export').addEventListener('click', () => { /* Export Hook */ });

        lucide.createIcons();
        init();
    </script>
</body>
</html>