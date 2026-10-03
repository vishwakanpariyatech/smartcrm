from django.shortcuts import render, redirect

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')

def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)
