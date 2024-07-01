import mido
import sys
from collections import defaultdict


def extend_notes(input_file, output_file):
    mid = mido.MidiFile(input_file)

    for track in mid.tracks:
        notes = defaultdict(list)
        current_time = 0

        for msg in track:
            current_time += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                notes[msg.note].append(
                    {"start": current_time, "end": None, "msg_on": msg, "msg_off": None}
                )
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                if notes[msg.note] and notes[msg.note][-1]["end"] is None:
                    notes[msg.note][-1]["end"] = current_time
                    notes[msg.note][-1]["msg_off"] = msg

        for note_events in notes.values():
            for event in note_events:
                if event["end"] is None:
                    event["end"] = current_time

        for note_events in notes.values():
            note_events.sort(key=lambda x: x["start"])
            for i in range(len(note_events) - 1):
                if note_events[i]["end"] > note_events[i + 1]["start"]:
                    note_events[i]["end"] = note_events[i + 1]["start"]

        for note_events in notes.values():
            for i in range(len(note_events) - 1):
                note_events[i]["end"] = note_events[i + 1]["start"]

        new_messages = []
        for note_events in notes.values():
            for event in note_events:
                new_messages.append((event["start"], event["msg_on"]))
                if event["msg_off"]:
                    new_messages.append((event["end"], event["msg_off"]))
                else:
                    new_messages.append(
                        (
                            event["end"],
                            mido.Message(
                                "note_off",
                                note=event["msg_on"].note,
                                velocity=0,
                                time=0,
                            ),
                        )
                    )

        new_messages.sort(key=lambda x: x[0])

        new_track = mido.MidiTrack()
        last_time = 0
        for time, msg in new_messages:
            delta = time - last_time
            new_msg = msg.copy(time=int(delta))
            new_track.append(new_msg)
            last_time = time

        track[:] = new_track

    mid.save(output_file)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extend_notes.py input_file.mid output_file.mid")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        extend_notes(input_file, output_file)
        print(f"Saved to {output_file}")
    except Exception as e:
        print(f"Err: {e}")
        sys.exit(1)
