"""Bounded JSON values only; never deserialize executable Python objects."""
import base64
import json
import math
from pathlib import Path
from types import SimpleNamespace

MAX_FRAME = 2 * 1024 * 1024


def encode(value, reference=None, depth=0):
    if depth > 40: raise ValueError('Value nesting exceeds protocol limit')
    child=lambda item:encode(item,reference,depth+1)
    if value is None or isinstance(value,(str,bool,int)): return value
    if isinstance(value,float):
        return value if math.isfinite(value) else {'t':'float','v':str(value)}
    if isinstance(value,bytes): return {'t':'bytes','v':base64.b64encode(value).decode()}
    if isinstance(value,Path): return {'t':'path','v':str(value)}
    if isinstance(value,tuple): return {'t':'tuple','v':[child(v) for v in value]}
    if isinstance(value,list): return {'t':'list','v':[child(v) for v in value]}
    if isinstance(value,dict): return {'t':'dict','v':[[child(k),child(v)] for k,v in value.items()]}
    if hasattr(value,'results') and hasattr(value,'next_cursor'):
        return {'t':'page','results':child(value.results),'next_cursor':child(value.next_cursor)}
    if reference: return reference(value)
    if type(value) is object: return {'t':'opaque'}
    raise ValueError('Unsupported result type')


def decode(value, reference=None, depth=0):
    if depth>40: raise ValueError('Value nesting exceeds protocol limit')
    if value is None or isinstance(value,(str,bool,int,float)): return value
    if not isinstance(value,dict): raise ValueError('Malformed encoded value')
    kind=value.get('t'); child=lambda item:decode(item,reference,depth+1)
    if kind=='list': return [child(v) for v in value['v']]
    if kind=='tuple': return tuple(child(v) for v in value['v'])
    if kind=='dict': return {child(k):child(v) for k,v in value['v']}
    if kind=='path': return Path(value['v'])
    if kind=='bytes': return base64.b64decode(value['v'],validate=True)
    if kind=='float' and value['v'] in {'nan','inf','-inf'}: return float(value['v'])
    if kind=='opaque': return object()
    if kind=='page': return SimpleNamespace(results=child(value['results']),next_cursor=child(value['next_cursor']))
    if kind in {'reference','handle'} and reference: return reference(value)
    raise ValueError('Unknown encoded type')


def send(stream,message):
    content=json.dumps(message,allow_nan=False,separators=(',',':')).encode()+b'\n'
    if len(content)>MAX_FRAME: raise ValueError('Protocol frame exceeds limit')
    stream.write(content);stream.flush()


def receive(stream):
    content=stream.readline(MAX_FRAME+1)
    if not content or len(content)>MAX_FRAME or not content.endswith(b'\n'):
        raise ValueError('Truncated or oversized protocol frame')
    result=json.loads(content,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    if not isinstance(result,dict): raise ValueError('Protocol message must be an object')
    return result
