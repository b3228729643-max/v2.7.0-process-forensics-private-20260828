# Read-only source/context used

## Figure source lines 1--37
```tex
  1: % v2.3.1 figure UID: FIG-P445-01
  2: % Proposed post-v2.3.1 polish for FIG-P445-01: protect key-label size and stroke hierarchy.
  3: \tikzset{slfig-FIG-P445-01/.style={font=\fontsize{9.2pt}{11.0pt}\selectfont,every path/.append style={line cap=round,line join=round}}}
  4: \begin{figure}[H]
  5: \centering
  6: \begin{tikzpicture}[slfig-FIG-P445-01,x=1.35cm,y=1.35cm,
  7:   cluster band/.style={rounded corners=2.2pt,line width=.44pt,draw opacity=.30,fill opacity=.075},
  8:   cluster label/.style={font=\bfseries\fontsize{9.6pt}{11.3pt}\selectfont},
  9:   merge axis/.style={-{Stealth[length=2.0mm,width=1.18mm]},line width=.72pt},
 10:   merge tick/.style={line width=.50pt},
 11:   dendro branch/.style={draw=SLInk,line width=.98pt},
 12:   cut line/.style={draw=SLGray!88!black,line width=.82pt,densely dashed},
 13: ]
 14:   % Cluster bands lie behind branches and stop below the cut height 1.40.
 15:   \path[cluster band,draw=SLBlue,fill=SLBlue] (-.35,.12) rectangle (1.35,1.34);
 16:   \path[cluster band,draw=SLGold,fill=SLGold] (1.65,.12) rectangle (2.35,1.34);
 17:   \path[cluster band,draw=SLTeal,fill=SLTeal] (2.65,.12) rectangle (4.35,1.34);
 18:   \node[cluster label,text=SLBlue] at (.5,.25) {$C_1$};
 19:   \node[cluster label,text=SLGold!88!black] at (2,.25) {$C_2$};
 20:   \node[cluster label,text=SLTeal] at (3.5,.25) {$C_3$};
 21: 
 22:   \draw[merge axis] (-.65,.05)--(-.65,3.35)
 23:     node[above,rotate=90,anchor=south,font=\fontsize{9.4pt}{11.2pt}\selectfont] {合并高度};
 24:   \foreach \y in {0,1,2,3}{\draw[merge tick] (-.70,\y)--(-.60,\y) node[left=2pt,font=\fontsize{8.6pt}{10.2pt}\selectfont]{\y};}
 25:   \foreach \x/\lab in {0/$x_1$,1/$x_2$,2/$x_3$,3/$x_4$,4/$x_5$}
 26:     \node[font=\fontsize{9.4pt}{11.2pt}\selectfont,anchor=north] at (\x,0) {\lab};
 27: 
 28:   % Explicit merge heights: .65, .95, 2.10, 3.00.
 29:   \draw[dendro branch] (0,.08)--(0,.65)--(1,.65)--(1,.08);
 30:   \draw[dendro branch] (3,.08)--(3,.95)--(4,.95)--(4,.08);
 31:   \draw[dendro branch] (3.5,.95)--(3.5,2.10)--(2,2.10)--(2,.08);
 32:   \draw[dendro branch] (.5,.65)--(.5,3.00)--(2.75,3.00)--(2.75,2.10);
 33:   \draw[cut line] (-.45,1.40)--(4.45,1.40);
 34:   \node[font=\fontsize{9.2pt}{11pt}\selectfont,text=SLGray!88!black,anchor=west] at (4.50,1.40) {切割高度 $h_c=1.4$};
 35: \end{tikzpicture}
 36: \caption{树的纵坐标表示合并高度；在虚线高度切割时，虚线以下的连通分支分别成为一个类。}\label{fig:V4-C02-dendrogram}
 37: \end{figure}
```

## Adjacent V4-C02 lines 416--417
```tex
416: \input{../../绘图源码/第04册_无监督学习与矩阵分解/V4-C02/fig_v4_c02_dendrogram.tex}
417: \Cref{fig:V4-C02-dendrogram}对应层次聚类知识点：在所示高度切割得到$\{x_1,x_2\}$、$\{x_3\}$和$\{x_4,x_5\}$三个类；改变切割高度只合并或拆分嵌套分支，不改变已经记录的合并顺序。
```

## Global caption style line 305
```tex
305: \captionsetup{font={small,stretch=1.12},labelfont=bf,labelsep=quad,skip=5pt}
```
