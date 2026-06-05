from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Union

from ast_nodes import ForStmtNode, IntLiteralNode, PrintStmtNode, ProgramNode

IntOrNone = Optional[int]


@dataclass(frozen=True)
class TacInstr:

    op: str
    arg1: str = ""
    arg2: str = ""
    result: str = ""

    def to_quad_row(self) -> Tuple[str, str, str, str]:
        if self.op == "label":
            return ("label", "", "", self.result)
        if self.op == "print":
            return ("print", self.arg1, "", "")
        if self.op == "if_le":
            return ("if_<=", self.arg1, self.arg2, self.result)
        if self.op in ("+", "-", "*", "/"):
            return (self.op, self.arg1, self.arg2, self.result)
        if self.op == "=":
            return ("=", self.arg1, "", self.result)
        if self.op == "goto":
            return ("goto", "", "", self.result)
        return (self.op, self.arg1, self.arg2, self.result)

    def format_line(self, index: int) -> str:
        if self.op == "label":
            return f"{index:3d}  {self.result}:"
        if self.op == "print":
            return f"{index:3d}  print {self.arg1}"
        if self.op == "goto":
            return f"{index:3d}  goto {self.result}"
        if self.op == "if_le":
            return f"{index:3d}  if {self.arg1} <= {self.arg2} goto {self.result}"
        if self.op in ("+", "-", "*", "/"):
            return f"{index:3d}  {self.result} = {self.arg1} {self.op} {self.arg2}"
        if self.op == "=":
            if self.arg1 and not self.arg2:
                return f"{index:3d}  {self.result} = {self.arg1}"
            return f"{index:3d}  {self.result} = {self.arg1}"
        return f"{index:3d}  {self.op} {self.arg1} {self.arg2} {self.result}".strip()


def format_tac(ir: Sequence[TacInstr]) -> str:
    if not ir:
        return ""
    return "\n".join(instr.format_line(i + 1) for i, instr in enumerate(ir))


def tac_to_quad_rows(ir: Sequence[TacInstr]) -> List[Tuple[str, str, str, str]]:
    return [instr.to_quad_row() for instr in ir]


def _int_from_literal(node) -> IntOrNone:
    if isinstance(node, IntLiteralNode):
        return int(node.value)
    return None


def collect_for_nodes(program: ProgramNode) -> List[ForStmtNode]:
    found: List[ForStmtNode] = []

    def walk(node) -> None:
        if isinstance(node, ForStmtNode):
            found.append(node)
            for st in node.body:
                walk(st)
        elif isinstance(node, PrintStmtNode):
            return

    for stmt in program.body:
        walk(stmt)
    return found


def generate_for_tac(node: ForStmtNode) -> List[TacInstr]:
    var = node.loop_var
    m = _int_from_literal(node.range_start)
    n = _int_from_literal(node.range_end)
    if m is None or n is None:
        return []

    ir: List[TacInstr] = []
    ir.append(TacInstr("=", str(m), "", "__m"))
    ir.append(TacInstr("=", str(n), "", "__n"))
    ir.append(TacInstr("-", "__n", "__m", "__t_sub"))
    ir.append(TacInstr("+", "__t_sub", "1", "__trip"))
    ir.append(TacInstr("=", "__m", "", var))

    ir.append(TacInstr("label", "", "", "L_body"))
    for stmt in node.body:
        ir.extend(_body_stmt_tac(stmt, var))
    ir.append(TacInstr("+", var, "1", "__t_inc"))
    ir.append(TacInstr("=", "__t_inc", "", var))
    ir.append(TacInstr("label", "", "", "L_cond"))
    ir.append(TacInstr("if_le", var, "__n", "L_body"))
    return ir


def _body_stmt_tac(stmt, loop_var: str) -> List[TacInstr]:
    if isinstance(stmt, PrintStmtNode):
        arg = stmt.argument
        name = getattr(arg, "name", loop_var) if arg else loop_var
        return [TacInstr("print", name, "", "")]
    if isinstance(stmt, ForStmtNode):
        return []
    return []


def _try_parse_int(s: str) -> IntOrNone:
    s = (s or "").strip()
    if not s or not s.lstrip("-").isdigit():
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _is_compile_temp(name: str) -> bool:
    return (name or "").startswith("__")


