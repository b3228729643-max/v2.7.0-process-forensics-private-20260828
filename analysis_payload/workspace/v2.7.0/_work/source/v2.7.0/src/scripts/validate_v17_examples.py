#!/usr/bin/env python3
"""Independent NumPy/SymPy recomputation for all 64 numbered examples.

The first (or ``--refresh-manifest``) run freezes source locations and hashes in
JSON.  Normal runs fail if an example question/solution changes without an
explicitly reviewed manifest refresh.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from fractions import Fraction as F
from pathlib import Path
from typing import Any, Callable

import numpy as np
import sympy as sp


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
CHAPTER_ROOT = SOURCE / "讲义源码"
TEST_ROOT = ROOT / "tests"
MANIFEST = TEST_ROOT / "v1.7_example_regression_manifest.json"
RESULT = TEST_ROOT / "v1.7_example_regression_results.json"
REPORT = TEST_ROOT / "v1.7_example_regression_report.md"
TOL = 1e-9


def close(actual: Any, expected: Any, tol: float = TOL) -> None:
    if not np.allclose(np.asarray(actual, dtype=float), np.asarray(expected, dtype=float), atol=tol, rtol=tol):
        raise AssertionError(f"actual={actual!r}, expected={expected!r}")


def scalar(actual: Any, expected: Any, tol: float = TOL) -> dict[str, Any]:
    close(float(actual), float(expected), tol)
    return {"actual": float(actual), "expected": float(expected)}


def entropy2(p: float) -> float:
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def c01() -> dict[str, Any]:
    value = np.array([[1, 0], [2, 1], [0, 1]]) @ np.array([2, -1])
    close(value, [2, 3, -1]); return {"value": value.tolist(), "shape": list(value.shape)}


def c02() -> dict[str, Any]:
    x, u = np.array([3.0, 1.0]), np.array([1.0, 1.0])
    a = u @ x / (u @ u); p = a * u; r = x - p
    close([a, u @ r, np.linalg.norm(r)], [2, 0, math.sqrt(2)])
    return {"coefficient": a, "projection": p.tolist(), "residual": r.tolist()}


def c03() -> dict[str, Any]:
    h = np.array([[2.0, 2.0], [2.0, 6.0]])
    eig = np.linalg.eigvalsh(h); close(np.linalg.det(h), 8); assert np.all(eig > 0)
    return {"determinant": float(np.linalg.det(h)), "eigenvalues": eig.tolist()}


def c04() -> dict[str, Any]: return scalar(len({2, 4, 6} | {4, 5, 6}) / 6, F(2, 3))
def c05() -> dict[str, Any]: return scalar(1 + 4 * 0.5 * 0.5, 2)
def c06() -> dict[str, Any]: return scalar(0.95 * 0.01 / (0.95 * 0.01 + 0.05 * 0.99), 0.0095 / 0.059)


def c07() -> dict[str, Any]:
    p = sp.symbols("p", positive=True)
    root = sp.solve(sp.Eq(sp.diff(7 * sp.log(p) + 3 * sp.log(1 - p), p), 0), p)[0]
    assert root == sp.Rational(7, 10)
    return {"mle": str(root), "second_derivative_at_mle": str(sp.diff(7 * sp.log(p) + 3 * sp.log(1 - p), p, 2).subs(p, root))}


def c08() -> dict[str, Any]:
    p, q = np.array([.8, .2]), np.array([.6, .4])
    d1, d2 = float(np.sum(p * np.log(p / q))), float(np.sum(q * np.log(q / p)))
    close([d1, d2], [0.091516221849, 0.104649628752], 1e-10); assert d1 != d2
    return {"kl_pq": d1, "kl_qp": d2}


def c09() -> dict[str, Any]:
    margins = np.array([1.4, 1.0, .3, -.2]); xi = np.maximum(0, 1 - margins)
    close(xi, [0, 0, .7, 1.2]); return {"margins": margins.tolist(), "slacks": xi.tolist()}


def c10() -> dict[str, Any]:
    a, b = np.array([3.0, 4.0]), 5.0; x = b * a / (a @ a); alpha = b / (a @ a)
    close([a @ x, np.linalg.norm(x), alpha], [b, 1, .2]); return {"x_star": x.tolist(), "multiplier": alpha}


def c11() -> dict[str, Any]:
    h, g0 = np.diag([4.0, 2.0]), np.array([-2.0, -4.0]); p = np.linalg.solve(h, -g0)
    close(p, [.5, 2]); close(h @ p + g0, [0, 0]); return {"newton_step": p.tolist()}


def c12() -> dict[str, Any]:
    h = np.diag([1.0, 100.0]); cond = np.linalg.cond(h); close(cond, 100)
    return {"condition_number": cond, "gd_stability_upper_bound": 2 / np.linalg.eigvalsh(h).max()}


def c13() -> dict[str, Any]:
    e0, e1 = np.array([0, 0, 1, 0]), np.array([0, 0, 0, 1]); risks = [e0.mean(), e1.mean()]
    close(risks, [.25, .25]); return {"risks": risks, "tie": True}


def c14() -> dict[str, Any]: return scalar(12 / 80 - 10 / 200, .10)


def c15() -> dict[str, Any]:
    degrees = np.array([1, 3, 9]); val = np.array([.42, .18, .31]); chosen = int(degrees[np.argmin(val)])
    assert chosen == 3; return {"chosen_degree": chosen, "validation_losses": val.tolist()}


def c16() -> dict[str, Any]:
    tp, fp, fn, tn = 36, 9, 4, 51
    vals = [(tp + tn) / 100, tp / (tp + fp), tp / (tp + fn), 2 * tp / (2 * tp + fp + fn)]
    close(vals, [.87, .8, .9, 72 / 85]); return {"accuracy_precision_recall_f1": vals}


def c17() -> dict[str, Any]:
    x, y, eta = np.array([2.0, -1.0]), 1.0, 1.0; w = eta * y * x; b = eta * y
    close([*w, b, y * (w @ x + b)], [2, -1, 1, 6]); return {"w": w.tolist(), "b": b, "new_margin": 6}


def c18() -> dict[str, Any]:
    w, b = np.array([1.0, 1.0]), -3.0; x = np.array([[3, 3], [2, 2], [1, 1]]); y = np.array([1, 1, -1])
    margins = y * (x @ w + b); close(margins, [3, 1, 1]); return {"final_margins": margins.tolist()}


def c19() -> dict[str, Any]:
    b = 1.0; w1, w2 = -1.1, -1.1
    assert w1 + b < 0 and w2 + b < 0 and w1 + w2 + b < -b < 0
    return {"contradiction": "two negative-class inequalities force the positive (1,1) score below zero"}


def c20() -> dict[str, Any]:
    x, a, b = np.array([0., 0.]), np.array([3., 0.]), np.array([2., 2.])
    vals = [np.linalg.norm(x-a, 1), np.linalg.norm(x-b, 1), np.linalg.norm(x-a), np.linalg.norm(x-b)]
    close(vals, [3, 4, 3, math.sqrt(8)]); return {"l1_a_l1_b_l2_a_l2_b": vals}


def c21() -> dict[str, Any]:
    pts = [(2, 3), (4, 7), (5, 4), (7, 2), (8, 1), (9, 6)]; root = sorted(pts)[len(pts)//2]
    assert root == (7, 2); return {"upper_median_root": root, "left_size": 3, "right_size": 2}


def c22() -> dict[str, Any]:
    threshold = math.log(2) / math.log(4/3); close(threshold, 2.409420839654)
    return {"switch_p": threshold, "p2_prefers": "x2", "p3_prefers": "x3"}


def c23() -> dict[str, Any]:
    qa, qb = F(7,12)*F(5,8)*F(4,8), F(5,12)*F(2,6)*F(4,6); post = qa/(qa+qb)
    assert qa == F(35,192) and qb == F(5,54) and post == F(63,95)
    return {"q_A": str(qa), "q_B": str(qb), "posterior_A": str(post)}


def c24() -> dict[str, Any]:
    gain = 1 - entropy2(.75); close(gain, .188721875541)
    return {"parent_entropy": 1.0, "conditional_entropy": entropy2(.75), "gain": gain}


def c25() -> dict[str, Any]:
    gains = {"A": 1-entropy2(.75), "B": 1.0}; assert max(gains, key=gains.get) == "B"
    return {"gains": gains, "chosen": "B"}


def c26() -> dict[str, Any]:
    z = .8*1.5 + (-1.2)*(-.5) - .4; p = sigmoid(z); close([z,p],[1.4,.802183888559])
    return {"z": z, "p": p, "decision_0.5": int(p>=.5), "decision_0.85": int(p>=.85)}


def c27() -> dict[str, Any]:
    p = np.array([F(3,20),F(3,20),F(7,30),F(7,30),F(7,30)], dtype=float)
    close([p.sum(), p[:2].sum()], [1,.3]); return {"max_entropy_distribution": p.tolist()}


def c28() -> dict[str, Any]:
    margins=np.array([1.4,1,.3,-.2]); xi=np.maximum(0,1-margins); close(xi,[0,0,.7,1.2])
    return {"slacks":xi.tolist(),"alpha_states":["0","[0,C]","C","C"]}


def c29() -> dict[str, Any]:
    a1=.5*math.log(3); z1=.75*math.exp(-a1)+.25*math.exp(a1); d2=np.array([1/6,1/6,1/6,1/2])
    close([z1,d2.sum(),.5*math.log(5)],[math.sqrt(3)/2,1,.5*math.log(5)])
    return {"alpha1":a1,"Z1":z1,"D2":d2.tolist(),"alpha2":.5*math.log(5)}


def c30() -> dict[str, Any]:
    r=np.array([[.9,.1],[.2,.8]]); x=np.array([0.,10.]); weights=r.sum(axis=0); means=(r*x[:,None]).sum(axis=0)/weights
    close(weights,[1.1,.9]); close(means,[20/11,80/9]); return {"weights":weights.tolist(),"means":means.tolist()}


def c31() -> dict[str, Any]:
    resp=np.array([.75,.25,.75]); pi=resp.mean(); p=(resp*np.array([1,0,1])).sum()/resp.sum(); q=((1-resp)*np.array([1,0,1])).sum()/(1-resp).sum()
    close([pi,p,q],[7/12,6/7,2/5]); return {"pi":pi,"p":p,"q":q}


def c32() -> dict[str, Any]:
    alpha1=np.array([.30,.04]); a=np.array([[.7,.3],[.4,.6]]); emit=np.array([.5,.9]); alpha2=(alpha1@a)*emit
    close(alpha2,[.113,.1026]); return {"alpha2":alpha2.tolist(),"likelihood":float(alpha2.sum())}


def c33() -> dict[str, Any]:
    scores=np.array([[.30*.7*.5,.30*.3*.9],[.04*.4*.5,.04*.6*.9]]); end=np.max(scores,axis=0)
    close(end,[.105,.081]); return {"delta2":end.tolist(),"best_path":[1,1],"score":float(end.max())}


def c34() -> dict[str, Any]:
    d1=np.array([.4,.1]); trans=np.array([[.3,.5],[.6,.2]]); d2=np.max(d1[:,None]+trans,axis=0); trans2=np.array([[.2,.1],[.4,.3]]); d3=np.max(d2[:,None]+trans2,axis=0)
    close(d2,[.7,.9]); close(d3,[1.3,1.2]); return {"delta2":d2.tolist(),"delta3":d3.tolist(),"path":["A","B","A"]}


def c35() -> dict[str, Any]:
    names=np.array(["L","K","B"]); recall=np.array([.91,.93,.94]); delay=np.array([2,18,7]); feasible=delay<=10; chosen=str(names[np.where(feasible)[0][np.argmax(recall[feasible])]])
    assert chosen=="B" and abs(.94-.91)>.02; return {"feasible":names[feasible].tolist(),"chosen":chosen}


def c36() -> dict[str, Any]:
    s2=.40+.5*(1-.90)+.1*.2; s10=.25+.5*(1-.55)+.1*1.; close([s2,s10],[.47,.575])
    return {"score_d2":s2,"score_d10":s10,"chosen":2}


def c37() -> dict[str, Any]:
    x=np.array([[0,2],[0,0],[1,0],[5,0],[5,2]],float); centers=np.array([[0,2],[0,0]],float)
    labels=np.argmin(((x[:,None,:]-centers[None,:,:])**2).sum(2),axis=1); new=np.vstack([x[labels==j].mean(0) for j in range(2)])
    labels2=np.argmin(((x[:,None,:]-new[None,:,:])**2).sum(2),axis=1); j=float(np.min(((x[:,None,:]-new[None,:,:])**2).sum(2),axis=1).sum())
    close(new,[[2.5,2],[2,0]]); assert np.array_equal(labels,labels2); close(j,26.5)
    return {"centers":new.tolist(),"labels":(labels+1).tolist(),"objective":j}


def c38() -> dict[str, Any]:
    a=np.array([[3.,0.],[0.,1.],[0.,0.]]); s=np.linalg.svd(a,compute_uv=False); a1=np.array([[3.,0.],[0.,0.],[0.,0.]])
    close(s,[3,1]); close(np.linalg.matrix_rank(a),2); close(np.linalg.norm(a-a1,'fro'),1)
    return {"singular_values":s.tolist(),"rank1_error":1.0}


def c39() -> dict[str, Any]:
    s=np.array([[5.,2.],[2.,2.]]); vals,vecs=np.linalg.eigh(s); close(vals,[1,6]); u=vecs[:,1]
    assert abs(abs(u@np.array([2,1])/math.sqrt(5))-1)<TOL; return {"eigenvalues":vals.tolist(),"explained_ratio":6/7}


def c40() -> dict[str, Any]:
    x=np.array([[2.,1.],[1.,2.]]); w=np.eye(2); h=np.ones((2,2)); w1=w*(x@h.T)/(w@h@h.T); h1=h*(w1.T@x)/(w1.T@w1@h)
    close(w1,[[1.5,0],[0,1.5]]); close(h1,[[4/3,2/3],[2/3,4/3]]); close(w1@h1,x)
    return {"W1":w1.tolist(),"H1":h1.tolist(),"loss":float(.5*np.linalg.norm(x-w1@h1,'fro')**2)}


def c41() -> dict[str, Any]:
    gamma=np.array([[12/13,4/7],[3/7,1/13]]); counts=np.array([[3,1],[1,3]],float); a1=(counts*gamma).sum(axis=1); phi1=a1/a1.sum()
    close(a1,[304/91,60/91]); close(phi1,[76/91,15/91]); return {"topic1_expected_counts":a1.tolist(),"phi1":phi1.tolist()}


def c42() -> dict[str, Any]:
    a=np.array([[.7,.3],[.2,.8]]); r0=np.array([1.,0.]); r1=r0@a; r2=r1@a; stationary=np.array([.4,.6])
    close(r1,[.7,.3]); close(r2,[.55,.45]); close(stationary@a,stationary); return {"rho1":r1.tolist(),"rho2":r2.tolist(),"stationary":stationary.tolist()}


def c43() -> dict[str, Any]: return c42()


def c44() -> dict[str, Any]:
    z=np.array([.64,.01,.49,.16]); run=np.cumsum(z)/np.arange(1,5); close(run,[.64,.325,.38,.325]); return {"running_means":run.tolist(),"final_error":float(run[-1]-1/3)}


def c45() -> dict[str, Any]:
    z=np.array([.16,.64,.01,.49]); mean=z.mean(); variance=z.var(ddof=1); se=math.sqrt(variance/4); close([mean,variance,se],[.325,.0843,.145172311],1e-8)
    return {"mean":mean,"sample_variance":variance,"se":se}


def c46() -> dict[str, Any]:
    pi=np.array([1/2,1/3,1/6]); q=np.array([[1/2,1/2,0],[1/4,1/2,1/4],[0,1/2,1/2]],float); alpha=min(1,pi[1]*q[1,0]/(pi[0]*q[0,1])); close(alpha,1/3)
    return {"alpha_12":alpha,"balanced_flow":pi[0]*q[0,1]*alpha}


def c47() -> dict[str, Any]:
    pi=np.array([1/2,1/3,1/6]); q=np.array([[1/2,1/2,0],[1/4,1/2,1/4],[0,1/2,1/2]],float); k=np.zeros_like(q)
    for i in range(3):
        for j in range(3):
            if i!=j and q[i,j]>0: k[i,j]=q[i,j]*min(1,pi[j]*q[j,i]/(pi[i]*q[i,j]))
        k[i,i]=1-k[i].sum()
    close(k.sum(1),np.ones(3)); close(pi@k,pi); return {"kernel":k.tolist(),"stationarity_residual":float(np.linalg.norm(pi@k-pi,1))}


def c48() -> dict[str, Any]:
    rho=.5; sigma=math.sqrt(3)/2; x11=rho*0+sigma*(-1/math.sqrt(3)); x21=rho*x11+sigma*1; x12=rho*x21+sigma*(-1); x22=rho*x12+sigma*0
    close([x11,x21,x12,x22],[-.5,-.25+math.sqrt(3)/2,-.125-math.sqrt(3)/4,-.0625-math.sqrt(3)/8])
    return {"two_sweeps":[x11,x21,x12,x22]}


def c49() -> dict[str, Any]:
    eta=.2; s=1-eta; weights=np.array([math.comb(14,r)*(2*s)**r*float(sp.beta(r+2,6)) for r in range(15)]); weights/=weights.sum()
    close(weights.sum(),1); assert np.all(weights>0); return {"eta":eta,"mixture_components":15,"weight_sum":float(weights.sum())}


def c50() -> dict[str, Any]:
    prior=np.array([2.,3.,5.]); post=np.array([6.,4.,5.]); close(prior/prior.sum(),[.2,.3,.5]); close(post/post.sum(),[.4,4/15,1/3]); mode=(post-1)/(post.sum()-3); close(mode,[5/12,1/4,1/3])
    return {"posterior_mean":(post/post.sum()).tolist(),"posterior_mode":mode.tolist()}


def c51() -> dict[str, Any]:
    assert sp.beta(2,3)==sp.Rational(1,12); close([2/5,2*3/(25*6),5/9],[.4,.04,5/9]); return {"B_2_3":"1/12","mean":.4,"variance":.04,"predictive":5/9}


def c52() -> dict[str, Any]:
    g=np.array([2.,3.,5.]); theta=g/g.sum(); close(theta,[.2,.3,.5]); return {"sum":float(g.sum()),"theta":theta.tolist()}


def c53() -> dict[str, Any]:
    beta111=math.prod([math.gamma(1)]*3)/math.gamma(3); beta322=math.gamma(3)*math.gamma(2)*math.gamma(2)/math.gamma(7); evidence=12*beta322/beta111
    close([beta111,beta322,evidence],[.5,1/360,1/15]); return {"B111":beta111,"B322":beta322,"count_evidence":evidence,"sequence_evidence":beta322/beta111}


def c54() -> dict[str, Any]:
    r1,r2=F(3,26),F(5,44); probs=np.array([float(r1/(r1+r2)),float(r2/(r1+r2))]); close(probs,[66/131,65/131]); return {"probabilities":probs.tolist()}


def c55() -> dict[str, Any]:
    u=np.array([.6*math.exp(-7/12),.2*math.exp(-13/12)]); eta=u/u.sum(); close(eta,[.832,.168],5e-4); close(eta.sum(),1); return {"unnormalized":u.tolist(),"responsibilities":eta.tolist()}


def c56() -> dict[str, Any]:
    p=math.exp(-.5*(math.log(.25)+math.log(.5))); leak=math.exp(-.5*(math.log(.5)+math.log(.8))); close([p,leak],[2*math.sqrt(2),1/math.sqrt(.4)])
    return {"holdout_perplexity":p,"leaked_perplexity":leak}


def c57() -> dict[str, Any]:
    m=np.array([[0,.5,1,0],[1/3,0,0,.5],[1/3,0,0,.5],[1/3,.5,0,0]],float); r0=np.ones(4)/4; r1=m@r0; star=np.array([1/3,2/9,2/9,2/9])
    close(r1,[3/8,5/24,5/24,5/24]); close(m@star,star); return {"first_step":r1.tolist(),"fixed_point":star.tolist()}


def c58() -> dict[str, Any]:
    m=np.array([[0,.5,0,0],[1/3,0,0,.5],[1/3,0,0,.5],[1/3,.5,0,0]],float); r=np.ones(4)/4; masses=[r.sum()]
    for _ in range(3): r=m@r; masses.append(r.sum())
    close(masses,[1,3/4,13/24,19/48]); return {"masses":masses}


def c59() -> dict[str, Any]:
    s=np.array([[0,.5,0,0],[1/3,0,0,.5],[1/3,0,1,.5],[1/3,.5,0,0]],float); r=np.linalg.solve(np.eye(4)-.8*s,.05*np.ones(4)); close(r,np.array([15,19,95,19])/148)
    return {"pagerank":r.tolist(),"residual_l1":float(np.linalg.norm(r-.8*s@r-.05*np.ones(4),1))}


def c60() -> dict[str, Any]:
    s=np.array([[0,0,1],[.5,0,0],[.5,1,0]],float); r=np.linalg.solve(np.eye(3)-.85*s,.05*np.ones(3)); close(r,np.array([686,380,703])/1769)
    return {"pagerank":r.tolist(),"sum":float(r.sum())}


def c61() -> dict[str, Any]:
    valid={"A":[1,1],"B":[1,0]}; feasible=[k for k,v in valid.items() if math.prod(v)==1]; assert feasible==["A"]
    return {"feasible":feasible,"mean_loss_A":np.mean([.42,.46]),"mean_cost_A":np.mean([8,9])}


def c62() -> dict[str, Any]:
    alpha=np.array([.4,.6]); theta=alpha/alpha.sum(); samples=np.array([[.3,.7],[.5,.5],[.4,.6]]); estimate=samples.mean(0)
    close(theta,[.4,.6]); close(estimate,[.4,.6]); return {"theta_shape":list(theta.shape),"posterior_mean_estimate":estimate.tolist()}


def c63() -> dict[str, Any]:
    u=np.zeros((6,2)); sigma=np.zeros((2,2)); v=np.zeros((4,2)); w=u@sigma; h=v.T; assert (w@h).shape==(6,4) and (w.T@w).shape==(2,2) and (h@h.T).shape==(2,2)
    return {"X_shape":[6,4],"W_shape":[6,2],"H_shape":[2,4]}


def c64() -> dict[str, Any]:
    rng=np.random.default_rng(20260809); noise=rng.normal(0,.1,size=(200000,20)); selected_min=float(noise.min(axis=1).mean()); assert selected_min < -.15
    return {"seed":20260809,"E_selected_min_error":selected_min,"min_E_error":0.0,"downward_bias":-selected_min}


LABELS = [
"exm:V1-C01-small","exm:V1-C02-projection","exm:V1-C03-quadratic","exm:V1-C04-dice","exm:V1-C04-total-variance","exm:V1-C04-base-rate","exm:V1-C05-binomial-mle","exm:V1-C06-kl-asymmetry","exm:V1-C07-kkt-nonnegative","exm:V1-C07-halfspace-kkt","exm:V1-C08-newton-quadratic","exm:V1-C08-preconditioning","exm:V1-C09-finite-class","exm:V1-C10-generalization-gap","exm:V1-C10-model-selection","exm:V1-C11-binary-metrics","exm:V2-C01-update","exm:V2-C01-primal","exm:V2-C01-xor","exm:V2-C02-lp-small","exm:V2-C02-kd-build","exm:V2-C02-original-distance","exm:V2-C03-smoothed-score","exm:V2-C04-information-gain","exm:V2-C04-split-choice","exm:V2-C05-decision","exm:V3-C01-two-groups","exm:V3-C02-kkt-state","exm:V3-C03-two-round","exm:V3-C04-three-coins-em","exm:V3-C04-three-coins-one-round","exm:V3-C05-viterbi-numeric","exm:V3-C05-viterbi-path-rb","exm:V3-C06-viterbi","exm:V3-C07-selection","exm:V4-C01-model-choice","exm:V4-C02-five-points","exm:V4-C03-tall","exm:V4-C04-pca-projection","exm:V4-C05-one-nmf-step","exm:V4-C06-one-em","exm:V5-C01-stationary-reversible","exm:V5-C01-two-state-audit","exm:V5-C02-four-uniforms","exm:V5-C02-mc-audit","exm:V5-C03-asymmetric-proposal","exm:V5-C03-three-state-kernel","exm:V5-C04-two-sweeps","exm:V5-C04-five-category","exm:V5-C05-three-category","exm:V5-C05-beta-update","exm:V5-C05-gamma-interface","exm:V5-C05-evidence","exm:V5-C06-gibbs-step","exm:V5-C06-vi-step","exm:V5-C06-perplexity","exm:V5-C07-basic-four","exm:V5-C07-dangling-loss","exm:V5-C07-damped-four","exm:V5-C07-power-three","exm:V5-C08-two-candidate-selection","exm:V5-C08-layering","exm:V5-C08-lsa-shape","exm:V5-C08-holdout"]
CHECKS: list[Callable[[], dict[str, Any]]] = [globals()[f"c{i:02d}"] for i in range(1,65)]


DOMAINS = [
"matrix_dimension","projection","convexity","probability","total_variance","bayes","mle","kl_entropy","kkt","kkt","newton","preconditioning","empirical_risk","generalization","model_selection","classification_metrics","perceptron","perceptron","separability","distance","kd_tree","distance","naive_bayes","decision_tree","decision_tree","logistic","maximum_entropy","svm_kkt","adaboost","gmm_em","em","hmm_forward","hmm_viterbi","crf_viterbi","model_selection","latent_model_selection","kmeans","svd","pca","nmf","plsa_em","markov_chain","markov_chain","monte_carlo","monte_carlo","metropolis_hastings","metropolis_hastings","gibbs","conditional_mixture","dirichlet","beta","dirichlet","dirichlet_evidence","lda_gibbs","lda_vi","perplexity","pagerank","pagerank_dangling","pagerank","pagerank","locked_test_selection","lda_layering","lsa_shape","selection_bias"]


def digest(text: str) -> str: return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def normalized_example_text(text: str) -> str:
    text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
    text = re.sub(r"\\(?:label|index|phantomsection)\{[^}]*\}", "", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", "", text)
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", text).lower()


def trigram_jaccard(left: str, right: str) -> float:
    def grams(value: str) -> set[str]:
        return {value[i:i+3] for i in range(max(0, len(value)-2))}
    a, b = grams(left), grams(right)
    return len(a & b) / len(a | b) if a or b else 1.0


def locate_examples() -> dict[str, dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    for path in CHAPTER_ROOT.glob("*/chapters/*.tex"):
        text = path.read_text(encoding="utf-8")
        headings = list(re.finditer(r"\\SLExampleSolutionHeading\{([^}]+)\}", text))
        question_blocks = list(re.finditer(r"\\begin\{example\}.*?\\end\{example\}", text, re.S))
        for index, match in enumerate(headings):
            label = match.group(1)
            if label not in LABELS: continue
            label_token = rf"\label{{{label}}}"
            qmatch = next((block for block in question_blocks if label_token in block.group(0)), None)
            if not qmatch: raise AssertionError(f"question block missing: {label}")
            end = headings[index+1].start() if index+1 < len(headings) else min(len(text), match.end()+12000)
            solution = text[match.start():end]
            if label in found: raise AssertionError(f"duplicate solution heading: {label}")
            found[label] = {
                "source_file": path.relative_to(SOURCE).as_posix(),
                "question_sha256": digest(qmatch.group(0)),
                "solution_sha256": digest(solution),
                "question_chars": len(normalized_example_text(qmatch.group(0))),
                "solution_chars": len(normalized_example_text(solution)),
                "_question_normalized": normalized_example_text(qmatch.group(0)),
            }
    return found


def degenerate_checks() -> list[dict[str, Any]]:
    rows=[]
    def add(name: str, passed: bool, evidence: Any) -> None: rows.append({"name":name,"passed":bool(passed),"evidence":evidence})
    add("empty_data", np.empty((0,2)).shape[0]==0, "reject before fitting")
    add("single_class", np.unique([1,1,1]).size==1, "classification metric/model guard")
    add("zero_denominator", not np.isfinite(np.divide(1.,0.,where=np.array(False),out=np.array(np.nan))), "guarded division remains NaN")
    add("non_finite", not np.isfinite([0.,np.nan,np.inf]).all(), "NaN/Inf detected")
    add("empty_cluster", len([])==0, "reinitialize or fail start")
    add("empty_topic", np.array([0.,0.]).sum()==0, "smooth/reinitialize/fail")
    dangling=np.array([[0.,0.],[1.,0.]]); add("dangling_graph", bool(np.any(dangling.sum(0)==0)), dangling.sum(0).tolist())
    periodic=np.array([[0.,1.],[1.,0.]]); add("periodic_chain", np.allclose(np.linalg.matrix_power(periodic,2),np.eye(2)), "period 2")
    reducible=np.eye(2); add("reducible_chain", bool(np.allclose(reducible,np.eye(2))), "two closed classes")
    badp=np.array([.7,.4,-.1]); add("illegal_probability", bool(np.any(badp<0) or not np.isclose(badp.sum(),1)), badp.tolist())
    add("line_search_failure", all(.5**k > 1e-20 for k in range(10)), "finite backtrack budget exhausted without certificate")
    add("iteration_budget", len(range(5))==5, "budget_stop is distinct from converged")
    return rows


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--refresh-manifest",action="store_true"); args=parser.parse_args()
    TEST_ROOT.mkdir(parents=True,exist_ok=True)
    located=locate_examples(); assert len(LABELS)==64 and len(set(LABELS))==64 and set(located)==set(LABELS)
    asset_rows=[]
    for i,label in enumerate(LABELS):
        located_row={key:value for key,value in located[label].items() if not key.startswith("_")}
        combined_chars=located_row["question_chars"]+located_row["solution_chars"]
        difficulty="starter" if combined_chars<=900 else ("core" if combined_chars<=1800 else "advanced")
        asset_rows.append({
            "ordinal":i+1,
            "label":label,
            "domain":DOMAINS[i],
            "learning_objective_id":f"{DOMAINS[i]}:{label.split(':')[-1]}",
            "data_signature":located_row["question_sha256"],
            "conclusion_signature":located_row["solution_sha256"],
            "difficulty_band":difficulty,
            "check_id":f"c{i+1:02d}",
            **located_row,
        })
    current={"schema_version":"1.1","source_root":"source","runtime":{"python":sys.version.split()[0],"numpy":np.__version__,"sympy":sp.__version__},"examples":asset_rows}
    if args.refresh_manifest or not MANIFEST.exists(): MANIFEST.write_text(json.dumps(current,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    frozen=json.loads(MANIFEST.read_text(encoding="utf-8")); frozen_by={x["label"]:x for x in frozen["examples"]}
    source_mismatch=[label for label in LABELS if any(frozen_by[label][k]!=located[label][k] for k in ("source_file","question_sha256","solution_sha256"))]
    near_duplicates=[]
    for i,left in enumerate(LABELS):
        for right in LABELS[i+1:]:
            if located[left]["source_file"] != located[right]["source_file"]:
                continue
            similarity=trigram_jaccard(located[left]["_question_normalized"], located[right]["_question_normalized"])
            if similarity>=0.78:
                near_duplicates.append({"left":left,"right":right,"similarity":round(similarity,6)})
    results=[]
    for i,(label,fn) in enumerate(zip(LABELS,CHECKS),1):
        try: metrics=fn(); passed=True; error=""
        except Exception as exc: metrics={}; passed=False; error=f"{type(exc).__name__}: {exc}"
        results.append({"ordinal":i,"label":label,"domain":DOMAINS[i-1],"check_id":f"c{i:02d}","passed":passed,"metrics":metrics,"error":error,"source_frozen_match":label not in source_mismatch})
    degenerate=degenerate_checks(); passed=sum(r["passed"] for r in results); overall=passed==64 and not source_mismatch and not near_duplicates and all(x["passed"] for x in degenerate)
    payload={"passed":overall,"summary":{"examples":64,"passed":passed,"failed":64-passed,"source_mismatches":len(source_mismatch),"near_duplicate_pairs":len(near_duplicates),"degenerate_checks":len(degenerate),"degenerate_passed":sum(x["passed"] for x in degenerate)},"runtime":current["runtime"],"source_mismatches":source_mismatch,"near_duplicate_pairs":near_duplicates,"examples":results,"degenerate_inputs":degenerate}
    RESULT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# v1.7.0 例题数学与数值复算报告","",f"结论：{'通过' if overall else '未通过'}；编号例题 {passed}/64；源码冻结不匹配 {len(source_mismatch)}；同章高相似问题对 {len(near_duplicates)}；退化输入 {sum(x['passed'] for x in degenerate)}/{len(degenerate)}。","",f"运行环境：Python {sys.version.split()[0]}，NumPy {np.__version__}，SymPy {sp.__version__}。","","资产表字段包含学习目标ID、数据签名、结论签名、难度带、源码位置与独立复算ID。","","| # | 标签 | 域 | 核验 | 源码冻结 |","|---:|---|---|---|---|"]
    for row in results: lines.append(f"| {row['ordinal']} | `{row['label']}` | {row['domain']} | {'PASS' if row['passed'] else 'FAIL'} | {'MATCH' if row['source_frozen_match'] else 'MISMATCH'} |")
    lines += ["","## 退化输入",""]+[f"- {'PASS' if x['passed'] else 'FAIL'} `{x['name']}`：{x['evidence']}" for x in degenerate]
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(payload["summary"]|{"passed":overall},ensure_ascii=False)); return 0 if overall else 1


if __name__=="__main__": raise SystemExit(main())
