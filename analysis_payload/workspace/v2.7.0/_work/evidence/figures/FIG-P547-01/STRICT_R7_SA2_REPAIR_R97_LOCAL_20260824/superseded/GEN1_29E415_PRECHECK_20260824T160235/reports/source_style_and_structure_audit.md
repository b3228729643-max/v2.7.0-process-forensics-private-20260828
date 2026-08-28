# Source style and structural audit

- Canonical source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_transition_graph.tex`
- SHA-256: `29E41548386DA1A3D0EAA40B728DD9CD7B235715A28EEDB5EACD5AAFDE9784E3`

## Declared typesetting / stroke values

- figure default: `\fontsize{9.8pt}{11.7pt}` (line 3)
- local geometry relations: equals `.72pt` rules at `±.57ex`; arrow `.70pt` with 2.0 mm head (lines 8–14)
- state node text: `10.2pt`, 9.6 mm node, `.86pt` border (lines 17–19)
- ordinary/focus labels: `11.6pt`; focus label outline `.72pt`, inner sep `2.75pt` (lines 21–22)
- title: bold `10.2pt` (line 23)
- matrix default: `9.8pt`; formulas `11.8pt`; explanatory formula `11.6pt` (lines 24, 39–41, 59–61)
- bridge default: `9.6pt`; bridge formula `12.0pt`; bridge sentence `11.6pt` (lines 25–28, 44–48)
- edge/focus/bridge-arrow line widths: `.86pt` / `1.34pt` / `.88pt` (lines 19–20,28)

## Source geometry / semantics

- Two panels use the same node and edge construction; gold focuses 0.3 and the transpose bridge explicitly preserves `P=A^{\mathsf T}` through an auditable geometric equality relation.
- There is no `resizebox`, `scalebox`, raster inclusion, or post-hoc figure scale in the frozen source.

## Frozen source excerpt

```tex
% v2.3.1 figure UID: FIG-P547-01
% v2.7.0 repair for FIG-P547-01: canonical A/P notation, readable type, and a literal transpose bridge.
\tikzset{slfig-FIG-P547-01/.style={font=\fontsize{9.8pt}{11.7pt}\selectfont,every path/.append style={line cap=round,line join=round}}}
\begin{figure}[htbp]
% Real TikZ geometry replaces low-profile relation glyphs.  The equals bars
% span 1.14ex plus their rule width, and the arrowhead is 2.0mm high, so each
% semantic relation remains compact while exposing auditable PDF paths.
\newcommand{\FIGPFiveGeomEq}{\mathrel{\vcenter{\hbox{%
  \tikz[x=1em,y=1ex,line cap=round]{%
    \draw[-,draw=SLInk,line width=.72pt] (-.36,.57)--(.36,.57);%
    \draw[-,draw=SLInk,line width=.72pt] (-.36,-.57)--(.36,-.57);}}}}}
\newcommand{\FIGPFiveGeomArrow}{\mathrel{\vcenter{\hbox{%
  \tikz[x=1em,y=1ex,line cap=round,line join=round]{%
    \draw[-{Stealth[length=1.8mm,width=2.0mm]},draw=SLInk,line width=.70pt] (-.48,0)--(.48,0);}}}}}
