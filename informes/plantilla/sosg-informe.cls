%% sosg-informe.cls — Clase para los informes técnicos de SOS Galápagos (USFQ).
%% Motor: pdfLaTeX + BibTeX (TinyTeX). Compilar con informes/compilar.sh. Ver informes/LEEME.md.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{sosg-informe}[2026/11/04 Informes tecnicos de SOS Galapagos (USFQ)]

\LoadClass[11pt,a4paper]{article}

% ---------------------------------------------------------------- idioma y tipografía
\RequirePackage[T1]{fontenc}
\RequirePackage[spanish,es-noshorthands,es-tabla,es-nodecimaldot]{babel}
\RequirePackage{XCharter}                       % Charter (texto)
\RequirePackage[xcharter,vvarbb]{newtxmath}     % matemáticas a juego
\RequirePackage{icomma}                         % coma decimal en matemáticas: $0,8$
\RequirePackage[varqu,scaled=0.88]{zi4}               % Inconsolata (monoespaciada, Type 1)
\RequirePackage{microtype}
\RequirePackage{csquotes}                       % \enquote{} → «»
\DeclareQuoteStyle{spanish}{\guillemotleft}{\guillemotright}{\textquotedblleft}{\textquotedblright}
\setlength{\parindent}{1.4em}
\linespread{1.06}

% ---------------------------------------------------------------- página
\RequirePackage[a4paper,top=25mm,bottom=25mm,left=24mm,right=24mm,headsep=8mm]{geometry}
\RequirePackage{fancyhdr}
\RequirePackage{xcolor}
\definecolor{sosgris}{gray}{0.38}

% ---------------------------------------------------------------- figuras, tablas, listas
\RequirePackage{graphicx}
\RequirePackage{booktabs,tabularx,array,multirow,makecell}
\RequirePackage[font=small,labelfont=bf,labelsep=period,justification=justified,singlelinecheck=false]{caption}
\captionsetup[table]{skip=4pt}
\captionsetup[figure]{skip=5pt}
\RequirePackage{enumitem}
\setlist{itemsep=1pt,topsep=3pt,parsep=0pt,leftmargin=1.6em}
\RequirePackage{float}
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.8}
\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.75}
\setcounter{topnumber}{3}
\setcounter{totalnumber}{4}

