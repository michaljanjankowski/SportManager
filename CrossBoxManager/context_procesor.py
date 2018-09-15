def	context_procesor(request):
    return {'logged_user':request.user.username}