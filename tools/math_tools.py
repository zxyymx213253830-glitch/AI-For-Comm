# -*- coding: utf-8 -*-
"""
符号数学工具（SymPy）—— 供数学/校验等 Agent 独立复核推导

覆盖：化简、展开、求解、积分、求导、极限、级数、数值代入、恒等式验证。
所有表达式用 Python 语法（sympify 自动识别常用函数）。
"""
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
)

from tools.registry import tool

_TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

# 常用符号与环境函数：表达式里直接写 x, y, z, t, f, sigma, Q 函数等
_ENV = {
    n: sp.Symbol(n) for n in
    ("x y z t u v w a b c d k n m p q r s f g h alpha beta gamma delta "
     "epsilon sigma mu omega theta phi psi rho tau x0 y0 Eb N0 B W SNR SINR").split()
}
_ENV.update({
    "exp": sp.exp, "log": sp.log, "ln": sp.log, "sqrt": sp.sqrt,
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "erf": sp.erf, "erfc": sp.erfc, "abs": sp.Abs, "Abs": sp.Abs,
    "factorial": sp.factorial, "gamma": sp.gamma,
    "pi": sp.pi, "E": sp.E, "oo": sp.oo, "zoo": sp.zoo, "I": sp.I,
    "Q": lambda e: sp.Rational(1, 2) * sp.erfc(sp.sqrt(e)),  # 标准 Q(x) 以能量自变量近似
    "binom": sp.binomial, "Qfunc": lambda x: sp.erfc(x) / 2,
})


def _parse(expr: str):
    return parse_expr(expr, local_dict=_ENV, transformations=_TRANSFORMS,
                      evaluate=True)


def _symbols(var: str):
    """把 "x" 或 "x,t" 解析成符号元组。"""
    return tuple(sp.Symbol(v.strip()) for v in str(var).split(",") if v.strip())


@tool(
    "sympy_compute",
    "符号数学计算：化简/展开/求解方程/定积分/不定积分/求导/极限/泰勒级数/数值代入",
    {"op": "操作，取 simplify|expand|solve|integrate|definite_integrate|diff|limit|series|evalf",
     "expression": "表达式，如 exp(-x**2) 或 x**2-5*x+6（方程求解时写 x**2-5*x+6=0）",
     "var": "变量名，如 x；多变量求导用逗号分隔顺序如 x,t",
     "extra": "补充参数：definite_integrate 写 '下限,上限'（如 0,oo）；limit 写 '点,方向'（如 0,+）；series 写 '展开点,阶数'（如 0,5）；其余留空"},
)
def sympy_compute(op: str, expression: str, var: str = "x", extra: str = ""):
    op = str(op).strip().lower()
    # 含等号的方程（solve 场景）先拆成 左-右 再解析，避免 parse 报错
    if "=" in str(expression) and op in ("solve", "evalf"):
        lhs, rhs = str(expression).split("=", 1)
        expr = _parse(lhs) - _parse(rhs)
    else:
        expr = _parse(expression)
    syms = _symbols(var) if var else ()
    x = syms[0] if syms else sp.Symbol("x")

    if op == "simplify":
        out = sp.simplify(expr)
    elif op == "expand":
        out = sp.expand(expr)
    elif op == "solve":
        sol = sp.solve(expr, *syms) if syms else sp.solve(expr)
        return {"解": str(sol), "说明": f"方程 {expression} 关于 {var} 的解"}
    elif op == "integrate":
        out = sp.integrate(expr, x)
    elif op == "definite_integrate":
        lo, _, hi = str(extra).partition(",")
        out = sp.integrate(expr, (x, _parse(lo.strip()), _parse(hi.strip())))
    elif op == "diff":
        out = sp.diff(expr, *syms) if len(syms) > 1 else sp.diff(expr, x)
    elif op == "limit":
        pt, _, direction = str(extra).partition(",")
        out = sp.limit(expr, x, _parse(pt.strip() or "0"),
                       direction.strip() or "+")
    elif op == "series":
        pt, _, order = str(extra).partition(",")
        out = sp.series(expr, x, _parse(pt.strip() or "0"),
                        int(order.strip() or 5)).removeO()
    elif op == "evalf":
        out = sp.N(expr, 12)
    else:
        raise ValueError(f"不支持的操作「{op}」，可选：simplify/expand/solve/integrate/"
                         f"definite_integrate/diff/limit/series/evalf")

    return {
        "结果": str(out),
        "LaTeX": sp.latex(out),
        "数值近似": str(sp.N(out, 8)) if out.is_number else "",
    }


@tool(
    "sympy_check_equality",
    "验证两个表达式是否恒等（数学推导交叉复核专用），返回成立/不成立及差式化简结果",
    {"left": "左边表达式，如 0.5*erfc(sqrt(x))",
     "right": "右边表达式，如 (1-sqrt(x/(1+x)))/2"},
)
def sympy_check_equality(left: str, right: str):
    a, b = _parse(left), _parse(right)
    diff = sp.simplify(a - b)
    equal = diff == 0 or diff.equals(0) is True
    return {
        "恒等": bool(equal),
        "差式化简": str(diff),
        "结论": "两式恒等（推导正确）" if equal
                else "两式不恒等，请检查推导（上方为化简后的差）",
    }