\centering
\begin{tikzpicture}[slfig-FIG-P547-01,>=Stealth,
  state/.style={circle,draw=SLBlue,fill=SLBlue!9,minimum size=9.6mm,inner sep=1.4pt,
    line width=.86pt,font=\fontsize{10.2pt}{12.0pt}\selectfont},
  edge/.style={-{Stealth[length=1.95mm]},draw=SLTeal,line width=.86pt},
  focus/.style={-{Stealth[length=2.15mm]},draw=SLGold,line width=1.34pt},
  lab/.style={font=\fontsize{11.6pt}{13.3pt}\selectfont,fill=white,inner sep=1.35pt},
  focus lab/.style={lab,draw=SLGold,line width=.72pt,rounded corners=1.2pt,inner sep=2.75pt},
  title/.style={font=\fontsize{10.2pt}{12.0pt}\selectfont\bfseries},
  matrix/.style={align=center,inner sep=2.5pt,font=\fontsize{9.8pt}{11.7pt}\selectfont},
  bridge/.style={draw=SLRuleGray,rounded corners=2pt,fill=SLSoftGray,align=center,
    minimum width=48mm,minimum height=15mm,line width=.72pt,inner sep=2.6pt,
    font=\fontsize{9.6pt}{11.5pt}\selectfont},
  bridge arrow/.style={-{Stealth[length=2.05mm]},draw=SLGold,line width=.88pt},
]
  \begin{scope}[shift={(-4.35,1.12)}]
    \node[title] at (0,1.47) {行随机 $A$：$a_{ij}\FIGPFiveGeomEq P(i\FIGPFiveGeomArrow j)$};
    \node[state] (l1) at (-1.35,0) {$1$};
    \node[state] (l2) at (1.35,0) {$2$};
    \draw[edge] (l1) to[loop left,min distance=11mm] node[lab,left] {$0.7$} (l1);
    \draw[edge] (l2) to[loop right,min distance=11mm] node[lab,right] {$0.8$} (l2);
    \draw[focus] (l1) to[bend left=22] node[focus lab,above=1.2mm] {$a_{12}\FIGPFiveGeomEq 0.3$} (l2);
    \draw[edge] (l2) to[bend left=22] node[lab,below] {$a_{21}\FIGPFiveGeomEq 0.2$} (l1);
    \node[matrix] at (0,-1.67)
      {{\fontsize{11.8pt}{13.6pt}\selectfont
        $A\FIGPFiveGeomEq\begin{bmatrix}0.7&\color{SLGold}\boxed{\mathbf{0.3}}\\0.2&0.8\end{bmatrix}$}\\[2.2pt]
       每行和为 $1$；{\fontsize{11.6pt}{13.3pt}\selectfont $\rho_{t+1}\FIGPFiveGeomEq\rho_tA$}};
  \end{scope}

  \node[bridge] (transpose) at (0,-.05)
    {{\fontsize{12.0pt}{13.8pt}\selectfont $P\FIGPFiveGeomEq A^{\mathsf T}$}\\[1.8pt]
     {\fontsize{11.6pt}{13.3pt}\selectfont 物理边 $i\FIGPFiveGeomArrow j$：$a_{ij}\FIGPFiveGeomEq P_{ji}$}};
  \draw[bridge arrow] (-2.98,-.05)--(transpose.west);
  \draw[bridge arrow] (transpose.east)--(2.98,-.05);

  \begin{scope}[shift={(4.35,1.12)}]
    \node[title] at (0,1.47) {列随机 $P$ / PageRank：$P_{ji}\FIGPFiveGeomEq P(i\FIGPFiveGeomArrow j)$};
    \node[state] (r1) at (-1.35,0) {$1$};
    \node[state] (r2) at (1.35,0) {$2$};
    \draw[edge] (r1) to[loop left,min distance=11mm] node[lab,left] {$0.7$} (r1);
    \draw[edge] (r2) to[loop right,min distance=11mm] node[lab,right] {$0.8$} (r2);
    \draw[focus] (r1) to[bend left=22] node[focus lab,above=1.2mm] {$P_{21}\FIGPFiveGeomEq 0.3$} (r2);
    \draw[edge] (r2) to[bend left=22] node[lab,below] {$P_{12}\FIGPFiveGeomEq 0.2$} (r1);
    \node[matrix] at (0,-1.67)
      {{\fontsize{11.8pt}{13.6pt}\selectfont
        $P\FIGPFiveGeomEq\begin{bmatrix}0.7&0.2\\\color{SLGold}\boxed{\mathbf{0.3}}&0.8\end{bmatrix}$}\\[2.2pt]
       每列和为 $1$；{\fontsize{11.6pt}{13.3pt}\selectfont $\boldsymbol p^{(t+1)}\FIGPFiveGeomEq P\boldsymbol p^{(t)}$}};
  \end{scope}
\end{tikzpicture}
\caption{行随机约定下的两状态转移图，并给出到列随机PageRank约定的显式转置桥。}\label{fig:V5-C01-transition-graph}
\end{figure}
```