% ---------------------------------------------------------------- títulos de sección
\RequirePackage{titlesec}
\titleformat{\section}{\normalfont\large\bfseries}{\thesection.}{0.6em}{}
\titleformat{\subsection}{\normalfont\normalsize\bfseries\itshape}{\upshape\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\normalfont\normalsize\itshape}{\thesubsubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{1.3em plus 0.3em}{0.5em}
\titlespacing*{\subsection}{0pt}{0.9em plus 0.2em}{0.35em}

% ---------------------------------------------------------------- bibliografía (autor-año, sosg.bst en español)
\RequirePackage[round,authoryear,sort]{natbib}
\setlength{\bibsep}{2pt plus 1pt}
\renewcommand{\bibfont}{\small}

% ---------------------------------------------------------------- enlaces
\RequirePackage[hidelinks,unicode]{hyperref}

% ---------------------------------------------------------------- datos del informe
% Valores por omisión: firma del responsable del repositorio.
\newcommand{\@serie}{SOS Galápagos · Informe técnico}
\newcommand{\@numero}{}
\newcommand{\@estado}{Borrador para discusión}
\newcommand{\@autores}{Julián Maya}
\newcommand{\@autorescita}{Maya, J.}
\newcommand{\@afiliacion}{Universidad San Francisco de Quito (USFQ) · USFQ Galápagos}
\newcommand{\@correo}{jamaya@usfq.edu.ec}
\newcommand{\@titulocorto}{}
\newcommand{\@titulocita}{}
\newcommand{\@anio}{2026}
\newcommand{\numero}[1]{\renewcommand{\@numero}{#1}}
\newcommand{\estado}[1]{\renewcommand{\@estado}{#1}}
\newcommand{\autores}[1]{\renewcommand{\@autores}{#1}}
\newcommand{\autorescita}[1]{\renewcommand{\@autorescita}{#1}}
\newcommand{\afiliacion}[1]{\renewcommand{\@afiliacion}{#1}}
\newcommand{\correo}[1]{\renewcommand{\@correo}{#1}}
\newcommand{\titulocorto}[1]{\renewcommand{\@titulocorto}{#1}}
\newcommand{\titulocita}[1]{\renewcommand{\@titulocita}{#1}}
\newcommand{\anio}[1]{\renewcommand{\@anio}{#1}}
\newcommand{\@relacionados}{}
\newcommand{\relacionados}[1]{\renewcommand{\@relacionados}{#1}}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyhead[R]{\footnotesize\itshape\color{sosgris}\@serie\ \@numero\ifx\@estado\@empty\else\ · \@estado\fi}
\fancyhead[L]{\footnotesize\itshape\color{sosgris}\@titulocorto}
\fancyfoot[C]{\small\thepage}
\fancypagestyle{primera}{\fancyhf{}\renewcommand{\headrulewidth}{0pt}\fancyfoot[C]{\small\thepage}}

\renewcommand{\maketitle}{%
  \thispagestyle{primera}%
  \begin{center}
    {\footnotesize\color{sosgris}\MakeUppercase{\@serie\ \@numero}\ifx\@estado\@empty\else\ · \MakeUppercase{\@estado}\fi\par}
    \vspace{1.1em}
    {\LARGE\bfseries\@title\par}
    \vspace{0.9em}
    {\large\@autores\par}
    \vspace{0.2em}
    {\small\itshape\color{sosgris}\@afiliacion\par}
    {\small\color{sosgris}\href{mailto:\@correo}{\@correo}\par}
    \ifx\@relacionados\@empty\else\vspace{0.15em}{\footnotesize\color{sosgris}\@relacionados\par}\fi
    \vspace{0.3em}
    {\small\color{sosgris}\@date\par}
  \end{center}
  \begingroup
    \renewcommand{\thefootnote}{}%
    \renewcommand{\@makefntext}[1]{\noindent\scriptsize\color{sosgris}##1}%
    \footnotetext{\textcopyright\ \@anio\ Universidad San Francisco de Quito (USFQ). Texto, figuras y modelos propios bajo licencia
      \textbf{CC BY 4.0}; el código, bajo Apache 2.0 con aviso de atribución (archivo \texttt{NOTICE}).
      Toda reutilización o publicación que use este material debe citar:
      \@autorescita\ (\@anio). \textit{\ifx\@titulocita\@empty\@titulocorto\else\@titulocita\fi}.
      \@serie\ \@numero. Universidad San Francisco de Quito (USFQ).
      Los datos de terceros conservan sus licencias (ver \texttt{LICENCIA-DATOS.md}).}%
  \endgroup
  \vspace{0.6em}}

% Resumen con palabras clave
\renewenvironment{abstract}{%
  \begin{center}\small\bfseries\MakeUppercase{Resumen}\end{center}\vspace{-0.6em}
  \list{}{\leftmargin=2.2em\rightmargin=2.2em}\item\relax\small\noindent\ignorespaces}%
  {\endlist}
\newcommand{\palabrasclave}[1]{\par\vspace{0.3em}\noindent\textbf{Palabras clave:} #1}

% Aviso obligatorio «modelo ≠ dato oficial» (AGENTS.md, regla 3)
\newenvironment{aviso}{%
  \par\vspace{0.6em}\list{}{\leftmargin=2.2em\rightmargin=2.2em}\item\relax\footnotesize
  \noindent\rule{\linewidth}{0.5pt}\par\vspace{0.2em}\noindent\textbf{Advertencia.}\ }%
  {\par\vspace{-0.2em}\noindent\rule{\linewidth}{0.5pt}\endlist\vspace{0.4em}}

% Utilidades
\newcommand{\issue}[1]{\##1}
\newcommand{\alto}{\enquote{alto}}
