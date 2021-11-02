from django.shortcuts import HttpResponse

def index(request):
    return HttpResponse("You are at the portals index")