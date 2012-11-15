from django.shortcuts import render_to_response

from xmodule.xmodule import XModule

def index(request):
    xmodules = XModule.load_classes()
    return render_to_response('index.html', {
        'xmodules': xmodules
    })