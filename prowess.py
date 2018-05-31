import json
import re
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

    def execute_action(self, obj, actions):
        for action in actions:
            skip = False
            for tag in re.findall("(<[^>]*>)", action):
                action = action.replace(tag, "")
                cmd, key, value = tag[1:-1].split()

                if cmd == "on" and obj.state.get(key, None) != value:
                    skip = True
                    break
                elif cmd == "set":
                    obj.state[key] = value

            if not skip:
                ln(action)

    def parse(self, cmd):
        cmd = cmd.replace("<", "").replace(">", "")
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
            dest = self.exits[obj]
        elif obj in (o.name for o in self.exits.values()):
            dest = [o for o in self.exits.values() if o.name == obj][0]
        else:
            ln("You can only go %s." % many(self.exits.keys(), art=lambda x: x,
                sep="or"))
            return
        self.obj = dest
        self.look()

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
            elif obj in self.inv:
                ln("You already have the %s." % obj)
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
            target = self.inv[obj]
            action = target.actions.get(verb, nope)
        elif obj in self.objs: # actions on objects
            target = self.objs[obj]
            action = target.actions.get(verb, nope)
        elif verb in self.obj.actions: # actions on current place
            target = self.obj
            action = target.actions[verb]
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

        if "<" in action:
            self.execute_action(target, [action])
        elif isinstance(action, list):
            self.execute_action(target, action)
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
        obj.state = {k: str(v) for (k,v) in data.get("state", {}).items()}
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
