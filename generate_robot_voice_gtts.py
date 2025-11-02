from gtts import gTTS
from pathlib import Path
import csv, re

PHRASES = {
    "greeting_activation": [
        "Hi there!",
        "Hello vending bot!",
        "Hey, wake up robot.",
        "Good afternoon, I’d like to order something.",
        "Hi, I’m ready to place my order.",
        "Hey there, what drinks do you have today?",
    ],
    "ordering_drinks": [
        "Give me one bottle of water, please.",
        "I’d like two cans of Coca-Cola.",
        "Hey, can I get one cold coffee and one juice?",
        "Please serve me three Pepsi bottles to the counter.",
        "Robot, I need two energy drinks and a soda.",
        "Can you add one lemonade to my order?",
        "Give me one large orange juice to car number 7.",
        "I want two Coke and one Sprite.",
    ],
    "ordering_food": [
        "Can I get one packet of chips and a chocolate bar?",
        "Add one sandwich and one cookie.",
        "Please give me two burgers and one fries combo.",
        "Robot, pack one doughnut and one coffee.",
        "I’d like one pizza slice and a soft drink.",
    ],
    "payment_confirmation": [
        "How much is the total?",
        "I’ll pay by card.",
        "Please take my online payment.",
        "Confirm my order.",
        "Yes, go ahead.",
        "Cancel the last item.",
    ],
    "delivery_location": [
        "Deliver to my car, slot number 5.",
        "Bring it to the front counter.",
        "Place it in pickup box two.",
        "Send to drive-thru window, please.",
        "Put my order in collection area three.",
    ],
    "closing_farewell": [
        "That’s all, thank you.",
        "Thanks, have a great day!",
        "Appreciate it, vending bot!",
        "Bye-bye, see you soon.",
        "Thank you, have a good day.",
        "Goodbye, robot.",
    ],
}

def safe_name(s: str, max_len=60) -> str:
    s = s.strip().lower()
    s = re.sub(r"[’']", "", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:max_len] or "line"

def synth_to_mp3(text: str, out_path: Path, lang="en", tld="us", slow=False):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gTTS(text=text, lang=lang, tld=tld, slow=slow).save(str(out_path))

def main():
    out_base = Path("robot_voice_out")
    out_base.mkdir(exist_ok=True)
    rows = []

    for category, lines in PHRASES.items():
        cat_dir = out_base / category
        cat_dir.mkdir(exist_ok=True)
        print(f"\nCategory: {category}")
        for i, line in enumerate(lines, start=1):
            name = f"{i:02d}_{safe_name(line)}.mp3"
            mp3_path = cat_dir / name
            synth_to_mp3(line, mp3_path)
            print(f"✅ {line} -> {name}")
            rows.append([category, line, str(mp3_path.relative_to(out_base))])

    with open(out_base / "index.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "text", "mp3_relpath"])
        writer.writerows(rows)

    print("\nAll voice files generated in 'robot_voice_out'.")

if __name__ == "__main__":
    main()