def optimize_constant_fold(ir: Sequence[TacInstr]) -> List[TacInstr]:
    out: List[TacInstr] = []
    env: dict[str, int] = {}

    def resolve(name: str) -> IntOrNone:
        v = _try_parse_int(name)
        if v is not None:
            return v
        if name in env:
            return env[name]
        return None

    for ins in ir:
        if ins.op == "=":
            v = _try_parse_int(ins.arg1)
            if v is not None:
                if _is_compile_temp(ins.result):
                    env[ins.result] = v
                out.append(TacInstr("=", str(v), "", ins.result))
                continue
            if ins.arg1 in env:
                v = env[ins.arg1]
                if _is_compile_temp(ins.result):
                    env[ins.result] = v
                out.append(TacInstr("=", str(v), "", ins.result))
                continue
            out.append(ins)
            continue

        if ins.op in ("+", "-", "*", "/"):
            if not _is_compile_temp(ins.result):
                out.append(ins)
                continue
            a = resolve(ins.arg1)
            b = resolve(ins.arg2)
            if a is not None and b is not None:
                if ins.op == "+":
                    val = a + b
                elif ins.op == "-":
                    val = a - b
                elif ins.op == "*":
                    val = a * b
                else:
                    val = a // b if b != 0 else 0
                env[ins.result] = val
                out.append(TacInstr("=", str(val), "", ins.result))
                continue
            out.append(ins)
            continue

        if ins.op == "if_le" and ins.arg2 in env:
            out.append(TacInstr("if_le", ins.arg1, str(env[ins.arg2]), ins.result))
            continue

        out.append(ins)
    return out


def optimize_remove_inc_temp(ir: Sequence[TacInstr]) -> List[TacInstr]:
    out: List[TacInstr] = []
    i = 0
    while i < len(ir):
        ins = ir[i]
        if (
            i + 1 < len(ir)
            and ins.op == "+"
            and ir[i + 1].op == "="
            and ir[i + 1].arg1 == ins.result
            and ir[i + 1].result == ins.arg1
            and ins.arg2 == "1"
        ):
            out.append(TacInstr("+", ins.arg1, "1", ins.arg1))
            i += 2
            continue
        out.append(ins)
        i += 1
    return out


def optimize_canonicalize_range_copy(ir: Sequence[TacInstr]) -> List[TacInstr]:
    env: dict[str, int] = {}
    for ins in ir:
        if ins.op == "=" and _try_parse_int(ins.arg1) is not None:
            env[ins.result] = int(ins.arg1)

    m, n, trip = env.get("__m"), env.get("__n"), env.get("__trip")
    if m is None or n is None:
        return list(ir)

    drop = frozenset({"__m", "__n", "__t_sub"})
    out: List[TacInstr] = []
    if trip is not None:
        out.append(TacInstr("=", str(trip), "", "__trip"))

    for ins in ir:
        if ins.result in drop or ins.arg1 in drop or ins.arg2 in drop:
            continue
        if ins.result == "__trip":
            continue
        if ins.op == "=" and ins.arg1 == "__m" and not _is_compile_temp(ins.result):
            out.append(TacInstr("=", str(m), "", ins.result))
            continue
        if ins.op == "if_le" and ins.arg2 == "__n":
            out.append(TacInstr("if_le", ins.arg1, str(n), ins.result))
            continue
        out.append(ins)
    return out


def build_for_ir_pipeline(node: ForStmtNode) -> Tuple[List[TacInstr], List[TacInstr], List[TacInstr]]:
    raw = generate_for_tac(node)
    folded = optimize_constant_fold(raw)
    folded = optimize_canonicalize_range_copy(folded)
    final = optimize_remove_inc_temp(folded)
    return raw, folded, final


def format_ir_report(
    node: ForStmtNode,
    *,
    header_for: str,
    title_input: str,
    title_opt1: str,
    title_opt2: str,
) -> str:
    raw, folded, final = build_for_ir_pipeline(node)
    if not raw:
        return ""
    parts = [
        header_for,
        "",
        title_input,
        format_tac(raw),
        "",
        title_opt1,
        format_tac(folded),
        "",
        title_opt2,
        format_tac(final),
    ]
    return "\n".join(parts)


def demo_ir_report(node: ForStmtNode) -> str:
    m = _int_from_literal(node.range_start)
    n = _int_from_literal(node.range_end)
    return format_ir_report(
        node,
        header_for=f"for ({node.loop_var} in {m}:{n}) {{ … }}",
        title_input="Входной IR",
        title_opt1="Оптимизация 1: свёртка констант (range, __trip)",
        title_opt2="Оптимизация 2: прямой инкремент i = i + 1",
    )
