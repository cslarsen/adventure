import base64
import json
import os
import re
import sys
import zlib

try:
    import gnureadline
except ImportError:
    pass

ALIASES = {
    "describe": "look",
    "get": "take",
    "items": "inventory",
    "pick": "take",
}

def w(*msg):
    sys.stdout.write("".join(msg))
    sys.stdout.flush()

def ln(*msg):
    if msg and None not in msg:
        w("".join(msg) + "\n")

def a(s):
    art = "an" if s[0] in "aeiou" else "a"
    return "%s %s" % (art, s)

def many(objs, art=a, sep="and"):
    objs = list(objs)
    if len(objs) > 1:
        return "%s %s %s" % (", ".join(map(art, objs[:-1])), sep, art(objs[-1]))
    if len(objs) == 1:
        return art(objs[0])
    return ""

class Object:
    def __init__(self, name):
        self.name = name

def comp(data):
    return base64.b85encode(zlib.compress(data.encode("utf-8"), 9))

def decomp(data):
    return zlib.decompress(base64.b85decode(data)).decode("utf-8")

def read(name):
    with open(os.path.join(os.path.dirname(__file__), name), "rt"):
        return decomp(f.read())

class Interpreter:
    def __init__(self, obj, inv, allobjs):
        self.obj = obj
        self.allobjs = allobjs
        self._inv = inv

    @property
    def inv(self):
        return self._inv.objs

    @property
    def objs(self):
        return self.obj.objs

    @property
    def hidden(self):
        return self.obj.hidden

    @property
    def exits(self):
        return self.obj.exits

    def ask(self):
        return input("> ").strip()

    def execute(self, obj, actions):
        def extract(action):
            commands = []
            for tag in re.findall("(<[^>]*>)", action):
                action = action.replace(tag, "")
                commands.append(tag[1:-1].split())
            return action, commands

        if isinstance(actions, list):
            for action in actions:
                self.execute(obj, action)
        else:
            action, commands = extract(actions)
            for com, key, value in commands:
                target = obj
                if "." in key:
                    name, key = key.split(".")
                    target = self.allobjs[name]

                if com == "on":
                    if key == "has" and value not in target.objs:
                        return
                    elif key != "has" and target.state.get(key, "") != value:
                        return
                elif com == "set":
                    target.state[key] = value
                elif com == "do":
                    if action: ln(action)
                    action = ""
                    self.dispatch(key, value)
            if action:
                ln(action)
        return

    def parse(self, cmd):
        cmd = cmd.replace("<", "").replace(">", "").replace(":", "")
        s = cmd.split()
        for rem in ("the", "at", "to", "a", "on", "down", "under", "over", "up"):
            if rem in s: s.remove(rem)
        for i in range(len(s)):
            s[i] = ALIASES.get(s[i], s[i])
        while len(s) < 2:
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
            ln("%s." % self.objs[obj].about)
        elif obj in self.hidden:
            ln("%s." % self.hidden[obj].about)
        elif obj in self.inv:
            ln("%s." % self.inv[obj].about)
        elif obj in (o.name for o in self.exits.values()):
            way = [k for k in self.exits if self.exits[k].name == obj][0]
            ln("There is a %s to the %s." % (obj, way))
        elif obj in self.exits:
            ln("There is %s to the %s." % (a(self.exits[obj].name),
                obj))
        elif obj in ["east", "north", "west", "south"]:
            ln("There isn't anything particular to the %s." % obj)
        elif obj in ("around"):
            ln("So, you look. Around. In the %s." % self.obj.name)
        elif obj == self.obj.name:
            self.look()
        elif obj == "inventory":
            self.inventory(None)
        else:
            ln("There is nothing particular about the %s." % obj)

    def inventory(self, obj):
        if obj:
            self.look(obj)
        elif self.inv:
            ln("You are carrying %s." % many(self.inv))
        else:
            ln("You are carrying nothing.")

    def jump(self, obj):
        self.obj = self.allobjs[obj]
        self.look()

    def go(self, obj):
        if obj in self.exits:
            dest = self.exits[obj]
        elif obj in (o.name for o in self.exits.values()):
            dest = [o for o in self.exits.values() if o.name == obj][0]
        elif not self.exits:
            ln("There is nowhere to go. You are trapped.")
            return
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
            elif obj in self.hidden:
                ln("You can't take the %s." % obj)
            elif obj:
                ln("I see no %s here." % obj)
            else:
                ln("What do you want to take? %s?" % many(self.objs,
                    art=lambda x: "the %s" % x, sep="or").capitalize())

    def drop(self, obj=None):
        if not obj:
            ln("What do you want to drop? %s?" % many(self.inv, art=lambda x:
                "the %s" % x, sep="or").capitalize())
        elif obj in self.inv:
            self.objs[obj] = self.inv.pop(obj)
            ln("You drop the %s." % obj)
        else:
            ln("You don't have %s." % a(obj))

    def action(self, verb, obj):
        nope = "You either can't or won't %s the %s." % (verb, obj)
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
                    many(found, art=lambda x: "the %s" % x, sep="or").capitalize()))
            return

        if "<" in action:
            self.execute(target, [action])
        elif isinstance(action, list):
            self.execute(target, action)
        else:
            ln(action)

    def dispatch(self, verb, obj, *rest):
        funcs = {
            ":jump": self.jump,
            "d": self.drop,
            "drop": self.drop,
            "g": self.go,
            "go": self.go,
            "i": self.inventory,
            "inventory": self.inventory,
            "l": self.look,
            "look": self.look,
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

def load(filename):
    if isinstance(filename, bytes):
        items = json.loads(decomp(filename))
    else:
        with open(filename) as f:
            items = json.load(f)

    objs = {}

    for data in items:
        obj = Object(data["name"])
        obj.about = data.get("about", "")
        obj.exits = data.get("exits", {})
        obj.objs = data.get("objects", [])
        obj.actions = data.get("actions", {})
        obj.hidden = data.get("hidden", [])
        obj.state = {k: str(v) for (k,v) in data.get("state", {}).items()}
        objs[obj.name] = obj

    # Resolve links
    for obj in objs.values():
        obj.exits = {way: objs[name] for (way, name) in obj.exits.items()}
        obj.objs = {name: objs[name] for name in obj.objs}
        obj.hidden = {name: objs[name] for name in obj.hidden}

    start = objs[items[0]["name"]]
    inventory = objs["inventory"]
    return start, inventory, objs

def run(name="objs.json"):
    try:
        Interpreter(*load(name)).run()
    except EOFError:
        ln("")
    except StopIteration:
        pass

if __name__ == "__main__":
    run()
