"""CLI for Gmail intake."""
from __future__ import annotations

import argparse
import json
import sys

from .config import GmailIntakeConfig
from .service import GmailIntakeService
from .pipeline import PipelinePoster
from .models import InvoiceEnvelope, Body, GmailInfo


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gl-gmail-intake")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("once", help="Run one polling cycle")
    loop_p = sub.add_parser("loop", help="Run polling loop")
    loop_p.add_argument("--interval", type=int, default=60)

    sub.add_parser("test", help="Send synthetic envelope")
    sub.add_parser("watch", help="(stub) register gmail watch")
    sub.add_parser("label", help="Ensure label exists")
    return p


def cmd_once(config: GmailIntakeConfig) -> int:
    service = GmailIntakeService(config)
    return service.run_once()


def cmd_loop(config: GmailIntakeConfig, interval: int) -> None:
    import time

    service = GmailIntakeService(config)
    while True:
        service.run_once()
        time.sleep(interval)


def cmd_test(config: GmailIntakeConfig) -> None:
    envelope = InvoiceEnvelope(
        gmail=GmailInfo(id="test"),
        from_="tester@example.com",
        body=Body(text_preview="test"),
    )
    PipelinePoster(config).post(envelope.dict(by_alias=True))


def cmd_label(config: GmailIntakeConfig) -> None:
    service = GmailIntakeService(config)
    service.ensure_label()


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    config = GmailIntakeConfig()
    if args.cmd == "once":
        count = cmd_once(config)
        print(count)
        return 0
    if args.cmd == "loop":
        cmd_loop(config, args.interval)
        return 0
    if args.cmd == "test":
        cmd_test(config)
        return 0
    if args.cmd == "label":
        cmd_label(config)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
