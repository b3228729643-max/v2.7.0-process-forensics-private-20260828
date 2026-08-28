# FIG-P556-03 数学/概率语义独立复算（SA1）

对行随机转移核 $K$，若 $\pi(x)K(x,y)=\pi(y)K(y,x)$ 对每对状态成立，则

$$ (\pi K)(y)=\sum_x\pi(x)K(x,y)=\sum_x\pi(y)K(y,x)=\pi(y)\sum_xK(y,x)=\pi(y). $$

故详细平衡可推出平稳性。它却不推出连通/不可约或唯一性：$K=A=I_2$ 有两个断开的闭沟通类。任意 $\pi=(a,1-a)$ 均满足 $\pi A=\pi$，也满足详细平衡，因而平稳分布不唯一。图中的一般核记号 $K(x,y),\pi(x)$ 在有限状态时正是章节的 $a_{ij},\rho_i$ 专门化，并未改变方向；图内、题注和紧邻正文的表述与该反例一致。

结论：`MATH_SEMANTICS_PASS=true`、`PROBABILITY_SEMANTICS_PASS=true`、`TEXT_CONSISTENCY_PASS=true`。
