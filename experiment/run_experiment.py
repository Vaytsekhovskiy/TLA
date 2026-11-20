"""Generate four benchmark modules with one local Ollama model and run SANY/TLC."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


EXPERIMENT = Path(__file__).resolve().parent
CHECKOUT = EXPERIMENT.parent / "dataset_release"
DATASET = CHECKOUT / "dataset_release"
TASKS = {
    "ConfigParams": (92, "basic", "declarative_claude"),
    "Test1623": (239, "basic", "declarative_claude"),
    "Bug2750": (67, "intermediate", "declarative_claude"),
    "test10": (352, "intermediate", "declarative_gpt"),
}
OLLAMA = "http://127.0.0.1:11434"
ITERATIONS = 10
METRICS = re.compile(
    r"([0-9,]+) states generated, ([0-9,]+) distinct states found.*?depth of "
    r"(?:the complete state graph search )?is ([0-9,]+)", re.DOTALL
)


def save_json(path, data):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def ollama(path, data=None):
    request = Request(
        OLLAMA + path,
        data=None if data is None else json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=600) as response:
        return json.load(response)


def verify(java, module, config, logs, *, dump=None):
    """Run SANY, then run TLC only if SANY accepts the module."""
    logs.mkdir(parents=True, exist_ok=True)
    java_command = [java, "-Dfile.encoding=UTF-8", "-XX:+UseParallelGC", "-cp",
                    str(CHECKOUT / "tla2tools.jar")]

    def run(name, args, timeout):
        command = [*java_command, *args]
        try:
            result = subprocess.run(
                command, cwd=module.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace", timeout=timeout, check=False,
            )
            output = result.stdout
            code = result.returncode
        except subprocess.TimeoutExpired as error:
            partial = error.stdout or b""
            output = partial.decode("utf-8", errors="replace") if isinstance(partial, bytes) else partial
            output += f"\nTimed out after {timeout} seconds.\n"
            code = None
        (logs / f"{name}.txt").write_text(output, encoding="utf-8")
        save_json(logs / f"{name}-command.json", {"argv": command, "cwd": str(module.parent), "exit": code})
        return code, output

    sany_code, sany = run("sany", ["tla2sany.SANY", module.name], 25)
    accepted = (
        sany_code == 0
        and f"Semantic processing of module {module.stem}" in sany
        and not re.search(r"(?im)\*\*\*\s+(?:Fatal )?Errors\s*:|^Parse Error|^Fatal errors", sany)
    )
    status = {"sany": accepted, "sany_exit": sany_code, "tlc": None, "metrics": None}
    if not accepted:
        return status, sany

    args = [
        "tlc2.TLC", "-workers", "1", "-fp", "0", "-noGenerateSpecTE",
        "-metadir", str(logs / "states"), "-config", str(config),
    ]
    if dump is not None:
        args.extend(["-dump", "dot", str(dump)])
    tlc_code, tlc = run("tlc", [*args, module.name], 45)
    success = tlc_code == 0 and "Model checking completed. No error has been found." in tlc
    metrics = METRICS.search(tlc) if success else None
    status.update(tlc=success, tlc_exit=tlc_code)
    if metrics:
        status["metrics"] = dict(zip(
            ("total", "distinct", "depth"),
            (int(number.replace(",", "")) for number in metrics.groups()),
        ))
    return status, "" if success else tlc


def extract_module(response):
    header = re.search(r"(?m)^[ \t]*-{4,}[ \t]+MODULE\b[^\n]*", response)
    if not header:
        return response
    body = response[header.start():]
    end = re.search(r"(?m)^[ \t]*={4,}[ \t]*$", body)
    return body[:end.end()] + "\n" if end else body


def check_answer(java, response, name, attempt, cfg, number):
    answer = response["message"]["content"] if "message" in response else response["response"]
    (attempt / "response.txt").write_text(answer, encoding="utf-8")
    module = attempt / f"{name}LLM.tla"
    module.write_text(extract_module(answer), encoding="utf-8")
    status, diagnostics = verify(java, module, cfg, attempt, dump=attempt / "graph.dot")
    status.update(iteration=number, done_reason=response.get("done_reason"))
    return status, diagnostics, module


def generate(java, model, output, name, task, think, endpoint, options):
    spec_id, level, description_kind = task
    task_dir = output / f"{spec_id}_{name}"
    task_dir.mkdir(exist_ok=True)
    result_path = task_dir / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {
        "id": spec_id, "level": level, "description": description_kind, "attempts": [],
    }
    cfg = task_dir / f"{name}.cfg"
    pending = task_dir / f"{len(result['attempts']) + 1:02}"
    if (pending / "request.json").exists():
        if (pending / "response.json").exists():
            response = json.loads((pending / "response.json").read_text(encoding="utf-8"))
            status, _, module = check_answer(
                java, response, name, pending, cfg, len(result["attempts"]) + 1,
            )
            if status["tlc"]:
                shutil.copyfile(module, task_dir / module.name)
        else:
            save_json(pending / "api-error.json", {"error": "Run interrupted before a full response was saved"})
            status = {
                "iteration": len(result["attempts"]) + 1, "sany": None, "tlc": None,
                "metrics": None, "done_reason": "interrupted",
            }
        result["attempts"].append(status)
        save_json(result_path, result)
    if result["attempts"] and result["attempts"][-1]["tlc"]:
        latest = task_dir / f"{result['attempts'][-1]['iteration']:02}" / f"{name}LLM.tla"
        shutil.copyfile(latest, task_dir / latest.name)
        return result
    description = (DATASET / "descriptions" / description_kind / f"{spec_id}.txt").read_text(encoding="utf-8")
    cfg_name = f"{spec_id}_{name}.cfg"
    (task_dir / "description.txt").write_text(description, encoding="utf-8")
    shutil.copyfile(DATASET / "specs" / "gold" / cfg_name, cfg)
    base_prompt = (
        f"Write a complete TLA+ module named {name}LLM for the task below. "
        "Return only the module text. It must work with the supplied TLC configuration.\n\n"
        f"Task description\n{description.strip()}\n\n"
        f"TLC configuration\n{cfg.read_text(encoding='utf-8').rstrip()}\n"
    )
    diagnostics = ""
    previous_module = ""
    for previous in reversed(result["attempts"]):
        previous_dir = task_dir / f"{previous['iteration']:02}"
        module_path = previous_dir / f"{name}LLM.tla"
        if module_path.exists():
            previous_module = module_path.read_text(encoding="utf-8")
            checker = "TLC" if previous["sany"] else "SANY"
            diagnostics = (previous_dir / f"{checker.lower()}.txt").read_text(encoding="utf-8")
            break
    for number in range(len(result["attempts"]) + 1, ITERATIONS + 1):
        attempt = task_dir / f"{number:02}"
        attempt.mkdir()
        prompt = base_prompt
        if diagnostics:
            prompt += (
                "\nRevise your previous attempt using the checker output. "
                f"Return the complete revised module.\n\nPrevious attempt\n{previous_module}\n"
                f"\nLatest {checker} output\n{diagnostics}"
            )
        request = {
            "model": model,
            "stream": False,
            "think": think,
            "keep_alive": "10m",
            "options": {**options, "seed": 1729 + number},
        }
        if endpoint == "chat":
            request["messages"] = [{"role": "user", "content": prompt}]
        else:
            request["prompt"] = prompt
        (attempt / "prompt.txt").write_text(prompt, encoding="utf-8")
        save_json(attempt / "request.json", request)
        try:
            response = ollama(f"/api/{endpoint}", request)
        except (OSError, TimeoutError) as error:
            save_json(attempt / "api-error.json", {"error": repr(error)})
            result["attempts"].append({
                "iteration": number, "sany": None, "tlc": None, "metrics": None,
                "done_reason": "transport_error",
            })
            save_json(result_path, result)
            print(f"{name} #{number}: API error {error}", flush=True)
            continue
        save_json(attempt / "response.json", response)
        status, diagnostics, module = check_answer(java, response, name, attempt, cfg, number)
        previous_module = module.read_text(encoding="utf-8")
        checker = "TLC" if status["sany"] else "SANY"
        result["attempts"].append(status)
        save_json(task_dir / "result.json", result)
        print(f"{name} #{number}: SANY={status['sany']}, TLC={status['tlc']}", flush=True)
        if status["tlc"]:
            shutil.copyfile(module, task_dir / module.name)
            break
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", default="java")
    parser.add_argument("--model", default="qwen2.5-coder:7b-instruct-q4_K_M")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--think", action="store_true")
    parser.add_argument("--endpoint", choices=("chat", "generate"), default="chat")
    parser.add_argument("--context", type=int, default=8192)
    parser.add_argument("--max-output", type=int, default=5000)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()
    java = shutil.which(args.java)
    if java is None:
        parser.error(f"Java executable not found: {args.java}")
    subprocess.run([java, "-version"], check=True)
    tags = ollama("/api/tags")
    matching = next((model for model in tags["models"] if model["name"] == args.model), None)
    if matching is None:
        parser.error(f"Ollama model is not installed: {args.model}")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=args.resume)
    model_path = output / "model.json"
    if model_path.exists():
        if json.loads(model_path.read_text(encoding="utf-8"))["digest"] != matching["digest"]:
            parser.error("The installed model digest differs from the recorded run")
    else:
        save_json(model_path, {
            "ollama": ollama("/api/version")["version"],
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            **matching,
        })
        save_json(output / "model-info.json", ollama("/api/show", {"model": args.model}))
    options = {
        "temperature": args.temperature, "top_p": 0.95, "top_k": 20,
        "num_ctx": args.context, "num_predict": args.max_output, "presence_penalty": 0.0,
    }
    save_json(output / "protocol.json", {
        "endpoint": args.endpoint, "think": args.think, "options": options,
    })
    provenance = {
        "checkout_commit": subprocess.check_output(
            ["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"], encoding="utf-8",
        ).strip(),
        "tla2tools_sha256": hashlib.sha256((CHECKOUT / "tla2tools.jar").read_bytes()).hexdigest(),
        "inputs": {},
    }
    for name, (spec_id, _, kind) in TASKS.items():
        files = [
            DATASET / "descriptions" / kind / f"{spec_id}.txt",
            DATASET / "specs" / "gold" / f"{spec_id}_{name}.tla",
            DATASET / "specs" / "gold" / f"{spec_id}_{name}.cfg",
        ]
        provenance["inputs"][name] = {
            str(path.relative_to(CHECKOUT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        }
    provenance_path = output / "provenance.json"
    if provenance_path.exists():
        if json.loads(provenance_path.read_text(encoding="utf-8")) != provenance:
            parser.error("Dataset inputs or checker JAR changed since the recorded run")
    else:
        save_json(provenance_path, provenance)
    results = {}
    for name, task in TASKS.items():
        results[name] = generate(java, args.model, output, name, task, args.think, args.endpoint, options)
        save_json(output / "results.json", results)


if __name__ == "__main__":
    main()
