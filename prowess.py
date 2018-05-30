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
    write("".join(msg) + "\n")

def a(s):
    art = "an" if s in "aeiou" else "a"
    return "%s %s" % (art, s)

def many(objs):
    objs = list(objs)
    if len(objs) > 1:
        return "%s and %s" % (", ".join(map(a, objs[:-1])), a(objs[-1]))
    if len(objs) == 1:
        return a(objs[0])
    return ""

class Game:
    def __init__(self, obj, inv):
        self.obj = obj
        self.inv = inv

    def ask(self):
        return input("> ").strip()

    def parse(self, cmd):
        s = cmd.split()
        while len(s) < 3:
            s += [None]
        return s

    def look(self):
        write("%s." % self.obj.about)

        if self.obj.objs:
            write(" You see %s." % many(self.obj.objs.keys()))

        if self.obj.exits:
            def to(wo):
                way, obj = wo
                return "%s to the %s" % (obj.name, way)
            write(" There is %s." % many(map(to, self.obj.exits.items())))

        writeln("")

    def run(self):
        self.look()
        while True:
            self.dispatch(*self.parse(self.ask()))

    def dispatch(self, verb, obj, subj):
        if verb in ["l", "look", "examine"]:
            if not obj:
                self.look()
            elif obj in self.obj.objs:
                writeln(self.obj.objs[obj].about)
            elif obj in self.inv.objs:
                writeln(self.inv.objs[obj].about)
            elif obj in self.obj.exits:
                writeln("You can't see the %s from here." % obj)
            else:
                writeln("There is no %s here." % obj)
        elif verb in ["i", "inventory"]:
            write("You are carrying %s" % many(selv.inv.objs))
        elif verb in ["quit", "exit"]:
            raise StopIteration

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

    start = objs[items[0]["name"]]
    inventory = objs["inventory"]
    return start, inventory

def run():
    try:
        writeln("Welcome to adventure.")
        writeln("Typical commands are: (l)ook, (g)o, (t)ake, (d)rop and (u)se.")
        writeln("Type 'quit' to quit.")
        writeln("")
        game = Game(*load("objs.json"))
        game.run()
    except EOFError:
        writeln("")
    except StopIteration:
        pass

if __name__ == "__main__":
    run()
