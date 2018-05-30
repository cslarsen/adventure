import json
import sys

try:
    import gnureadline
except ImportError:
    pass

def w(*msg):
    sys.stdout.write("".join(msg))
    sys.stdout.flush()

def ln(*msg):
    if msg and None not in msg:
        w("".join(msg) + "\n")

def a(s):
    art = "an" if s[0] in "aeiou" else "a"
    return "%s %s" % (art, s)

def the(s):
    return "the %s" % s

def many(objs, art=a, sep="and"):
    objs = list(objs)
    if len(objs) > 1:
        return "%s %s %s" % (", ".join(map(art, objs[:-1])), sep, art(objs[-1]))
    if len(objs) == 1:
        return art(objs[0])
    return ""

class Game:
    def __init__(self, obj, inv):
        self.obj = obj
        self._inv = inv

    @property
    def inv(self):
        return self._inv.objs

    @property
    def objs(self):
        return self.obj.objs

    @property
    def exits(self):
        return self.obj.exits

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

    def run(self):
        self.look()
        while True:
            self.dispatch(*self.parse(self.ask()))

    def look(self, obj=None):
        if not obj:
            if self.obj.about.lower().startswith("you"):
                w("%s." % self.obj.about)
            else:
                w("You are in %s." % self.obj.about)
            if self.objs:
                w(" You see %s here." % many(self.objs.keys()))
            if self.exits:
                def to(wo):
                    way, obj = wo
                    return "%s to the %s" % (obj.name, way)
                w(" There is %s." % many(map(to, self.exits.items())))
            ln("")
        elif obj in self.objs:
            ln("%s." % self.objs[obj].about.capitalize())
        elif obj in self.inv:
            ln("%s." % self.inv[obj].about.capitalize())
        elif obj in (o.name for o in self.exits.values()):
            ln("You can't see the %s from here." % obj)
        elif obj in self.exits:
            ln("There is %s to the %s." % (a(self.exits[obj].name),
                obj))
        elif obj in ["east", "north", "west", "south"]:
            ln("There isn't anything particular to the %s." % obj)
        elif obj in ("around"):
            ln("So, you look. Around. In the %s." % self.obj.name)
        else:
            ln("There is no %s here." % obj)

    def inventory(self, obj):
        if obj:
            self.look(obj)
        elif self.inv:
            ln("You are carrying %s." % many(self.inv))
        else:
            ln("You are carrying nothing.")

    def go(self, obj):
        if obj in self.exits:
            self.obj = self.exits[obj]
            self.look()
            return
        elif obj in (o.name for o in self.exits.values()):
            for o in self.exits.values():
                if o.name == obj:
                    self.obj = o
                    self.look()
                    return
        ln("You can only go %s." % many(self.exits.keys(), art=lambda x: x,
            sep="or"))

    def quit(self, obj):
        raise StopIteration

    def take(self, obj):
        if obj in self.objs:
            self.inv[obj] = self.objs.pop(obj)
            ln("You take the %s." % obj)
        else:
            if obj in (o.name for o in self.exits.values()):
                ln("You cannot actually take the %s." % obj)
            elif obj in self.exits:
                ln("Right, you can't pocket an abstract term like %r." % obj)
            else:
                ln("I see no %s here." % obj)

    def drop(self, obj):
        if obj in self.inv:
            self.objs[obj] = self.inv.pop(obj)
            ln("You drop the %s." % obj)
        else:
            ln("You don't have %s." % a(obj))

    def action(self, verb, obj):
        nope = "You either can't or won't  %s the %s." % (verb, obj)
        if obj in self.inv: # actions on inventory objects
            action = self.inv[obj].actions.get(verb, nope)
        elif obj in self.objs: # actions on objects
            action = self.objs[obj].actions.get(verb, nope)
        elif verb in self.obj.actions: # actions on current place
            action = self.obj.actions[verb]
        else:
            # Enumerate possibilities
            found = [o.name for o in self.inv.values() if verb in o.actions]
            found += [o.name for o in self.objs.values() if verb in o.actions]
            if not found:
                ln("There is nothing you can safely %s around here." % verb)
            else:
                ln("What do you want to %s? %s?" % (verb,
                    many(found, art=the, sep="or").capitalize()))
            return

        if action[0] == "<" and action[-1] == ">":
            self.dispatch(*self.parse(action[1:-1]))
            return
        elif isinstance(action, list):
            found = None
            for act in action:
                if act[0] == "<" and act[-1] == ">":
                    # dirty, rewrite
                    act = act[1:-1]
                    verb, when, obj = act.split()
                    which, value = when.split("=")
                    if which == "at" and self.obj.name == value:
                        found = [verb, obj, None]
                        break
            if found:
                self.dispatch(*found)
            else:
                ln("That doesn't work.")
        else:
            ln(action)


    def dispatch(self, verb, obj, subj):
        funcs = {
            "d": self.drop,
            "drop": self.drop,
            "g": self.go,
            "get": self.take,
            "go": self.go,
            "i": self.inventory,
            "inventory": self.inventory,
            "l": self.look,
            "look": self.look,
            "ls": self.look,
            "q": self.quit,
            "quit": self.quit,
            "t": self.take,
            "take": self.take,
        }

        if verb in funcs:
            func = funcs[verb]
            func(obj)
        elif verb:
            self.action(verb, obj)

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
        ln("Welcome to adventure.")
        ln("Typical commands are: (l)ook, (g)o, (t)ake, (d)rop and (u)se.")
        ln("Type (q)uit to exit.")
        ln("")
        game = Game(*load("objs.json"))
        game.run()
    except EOFError:
        ln("")
    except StopIteration:
        pass

if __name__ == "__main__":
    run()
