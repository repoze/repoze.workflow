def has_permission(permission, context, request):
    """ Default permission checker """
    return request.has_permission(
        permission,
        context=context)
