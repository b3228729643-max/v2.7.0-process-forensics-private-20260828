# Exact single-source diff

```diff
-  xmin=-4.35,xmax=2.55,ymin=-2.05,ymax=2.45,
+  xmin=-4.00,xmax=3.90,ymin=-2.80,ymax=2.80,
-    ({4.2*cos(x)},{1.52*sin(x)});
+    ({2.70*(cos(x)-sin(x))},{2.70*sin(x)});
-    ({3.25*cos(x)},{1.17*sin(x)});
+    ({2.15*(cos(x)-sin(x))},{2.15*sin(x)});
-    ({2.35*cos(x)},{.85*sin(x)});
+    ({1.65*(cos(x)-sin(x))},{1.65*sin(x)});
-    ({1.45*cos(x)},{.52*sin(x)});
-  \coordinate (q0) at (axis cs:-3.20,1.75);
-  \coordinate (q1) at (axis cs:-3.20,.85);
-  \coordinate (q2) at (axis cs:-1.65,.85);
-  \coordinate (q3) at (axis cs:-1.65,.32);
-  \coordinate (q4) at (axis cs:-.70,.32);
-  \coordinate (q5) at (axis cs:-.70,.08);
-  \coordinate (q6) at (axis cs:0,.08);
-  \coordinate (q7) at (axis cs:0,0);
+    ({.90*(cos(x)-sin(x))},{.90*sin(x)});
+  \coordinate (q0) at (axis cs:-3.20,2.20);
+  \coordinate (q1) at (axis cs:-3.20,1.60);
+  \coordinate (q2) at (axis cs:-1.60,1.60);
+  \coordinate (q3) at (axis cs:-1.60,.80);
+  \coordinate (q4) at (axis cs:-.80,.80);
+  \coordinate (q5) at (axis cs:-.80,.40);
+  \coordinate (q6) at (axis cs:-.40,.40);
+  \coordinate (q7) at (axis cs:-.40,.20);
-  \draw[-{Stealth[length=2mm,width=1.2mm]},draw=SLTeal,line width=1.05pt,dash pattern=on 3pt off 2pt] (q0)--(q1);
-  \draw[-{Stealth[length=2mm,width=1.2mm]},draw=SLTeal,line width=1.05pt,dash pattern=on 3pt off 2pt] (q2)--(q3);
-  \draw[-{Stealth[length=2mm,width=1.2mm]},draw=SLTeal,line width=1.05pt,dash pattern=on 3pt off 2pt] (q4)--(q5);
-  \draw[-{Stealth[length=2mm,width=1.2mm]},draw=SLTeal,line width=1.05pt,dash pattern=on 3pt off 2pt] (q6)--(q7);
+  \draw[-{Stealth[length=2mm,width=1.2mm]},draw=SLTeal,line width=1.05pt,dash pattern=on 1.2pt off 1.2pt] (q0)--(q1);
+  \draw[-{Stealth[length=2mm,width=1.2mm]},draw=SLTeal,line width=1.05pt,dash pattern=on 1.2pt off 1.2pt] (q2)--(q3);
+  \draw[-{Stealth[length=2mm,width=1.2mm]},draw=SLTeal,line width=1.05pt,dash pattern=on 1.2pt off 1.2pt] (q4)--(q5);
+  \draw[-{Stealth[length=2mm,width=1.2mm]},draw=SLTeal,line width=1.05pt,dash pattern=on 1.2pt off 1.2pt] (q6)--(q7);
-  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,left=1.5pt] at (q1) {1};
-  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,above=1.5pt] at (q2) {2};
-  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,left=1.5pt] at (q3) {3};
-  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,above=1.5pt] at (q4) {4};
-  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,left=1.5pt] at (q5) {5};
+  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,anchor=east,xshift=-4pt] at (q1) {1};
+  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,anchor=south,yshift=3pt] at (q2) {2};
+  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,anchor=east,xshift=-4pt] at (q3) {3};
+  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,anchor=south,yshift=4pt] at (q4) {4};
+  \node[font=\fontsize{8.6pt}{10.1pt}\selectfont,anchor=east,xshift=-2pt] at (q5) {5};
-    anchor=south east,xshift=-2pt,yshift=3.5pt] at (q6) {6};
+    anchor=south west,xshift=4pt,yshift=12pt] at (q6) {6};
-    anchor=south west,xshift=5.5pt,yshift=1.5pt] at (q7) {7};
+    anchor=south east,xshift=-4pt,yshift=8pt] at (q7) {7};
-    coordinates {(-3.20,.85) (-1.65,.32) (-.70,.08) (0,0)};
+    coordinates {(-3.20,1.60) (-1.60,.80) (-.80,.40) (-.40,.20)};
-  \addlegendimage{draw=SLTeal,line width=1.05pt,dash pattern=on 3pt off 2pt}
+  \addlegendimage{draw=SLTeal,line width=1.05pt,dash pattern=on 1.2pt off 1.2pt}
```

No caption, alt text, font declaration, axis name, figure label, color role, shared macro, chapter source, build entry, or second source changed.
