"""Command-line interface for reproducible demonstrations."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .bridge import UnityBridgeServer
from .psychophysics import write_experiment_outputs
from .simulation import write_comparison_outputs, write_demo_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="haptisense",
        description="HaptiSense VR research prototype",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    research = subparsers.add_parser("research", help="run an immutable computational contact experiment")
    research.add_argument("--output", required=True, help="new output directory")
    research.add_argument("--model", choices=("elastic", "kelvin", "sls"), default="sls")
    research.add_argument("--protocol", choices=("hold", "cycle"), default="hold")
    research.add_argument("--stiffness", type=float, default=650)
    research.add_argument("--depth-mm", type=float, default=6)

    demo = subparsers.add_parser("demo", help="generate a deterministic haptic contact trace")
    demo.add_argument("--output", default="results/demo")
    demo.add_argument("--duration", type=float, default=4.0)
    demo.add_argument("--rate", type=int, default=500)

    experiment = subparsers.add_parser("psychophysics", help="run a synthetic 2AFC pipeline demonstration")
    experiment.add_argument("--output", default="results/psychophysics")
    experiment.add_argument("--trials", type=int, default=72)
    experiment.add_argument("--seed", type=int, default=255)

    comparison = subparsers.add_parser("compare", help="compare three deterministic virtual-tissue scenarios")
    comparison.add_argument("--output", default="results/comparison")
    comparison.add_argument("--duration", type=float, default=4.0)
    comparison.add_argument("--rate", type=int, default=500)

    bridge = subparsers.add_parser("bridge", help="start the loopback Unity UDP bridge")
    bridge.add_argument("--listen-host", default="127.0.0.1")
    bridge.add_argument("--listen-port", type=int, default=9051)
    bridge.add_argument("--unity-host", default="127.0.0.1")
    bridge.add_argument("--unity-port", type=int, default=9050)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "research":
        from .research import ResearchConfig, write_research
        try:
            result = write_research(args.output, ResearchConfig(model=args.model, stiffness=args.stiffness,
                                                               depth=args.depth_mm / 1000), args.protocol)
        except (ValueError, FileExistsError) as error:
            build_parser().error(str(error))
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "demo":
        result = write_demo_outputs(args.output, args.duration, args.rate)
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "psychophysics":
        result = write_experiment_outputs(args.output, args.trials, args.seed)
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "compare":
        result = write_comparison_outputs(args.output, args.duration, args.rate)
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "bridge":
        UnityBridgeServer(
            listen_host=args.listen_host,
            listen_port=args.listen_port,
            unity_host=args.unity_host,
            unity_port=args.unity_port,
        ).serve_forever()
        return 0
    return 2
