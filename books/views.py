from django.shortcuts import render

# Create your views here.
def index(request):
    """Index page, starting page"""
    return render(request, "books/index.html")

def books(request):
    """All books page"""
    pass

def book_detail(request):
    """Detailed book page"""
    pass