"""CLI handlers and parser configuration for AGYToolkit Volatile Event Bus."""

import json
import sys
from pathlib import Path

from agy_toolkit.bus import (
    clear_bus,
    consume_events,
    list_events,
    publish_event,
    read_event,
)


def handle_bus(args):
    """Handle all subcommands under 'agy-toolkit bus'."""
    action = args.bus_action
    target_dir = Path(args.path or ".").resolve() / ".agents" / "memory"

    if action == "send":
        raw_payload = args.payload
        try:
            payload = json.loads(raw_payload)
        except (json.JSONDecodeError, TypeError):
            payload = raw_payload

        evt = publish_event(
            topic=args.topic,
            sender=args.sender,
            payload=payload,
            recipient=getattr(args, "recipient", "*") or "*",
            ttl_seconds=getattr(args, "ttl", 3600),
            memory_dir=target_dir,
        )
        print(f"[AGYToolkit Bus] Published event {evt.id} to topic '{evt.topic}' (Recipient: {evt.recipient}).")

    elif action == "read":
        if getattr(args, "id", None):
            evt = read_event(event_id=args.id, consume=getattr(args, "consume", False), memory_dir=target_dir)
            if evt:
                print(json.dumps(evt.to_dict(), indent=2))
            else:
                print(f"[AGYToolkit Bus] Event '{args.id}' not found.")
        else:
            if getattr(args, "consume", False):
                events = consume_events(
                    topic=getattr(args, "topic", None),
                    recipient=getattr(args, "recipient", None),
                    sender=getattr(args, "sender", None),
                    memory_dir=target_dir,
                )
            else:
                events = list_events(
                    topic=getattr(args, "topic", None),
                    recipient=getattr(args, "recipient", None),
                    sender=getattr(args, "sender", None),
                    memory_dir=target_dir,
                )
            if getattr(args, "json", False):
                print(json.dumps([e.to_dict() for e in events], indent=2))
            else:
                print(f"[AGYToolkit Bus] Found {len(events)} event(s):")
                for e in events:
                    print(f"  * {e.id} [{e.topic}] {e.sender} -> {e.recipient}")

    elif action == "list":
        events = list_events(memory_dir=target_dir)
        if getattr(args, "json", False):
            print(json.dumps([e.to_dict() for e in events], indent=2))
        else:
            print(f"[AGYToolkit Bus] Active events on volatile bus: {len(events)}")
            for e in events:
                print(f"  * {e.id} [{e.topic}] ({e.sender} -> {e.recipient})")

    elif action == "clear":
        cleared = clear_bus(memory_dir=target_dir)
        print(f"[AGYToolkit Bus] Cleared {cleared} event payload(s) from volatile bus.")

    elif action == "heartbeat":
        from agy_toolkit.bus import heartbeat_claim
        success = heartbeat_claim(
            event_id=args.id,
            claimer=args.claimer,
            extend_seconds=getattr(args, "extend", None),
            memory_dir=target_dir,
        )
        if success:
            print(f"[AGYToolkit Bus] Heartbeat refreshed for event '{args.id}' (Claimer: {args.claimer}).")
        else:
            print(f"[AGYToolkit Bus] Failed to refresh heartbeat for event '{args.id}'. Lock missing or claimer mismatch.")
            sys.exit(1)

    elif action == "reclaim":
        from agy_toolkit.bus import reclaim_expired_claims
        reclaimed = reclaim_expired_claims(
            memory_dir=target_dir,
            grace_seconds=getattr(args, "grace_seconds", 0.0) or 0.0,
        )
        if getattr(args, "json", False):
            print(json.dumps(reclaimed, indent=2))
        else:
            print(f"[AGYToolkit Bus] Reclaimed {len(reclaimed)} expired claim(s):")
            for item in reclaimed:
                print(f"  * {item['id']} [topic: {item['topic']}] from '{item['claimer']}' (elapsed: {item['elapsed_seconds']}s / lease: {item['lease_seconds']}s)")

    elif action == "watch":
        from agy_toolkit.bus import watch_events, claim_event, complete_claimed_event

        timeout = getattr(args, "timeout", None)
        consume = getattr(args, "consume", False)
        topic = getattr(args, "topic", None)
        recipient = getattr(args, "recipient", None)
        sender = getattr(args, "sender", None)
        output_json = getattr(args, "json", False)

        if not output_json:
            filt = f" [topic: {topic}]" if topic else ""
            print(f"[AGYToolkit Bus] Watching volatile bus for events{filt} (timeout: {timeout or 'infinite'})...")

        for event in watch_events(
            topic=topic,
            recipient=recipient,
            sender=sender,
            timeout_seconds=timeout,
            memory_dir=target_dir,
        ):
            if consume:
                claimed = claim_event(event.id, claimer="bus-watch-cli", memory_dir=target_dir)
                if claimed:
                    complete_claimed_event(event.id, claimer="bus-watch-cli", memory_dir=target_dir)

            if output_json:
                print(json.dumps(event.to_dict()))
                sys.stdout.flush()
            else:
                print(f"[EVENT] {event.id} [{event.topic}] {event.sender} -> {event.recipient}: {json.dumps(event.payload)}")
                sys.stdout.flush()


