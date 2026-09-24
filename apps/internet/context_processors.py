from apps.internet.access import is_internet_module_user


def internet(request):
    user = request.user
    return {
        "is_internet_module_user": is_internet_module_user(user),
    }
