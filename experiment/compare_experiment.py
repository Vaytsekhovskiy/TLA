"""Compare a completed Ollama run against Gold using TLC and its DOT graphs."""

import argparse
import json
import re
import shutil
from pathlib import Path

from run_experiment import DATASET, TASKS, save_json, verify


GOLD_VARIABLES = {
    "ConfigParams": ("x", "y", "z", "w"),
    "Test1623": ("x",),
    "Bug2750": ("buffer", "waitP", "waitC"),
    "test10": ("x",),
}
NODE = re.compile(r'^(-?\d+) \[label=("(?:(?:\\.)|[^"\\])*")([^\n]*)$', re.MULTILINE)
EDGE = re.compile(r"^(-?\d+) -> (-?\d+) ", re.MULTILINE)


def read_graph(path, variables, expected_size):
    """Read TLC labels in a common variable order, independently of fingerprints."""
    dot = path.read_text(encoding="utf-8")
    states = {}
    initial = set()
    for node, label, attributes in NODE.findall(dot):
        assignments = {}
        for line in json.loads(label).splitlines():
            name, value = line.removeprefix("/\\ ").split(" = ", 1)
            assignments[name] = value
        state = tuple(assignments[name] for name in variables)
        states[node] = state
        if "style = filled" in attributes:
            initial.add(state)
    if len(states) != expected_size or not initial:
        raise ValueError(f"Unexpected node count or missing initial state: {path}")
    edges = {(states[source], states[target]) for source, target in EDGE.findall(dot)}
    return {"initial": initial, "states": set(states.values()), "edges": edges}


def graph_delta(gold, model):
    result = {}
    for kind, gold_values in gold.items():
        model_values = model[kind]
        missing = gold_values - model_values
        extra = model_values - gold_values
        result[kind] = {
            "gold": len(gold_values),
            "model": len(model_values),
            "gold_only": len(missing),
            "model_only": len(extra),
            "gold_only_example": min(missing, default=None),
            "model_only_example": min(extra, default=None),
        }
    return result


def check_refinement(java, folder, source, target, cfg, variables, temporal, instance):
    """Run a specification and check target behavior on the same state variables."""
    folder.mkdir()
    for module in (source, target):
        shutil.copyfile(module, folder / module.name)
    name = f"{source.stem}Against{target.stem}"
    property_name = f"{instance}Spec"
    module = folder / f"{name}.tla"
    config = folder / f"{name}.cfg"
    substitution = ", ".join(f"{other} <- {local}" for other, local in variables.items())
    state_tuple = "<<" + ", ".join(variables.values()) + ">>"
    expression = (
        f"{instance}!Spec" if temporal
        else f"{instance}!Init /\\ [][{instance}!Next]_{state_tuple}"
    )
    module.write_text(
        f"---- MODULE {name} ----\n"
        f"EXTENDS {source.stem}\n\n"
        f"{instance} == INSTANCE {target.stem} WITH {substitution}\n"
        f"{property_name} == {expression}\n"
        "====\n",
        encoding="utf-8",
    )
    config.write_text(
        cfg.read_text(encoding="utf-8").rstrip() + f"\n\nPROPERTY {property_name}\n",
        encoding="utf-8",
    )
    status, _ = verify(java, module, config, folder)
    return status


def compare_task(java, run, output, name, spec_id, aliases):
    key = f"{spec_id}_{name}"
    result_dir = output / key
    gold_dir = result_dir / "gold"
    gold_dir.mkdir(parents=True)
    gold = gold_dir / f"{name}.tla"
    cfg = gold_dir / f"{name}.cfg"
    for target in (gold, cfg):
        shutil.copyfile(DATASET / "specs" / "gold" / f"{spec_id}_{target.name}", target)
    gold_graph = gold_dir / "graph.dot"
    gold_status, _ = verify(java, gold, cfg, gold_dir, dump=gold_graph)
    result = {"gold": gold_status}

    candidate_dir = run / key
    candidate = candidate_dir / f"{name}LLM.tla"
    if not candidate.is_file():
        return result

    candidate_cfg = candidate_dir / cfg.name
    if candidate_cfg.read_bytes() != cfg.read_bytes():
        raise ValueError(f"Different TLC configurations for {key}")
    generation = json.loads((candidate_dir / "result.json").read_text(encoding="utf-8"))
    attempt = generation["attempts"][-1]
    attempt_dir = candidate_dir / f"{attempt['iteration']:02}"
    if not attempt["tlc"] or candidate.read_bytes() != (attempt_dir / candidate.name).read_bytes():
        raise ValueError(f"Candidate differs from the successful attempt for {key}")

    variables = {var: aliases.get(var, var) for var in GOLD_VARIABLES[name]}
    uses_spec = name == "Bug2750"
    result["variable_map"] = variables
    result["model"] = attempt
    result["gold_property"] = check_refinement(
        java, result_dir / "model_against_gold", candidate, gold, cfg, variables, uses_spec, "Gold",
    )
    result["model_property"] = check_refinement(
        java, result_dir / "gold_against_model", gold, candidate, cfg,
        {model: gold for gold, model in variables.items()}, uses_spec, "Model",
    )
    if gold_status["metrics"] and attempt["metrics"]:
        result["graph"] = graph_delta(
            read_graph(gold_graph, variables, gold_status["metrics"]["distinct"]),
            read_graph(attempt_dir / "graph.dot", variables.values(), attempt["metrics"]["distinct"]),
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--java", default="java")
    parser.add_argument("--aliases", type=Path, help="JSON mapping module names to Gold-to-model variable maps")
    args = parser.parse_args()
    java = shutil.which(args.java)
    if java is None:
        parser.error(f"Java executable not found: {args.java}")
    aliases = json.loads(args.aliases.read_text(encoding="utf-8")) if args.aliases else {}
    output = args.output.resolve()
    output.mkdir(parents=True)
    summary = {}
    for name, (spec_id, _, _) in TASKS.items():
        summary[name] = compare_task(java, args.run.resolve(), output, name, spec_id, aliases.get(name, {}))
        save_json(output / "results.json", summary)
        print(name, summary[name].get("gold_property"), flush=True)


if __name__ == "__main__":
    main()
