from prowess import *

with open("prowess.py", "rt") as f:
    print("code = %r" % comp(f.read()))

with open("objs.json", "rt") as f:
    print("objs = %r" % comp(f.read()))

print("""
def run():
    # Indulge me!
    def dec(x):
        import base64
        import zlib
        return zlib.decompress(base64.b85decode(x)).decode("utf-8")

    globs = {}
    exec(dec(code), globs)
    globs["run"](objs)

if __name__ == "__main__":
    run()""")