def configure_bus_parser(bus_sub):
    """Register all subparser arguments for 'agy-toolkit bus'."""
    bus_send = bus_sub.add_parser("send", help="Publish event to volatile bus")
    bus_send.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_send.add_argument("--topic", required=True, help="Event topic (e.g. handoff, review, gate)")
    bus_send.add_argument("--sender", required=True, help="Sender agent name")
    bus_send.add_argument("--recipient", default="*", help="Recipient agent name or '*' for broadcast")
    bus_send.add_argument("--payload", required=True, help="JSON or plain text payload")
    bus_send.add_argument("--ttl", type=int, default=3600, help="Time-to-live in seconds (default: 3600)")

    bus_read = bus_sub.add_parser("read", help="Read events from volatile bus")
    bus_read.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_read.add_argument("--id", help="Read specific event by ID")
    bus_read.add_argument("--topic", help="Filter by topic")
    bus_read.add_argument("--recipient", help="Filter by recipient")
    bus_read.add_argument("--sender", help="Filter by sender")
    bus_read.add_argument("--consume", action="store_true", help="Delete events upon reading")
    bus_read.add_argument("--json", action="store_true", help="Output events as JSON")

    bus_list = bus_sub.add_parser("list", help="List all events in volatile bus")
    bus_list.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_list.add_argument("--json", action="store_true", help="Output list as JSON")

    bus_clear = bus_sub.add_parser("clear", help="Clear all volatile bus events")
    bus_clear.add_argument("path", nargs="?", default=".", help="Workspace root directory")

    bus_hb = bus_sub.add_parser("heartbeat", help="Extend lease of an actively claimed event")
    bus_hb.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_hb.add_argument("--id", required=True, help="Target event ID")
    bus_hb.add_argument("--claimer", required=True, help="Claiming agent name")
    bus_hb.add_argument("--extend", type=int, help="Extension in seconds (optional)")

    bus_reclaim = bus_sub.add_parser("reclaim", help="Recover expired/orphaned claims back to bus")
    bus_reclaim.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_reclaim.add_argument("--grace-seconds", type=float, default=0.0, help="Grace period in seconds before reclaiming")
    bus_reclaim.add_argument("--json", action="store_true", help="Output reclaimed events as JSON")

    bus_watch = bus_sub.add_parser("watch", help="Watch and stream events from volatile bus in real time")
    bus_watch.add_argument("path", nargs="?", default=".", help="Workspace root directory")
    bus_watch.add_argument("--topic", help="Filter by topic")
    bus_watch.add_argument("--recipient", help="Filter by recipient")
    bus_watch.add_argument("--sender", help="Filter by sender")
    bus_watch.add_argument("--timeout", type=float, help="Timeout in seconds before exiting")
    bus_watch.add_argument("--consume", action="store_true", help="Atomically consume events as they arrive")
    bus_watch.add_argument("--json", action="store_true", help="Stream events as JSON Lines")
