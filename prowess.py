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

def the(s):
    return "the %s" % s

def many(objs, art=a, sep="and"):
    objs = list(objs)
    if len(objs) > 1:
        return "%s %s %s" % (", ".join(map(a, objs[:-1])), sep, art(objs[-1]))
    if len(objs) == 1:
        return art(objs[0])
    return ""

class Game:
    def __init__(self, obj, inv):
        self.obj = obj
        self.inv = inv

    def ask(self):
        return input("> ").strip()

    def parse(self, cmd):
        s = cmd.split()
        for rem in ("the", "to", "a"):
            if rem in s:
                s.remove(rem)
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
                writeln("%s." % self.obj.objs[obj].about)
            elif obj in self.inv.objs:
                writeln("%s." % self.inv.objs[obj].about)
            elif obj in self.obj.exits:
                writeln("You can't see the %s from here." % obj)
            else:
                writeln("There is no %s here." % obj)
        elif verb in ["i", "inventory"]:
            writeln("You are carrying %s." % many(self.inv.objs))
        elif verb in ["g", "go", "walk"]:
            if obj in self.obj.exits:
                self.obj = self.obj.exits[obj]
                self.look()
            elif obj in (o.name for o in self.obj.exits.values()):
                for o in self.obj.exits.values():
                    if o.name == obj:
                        self.obj = o
                        self.look()
                        return
            writeln("You can't go there.")
        elif verb in ["q", "quit"]:
            raise StopIteration
        elif verb in ["t", "take", "get"]:
            if obj in self.obj.objs:
                target = self.obj.objs.pop(obj)
                self.inv.objs[obj] = target
                writeln("You put the %s in your pocket." % obj)
            else:
                if obj in (o.name for o in self.obj.exits.values()):
                    writeln("You cannot actually take the %s." % obj)
                elif obj in self.obj.exits:
                    writeln("Right, you can't pocket an abstract term like %r."
                            % obj)
                else:
                    writeln("I see no %s here." % obj)
        elif verb in ["d", "drop"]:
            if obj in self.inv.objs:
                target = self.inv.objs.pop(obj)
                self.obj.objs[obj] = target
                writeln("You drop the %s." % obj)
            else:
                writeln("You don't have %s." % a(obj))
        elif verb:
            # Perform action on an object
            if obj in self.inv.objs:
                target = self.inv.objs[obj]
                if verb in target.actions:
                    writeln(" ".join(target.actions[verb]))
                    return
            if obj in self.obj.objs:
                target = self.objs[obj]
                if verb in target.actions:
                    writeln(" ".join(target.actions[verb]))
                    return
            # Do any objects have this action?
            found = []
            for o in self.inv.objs.values():
                if verb in o.actions:
                    found.append(o.name)
                    break
            for o in self.obj.objs.values():
                if verb in o.actions:
                    found.append(o.name)
                    break
            if not found:
                writeln("There is nothing to %s around here." % verb)
            else:
                writeln("What do you want to %s? %s?" % (verb,
                    many(found, art=the, sep="or").capitalize()))


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
        obj.actions = data.get("actions", {})
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
        writeln("Type (q)uit to exit.")
        writeln("")
        game = Game(*load("objs.json"))
        game.run()
    except EOFError:
        writeln("")
    except StopIteration:
        pass

if __name__ == "__main__":
    run()
