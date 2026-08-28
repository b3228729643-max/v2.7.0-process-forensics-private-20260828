# Installed pgfplots causality excerpts

- `D:\texlive\2026\texmf-dist\tex\generic\pgfplots\pgfplotscoordprocessing.code.tex` (367036 bytes, SHA-256 `7A884E8DAA52C24CD65DA0B6A7158466B544FA65355116686FDA292F0A60CEF3`)
- `D:\texlive\2026\texmf-dist\tex\generic\pgfplots\pgfplots.code.tex` (486348 bytes, SHA-256 `C4245419E40E5058320853728F6BB93521C153D89F1FBF185CE8793D067C1CA6`)

## `forget plot` marks an ordinary plot irrelevant before plot-spec retention

```tex
4249		/pgfplots/forget plot/.is if=pgfplots@curplot@isirrelevant,
4250		/pgfplots/forget plot/.default=true,
5121		% it is possible that '#1' contains 'forget plot'. So, we need to
5122		% set the options before checking \ifpgfplots@curplot@isirrelevant:
5123		\pgfplots@disable@non@survey@keys
5124		\pgfplotsset{/pgfplots/every axis plot,#1}%
5125		%
5126		\ifpgfplots@curplot@isirrelevant
5127			\def\pgfplots@addplot@survey@@optionlist{/pgfplots/every axis plot,/pgfplots/every forget plot}%
5128			\pgfplotsset{/pgfplots/every forget plot,/pgfplots/every axis plot post}%
5129		\else
5130			\edef\pgfplots@addplot@survey@@optionlist{%
5131				/pgfplots/every axis plot,%
5132				/pgfplots/every axis plot except legend,%
3716		\ifpgfplots@curplot@isirrelevant
3717			% for \label commands:
3718			\expandafter\pgfplots@rememberplotspec@for@label\expandafter{\pgfplots@addplot@survey@@optionlist}%
3719		\else
3720			\expandafter\pgfplots@rememberplotspec\expandafter{\pgfplots@loc@TMPa}%
```

The five current ordinary `\addplot` option lists each set `forget plot` exactly once. The key sets `pgfplots@curplot@isirrelevant`; the coordinate-processing branch then avoids `\pgfplots@rememberplotspec` for those plots.

## Manual legend images append their specs

```tex
5794	\def\pgfplots@addlegendimage{\pgfutil@ifnextchar[{\pgfplots@addlegendimage@opt}{\pgfplots@addlegendimage@opt[]}}%
5795	\def\pgfplots@addlegendimage@opt[#1]#2{%
5796		\pgfplots@rememberplotspec[#1]{/pgfplots/every axis plot,#2,/pgfplots/.cd,/pgfplots/every axis plot post}%
```

## Legend construction consumes remembered plot specs in list order

```tex
5721		\pgfplotslistforeachungrouped\pgfplots@plotspeclist\as\entry{%
5722			\expandafter\let\csname m@pgfplots@img@\the\c@pgfplots@row,\the\c@pgfplots@col\endcsname=\entry
5723			\advance\c@pgfplots@col by1
5724			\ifnum\pgfplots@legend@columns=\c@pgfplots@col\relax
5725				\c@pgfplots@col=0
5726				\advance\c@pgfplots@row by1
5727			\fi
5728			\advance\c@pgfplots@no by1
5729		}%
5730		\ifnum\c@pgfplots@col=0
5731		\else
5732			\advance\c@pgfplots@row by1
5733		\fi
5734		\ifnum\c@pgfplots@row<\c@pgfplots@row@end
5735			\edef\c@pgfplots@row@end{\the\c@pgfplots@row}%
5736		\fi
5737		\ifnum\c@pgfplots@no<\c@pgfplots@no@leg
5738			\edef\c@pgfplots@no@leg{\the\c@pgfplots@no}%
5739		\fi
5760				\pgfutil@ifundefined{m@pgfplots@\the\c@pgfplots@row,\the\c@pgfplots@col}{%
5761				}{%
5762					\pgfutil@ifundefined{m@pgfplots@img@\the\c@pgfplots@row,\the\c@pgfplots@col}{%
5763					}{%
5764						\expandafter\let\expandafter\pgfplots@legendtmp\csname m@pgfplots@\the\c@pgfplots@row,\the\c@pgfplots@col\endcsname
5765						\expandafter\pgfplotslistpushbackglobal\expandafter{\pgfplots@legendtmp}\to\pgfplots@legend%
5766						%
5767						\expandafter\let\expandafter\pgfplots@legendtmp\csname m@pgfplots@img@\the\c@pgfplots@row,\the\c@pgfplots@col\endcsname
5768						\expandafter\pgfplotslistpushbackglobal\expandafter{\pgfplots@legendtmp}\to\pgfplots@plotspeclist%
```

With zero retained ordinary plot specs, the two unchanged manual legend-image specs are the only entries in the plot-spec list. They therefore pair, in order, with the unchanged two legend entries. This is a static mechanism proof only; the disconnected x2 rendering still requires a new PDF.
