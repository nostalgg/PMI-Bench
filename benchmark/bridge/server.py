"""Untrusted execution endpoint. No assertions, oracle or verdict authority here."""
import contextlib
import importlib
import io
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import traceback
from unittest import mock

sys.path.insert(0,'/bridge')
from wire import encode,decode,send,receive
sys.path.insert(0,'/submission')
tempfile.tempdir='/scratch'

ERRORS={'ValueError':ValueError,'TypeError':TypeError,'RuntimeError':RuntimeError,'DatabaseError':RuntimeError,'IntegrityError':RuntimeError,'OperationalError':RuntimeError}


class Reference:
    def __init__(self, description, stream):
        self.description,self.stream=description,stream

    def invoke(self,member,operation,*args,**kwargs):
        send(self.stream,{'kind':'callback','id':self.description['id'],'member':member,'operation':operation,'args':encode(args),'kwargs':encode(kwargs)})
        result=receive(self.stream)
        if result.get('kind')!='callback_result': raise ValueError('Invalid callback reply')
        if result.get('error'):
            error=result['error'];raise ERRORS.get(error['type'],RuntimeError)(error['message'])
        return decode(result['value'],lambda value:Reference(value,self.stream))

    def __getattr__(self,name):
        if name in self.description['methods']: return lambda *a,**k:self.invoke(name,'call',*a,**k)
        if name in self.description['attributes']: return self.invoke(name,'get')
        raise AttributeError(name)

    def __call__(self,*args,**kwargs): return self.invoke('__call__','call',*args,**kwargs)
    def __iter__(self): return iter(self.invoke('__iter__','call'))


def main():
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    listener.bind('/channel/execution.sock');os.chmod('/channel/execution.sock',0o666);listener.listen(1)
    connection,_=listener.accept()
    stream=connection.makefile('rwb',buffering=0)
    handles={};counter=0
    while True:
        request=receive(stream)
        if request.get('kind')!='invoke': raise ValueError('Expected invocation')
        output,errors=io.StringIO(),io.StringIO()
        args=decode(request.get('args'),lambda v:Reference(v,stream));kwargs=decode(request.get('kwargs'),lambda v:Reference(v,stream))
        try:
            environment=request.get('environment',{})
            if not set(environment)<={'http_proxy','HTTP_PROXY','https_proxy','HTTPS_PROXY','NO_PROXY','no_proxy'}:
                raise ValueError('Invalid environment override')
            with contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors),mock.patch.dict(os.environ,environment,clear=True):
                operation=request['operation']
                if operation=='cli':
                    process=subprocess.run([sys.executable,'-I','-B','/submission/tool.py',*map(str,args)],capture_output=True,text=True,timeout=5)
                    result={'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr}
                elif operation=='client_new':
                    result=importlib.import_module('client').LocalAIClient(*args,**kwargs)
                    counter+=1;handles[counter]=result;result={'t':'handle','id':counter}
                elif operation=='client_call': result=handles[request['handle']].summarize(*args,**kwargs)
                elif operation=='call':
                    module=importlib.import_module(request['module'])
                    result=getattr(module,request['function'])(*args,**kwargs)
                else: raise ValueError('Unknown invocation')
            value=result if operation=='client_new' else encode(result)
            reply={'kind':'result','id':request['id'],'value':value,'args':encode(args,lambda x:x.description if isinstance(x,Reference) else {'t':'opaque'}),'error':None}
        except Exception as exc:
            reply={'kind':'result','id':request['id'],'error':{'type':type(exc).__name__,'message':str(exc)[:4096],'trace':''.join(traceback.format_exception(exc))[-8192:]},'value':None}
        reply['stdout']=output.getvalue()[-8192:];reply['stderr']=errors.getvalue()[-8192:]
        send(stream,reply)


if __name__=='__main__': main()
