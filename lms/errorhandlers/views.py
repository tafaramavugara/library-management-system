from django.shortcuts import render

# Create your views here.
def e500(request):
    return render(request, 'Errors/e500.html', status=500)

def e404handler(request, exception):
    return render(request, 'Errors/e404.html', status=404)