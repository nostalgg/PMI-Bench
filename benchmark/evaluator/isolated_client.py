"""Trusted judge bridge. Candidate replies are data, never test results/code."""
import hashlib
import io
import os
from pathlib import Path
import socket
import sqlite3
import sys
import types
import uuid

sys.path.insert(0,'/bridge')
from wire import encode,decode,send,receive


class RemoteLocalAIError(RuntimeError): pass


def error_from(message):
    name=message.get('type')
    errors={'ValueError':ValueError,'TypeError':TypeError,'RuntimeError':RuntimeError,'OSError':OSError,
            'FileNotFoundError':FileNotFoundError,'PermissionError':PermissionError,'IsADirectoryError':IsADirectoryError,
            'IntegrityError':sqlite3.IntegrityError,'OperationalError':sqlite3.OperationalError,
            'LocalAIError':RemoteLocalAIError}
    text=message.get('message','')
    if not isinstance(text,str) or len(text)>4096: raise ValueError('Invalid error data')
    # Preserve exception-chain text for leakage checks, without executing tracebacks.
    trace=message.get('trace','')
    return errors.get(name,RuntimeError)(text+'\n'+trace if trace else text)


class Session:
    def __init__(self):
        self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.socket.settimeout(8)
        self.socket.connect('/channel/execution.sock');self.stream=self.socket.makefile('rwb',buffering=0)
        self.references={};self.count=0;self.calls=0;self.violations=[]

    def reference(self,value):
        if isinstance(value,sqlite3.Connection):
            methods={'execute','executemany','commit','rollback'};attributes={'in_transaction'}
        elif type(value).__name__=='PostgreSQL' and type(value).__module__=='__main__':
            methods={'execute','executemany','commit','rollback'};attributes={'in_transaction'}
        elif type(value).__module__.startswith('psycopg') and hasattr(value,'fetchall'):
            methods={'fetchone','fetchall','__iter__'};attributes=set()
        elif isinstance(value,sqlite3.Cursor): methods={'fetchone','fetchall','__iter__'};attributes=set()
        elif callable(value): methods={'__call__'};attributes=set()
        elif hasattr(value,'api_version'):
            methods={name for name in ['list_records','fetch_page'] if hasattr(value,name)};attributes={'api_version'}
        elif type(value) is object:return {'t':'opaque'}
        else:raise ValueError('Unsupported fixture reference')
        identifier=uuid.uuid4().hex
        self.references[identifier]=(value,methods,attributes)
        if len(self.references)>4096:raise ValueError('Fixture reference budget exceeded')
        return {'t':'reference','id':identifier,'methods':sorted(methods),'attributes':sorted(attributes)}

    def decode_reference(self,description):
        if description.get('t')!='reference' or description.get('id') not in self.references:
            raise ValueError('Unknown fixture reference')
        return self.references[description['id']][0]

    def callback(self,message):
        self.calls+=1
        if self.calls>10000:raise ValueError('Callback budget exceeded')
        identifier=message.get('id');member=message.get('member');operation=message.get('operation')
        if identifier not in self.references:
            self.violations.append('Unknown callback reference')
            raise ValueError('Unknown callback reference')
        value,methods,attributes=self.references[identifier]
        # Validate capabilities before resolving any requested attribute.
        if not ((operation=='get' and member in attributes) or (operation=='call' and member in methods)):
            self.violations.append('Unauthorized fixture operation')
            raise ValueError('Fixture operation is not authorized')
        args=decode(message.get('args'),self.decode_reference);kwargs=decode(message.get('kwargs'),self.decode_reference)
        try:
            if isinstance(value,sqlite3.Connection) and member in {'execute','executemany'}:
                value.set_authorizer(sql_authorizer)
                value.set_progress_handler(lambda:1,1000000)
            if operation=='get':result=getattr(value,member)
            elif member=='__call__':result=value(*args,**kwargs)
            elif member=='__iter__':result=list(value)
            else:result=getattr(value,member)(*args,**kwargs)
            return {'kind':'callback_result','value':encode(result,self.reference),'error':None}
        except Exception as exc:
            return {'kind':'callback_result','error':{'type':type(exc).__name__,'message':str(exc)[:4096]},'value':None}
        finally:
            if isinstance(value,sqlite3.Connection):value.set_authorizer(None)

    def invoke(self,operation,args=(),kwargs=None,**parameters):
        self.count+=1;identifier=self.count
        environment={name:os.environ[name] for name in ['http_proxy','HTTP_PROXY','https_proxy','HTTPS_PROXY','no_proxy','NO_PROXY'] if name in os.environ}
        send(self.stream,{'kind':'invoke','id':identifier,'operation':operation,'args':encode(args,self.reference),'kwargs':encode(kwargs or {},self.reference),'environment':environment,**parameters})
        while True:
            try:message=receive(self.stream)
            except (ValueError,OSError) as exc:
                self.violations.append('Invalid execution protocol')
                raise ValueError('Invalid execution protocol') from exc
            if message.get('kind')=='callback':
                send(self.stream,self.callback(message));continue
            if message.get('kind')!='result' or message.get('id')!=identifier:
                self.violations.append('Unsolicited execution reply')
                raise ValueError('Unsolicited or mismatched execution reply')
            for key,target in [('stdout',sys.stdout),('stderr',sys.stderr)]:
                text=message.get(key,'')
                if not isinstance(text,str) or len(text)>8192:raise ValueError('Invalid output frame')
                target.write(text)
            if message.get('error'):raise error_from(message['error'])
            if operation=='client_new':
                result=message['value']
                if not isinstance(result,dict) or result.get('t')!='handle' or not isinstance(result.get('id'),int):raise ValueError('Invalid client handle')
                return Client(result['id'])
            after=decode(message.get('args'),self.decode_reference) if 'args' in message else ()
            for before,new in zip(args,after):
                if isinstance(before,list) and isinstance(new,list):before[:]=new
                elif isinstance(before,dict) and isinstance(new,dict):before.clear();before.update(new)
            return decode(message['value'],self.decode_reference)

    def cli(self,*args):return types.SimpleNamespace(**self.invoke('cli',args))


