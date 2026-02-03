\documentclass[11pt, a4paper]{article}

% --- UNIVERSAL PREAMBLE BLOCK ---
\usepackage[a4paper, top=2.5cm, bottom=2.5cm, left=2cm, right=2cm]{geometry}
\usepackage{fontspec}
\usepackage[english, bidi=basic, provide=*]{babel}

% Set default font to Sans Serif (Noto Sans) for corporate minimalism
\babelfont{rm}{Noto Sans}

\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{fancyhdr}

% Custom Colors (Grew Identity)
\definecolor{grewindigo}{HTML}{6366F1}
\definecolor{darkslate}{HTML}{0F172A}

% Header/Footer Configuration
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small \textcolor{grewindigo}{\textbf{GREW ENERGY}} | Analytics Terminal}
\fancyhead[R]{\small User Manual v2.0}
\fancyfoot[C]{\thepage}

% Title Styling
\titleformat{\section}{\large\bfseries\color{darkslate}}{}{0em}{}[\titlerule]

\begin{document}

\begin{titlepage}
    \centering
    \vspace*{4cm}
    {\Huge \bfseries \color{darkslate} Grew Analytics Command Manual \par}
    \vspace{1cm}
    {\Large Operational Logic \& Strategic Intelligence \par}
    \vspace{2cm}
    \framebox{\parbox{0.75\textwidth}{\centering \vspace{1cm} \textbf{Internal Audit Documentation} \\ Revenue, CAGR, HHI, and Ingestion Governance. \vspace{1cm}}}
    \vfill
    {\large Version 2.0 \par}
\end{titlepage}

\section{Revenue Derivation \& Register Logic}
The dashboard's revenue figures are derived from the master register using a strict exclusionary audit path to ensure financial precision.

\begin{itemize}[leftmargin=*]
    \item \textbf{Currency Denomination:} All financial values displayed in the dashboard are denominated in \textbf{Indian Rupees (₹) Crores}.
    \item \textbf{Basis of Value:} All revenue figures represent the \textbf{Taxable Value} only.
    \item \textbf{Revenue Exclusion Criteria (Governance Drops):}
    \begin{enumerate}
        \item \textbf{Advance Billing (Logistics):} Any entries containing a \textit{Vehicle No.} or marked as \textit{By Road} are categorized as Advance Billing and are strictly \textbf{excluded} from the primary Revenue metrics.
        \item \textbf{Invoice Status:} Any record with an \textit{Invoice Status} marked as \textbf{'X'} is considered void/cancelled and is \textbf{excluded} from all revenue calculations.
    \end{enumerate}
    \item \textbf{Advanced Billing (Realised Flip):} By toggling the \textbf{Realised} button at the top of the Matrix Master, the dashboard flips to display these excluded "Advance Billing" metrics for separate auditing.
\end{itemize}

\section{Strategic Intelligence Section}
The Strategic Intelligence section provides high-level insights derived from the processed data. These insights enable executives to monitor growth, concentration, and operational scale.

\begin{table}[htbp]
\centering
\small
\begin{tabular}{lp{6.5cm}p{5cm}}
\toprule
\textbf{Insight / Metric} & \textbf{Calculation / Derivation Logic} & \textbf{Strategic Utility} \\
\midrule
Total Revenue & $\sum (\text{Taxable Value}) - \text{Exclusions}$ & Absolute realized income in \textbf{Crores}. \\ \addlinespace
Revenue / MW & $\frac{\text{Net Taxable Revenue (₹ Cr)}}{\text{Segment Capacity (MW)}}$ & Yield efficiency per unit of scale. \\ \addlinespace
Annualized CAGR & $\left[ \left( \frac{\text{Value}_{\text{end}}}{\text{Value}_{\text{start}}} \right)^{\frac{1}{n}} - 1 \right] \times 100$ & Measures the smooth annualized growth rate over $n$ periods. \\ \addlinespace
HHI Index & $\sum_{i=1}^{N} (s_i^2)$ & Measures concentration risk where $s_i$ is the \% share of a customer. \\
\bottomrule
\end{tabular}
\caption{Strategic Intelligence Metric Glossary}
\end{table}

\subsection{CAGR \& Concentration Details}
\begin{itemize}
    \item \textbf{Annualized CAGR:} This calculation provides the geometric progression ratio that provides a constant rate of return over the time period ($n$). It is used to evaluate the growth trajectory of specific segments or customers.
    \item \textbf{HHI Interpretation:} The Herfindahl-Hirschman Index (HHI) monitors customer dependency. 
    \begin{itemize}
        \item \textbf{HHI $>$ 2,500:} High concentration; indicates high dependency on few large clients.
        \item \textbf{HHI $<$ 1,500:} Diversified, lower-risk customer base.
    \end{itemize}
\end{itemize}

\section{App Features \& UI Interaction}
\begin{itemize}[leftmargin=*]
    \item \textbf{Customer Analytics:} Sidebar selection filters the entire dashboard (including Strategic Intelligence) for the specific customer.
    \item \textbf{Segment Drill-down:} Defaults to \textbf{Solar Module}. Users can switch segments to view alternate product vertical performance.
    \item \textbf{Metric Toggling:} Interactive controls allow the user to toggle between \textbf{Amount} and \textbf{Quantity (Qty)} within specific views.
    \item \textbf{Data Ingestion Audit:} "Ingested Rows" shows total raw data; "Governance Drops" shows rows excluded by logic.
\end{itemize}

\section{Keyboard Shortcuts \& Navigation}
\begin{itemize}[label=--]
    \item \textbf{Ctrl+B:} Toggle sidebar visibility (Expand/Collapse).
    \item \textbf{Tab Key:} Sequential jump between interface elements (Right/Left).
    \item \textbf{Arrow Keys:} Navigate between adjacent metric columns in data grids.
\end{itemize}

\section{Authentication \& Security}
\begin{itemize}
    \item \textbf{Verification:} Fresh Magic Link required upon every explicit signout.
    \item \textbf{Rate Limiting:} Collective system limit of \textbf{2 Magic Link requests per hour}.
\end{itemize}

\end{document}
