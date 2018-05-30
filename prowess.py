import json
import sys

try:
    import gnureadline
except ImportError:
    pass

def write(*msg):
    sys.stdout.write("".join(msg))
    sys.stdout.flush()

def writeln(*msg):
    write(*msg, "\n")

class Game:
    def __init__(self, obj, inv):
        self.obj = obj
        self.inv = inv

    def ask(self):
        return input("> ").strip()

    def parse(self, cmd):
        s = cmd.split()
        while len(s) < 3:
            s += [""]
        return s

    def run(self):
        print("You are in %s." % self.obj.about)
        while True:
            subj, verb, obj = self.parse(self.ask())

class Object:
    def __init__(self, name):
        self.name = name
        self.objs = []
        self.exits = []
        self.about = ""

    def __repr__(self):
        return "<Object: name=%r objs=%d>" % (self.name, len(self.objs))

def load(filename):
    with open(filename) as f:
        items = json.load(f)

    objs = {}

    for data in items:
        obj = Object(data["name"])
        obj.about = data.get("about", "")
        obj.exits = data.get("exits", {})
        obj.objs = data.get("objects", [])
        objs[obj.name] = obj

    # Resolve links
    for obj in objs.values():
        obj.exits = {way: objs[name] for (way, name) in obj.exits.items()}
        obj.objs = {name: objs[name] for name in obj.objs}

    start = items[0]["name"]
    return objs[start]

def run():
    try:
        game = Game(load("objs.json"))
        game.run()
    except EOFError:
        print("")

if __name__ == "__main__":
    run()