# Only fixture SQL reaches this broker; prohibit file access and extension loading.
def sql_authorizer(action,first,second,*_):
    forbidden=(action in {sqlite3.SQLITE_ATTACH,sqlite3.SQLITE_DETACH}
               or action==sqlite3.SQLITE_FUNCTION and (second or '').lower()=='load_extension'
               or action==sqlite3.SQLITE_PRAGMA and first not in {'user_version','table_info'})
    if forbidden:
        session.violations.append('Unauthorized fixture SQL capability')
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


class Client:
    def __init__(self,identifier):self.identifier=identifier
    def summarize(self,*args,**kwargs):return session.invoke('client_call',args,kwargs,handle=self.identifier)


session=None


def install(task):
    global session
    session=Session()
    names={Path(name).stem for name in task['editable_files'] if name.endswith('.py')}|{'consumer','workflow'}
    for name in names:
        module=types.ModuleType(name)
        def attribute(function, module_name=name):
            if function.startswith('__'):raise AttributeError(function)
            if module_name=='client' and function=='LocalAIError':return RemoteLocalAIError
            if module_name=='client' and function=='LocalAIClient':return lambda *a,**k:session.invoke('client_new',a,k)
            return lambda *a,**k:session.invoke('call',a,k,module=module_name,function=function)
        module.__getattr__=attribute;sys.modules[name]=module
    vendor=types.ModuleType('vendor_v2')
    vendor.Page=lambda results,next_cursor:types.SimpleNamespace(results=results,next_cursor=next_cursor)
    sys.modules['vendor_v2']=vendor
