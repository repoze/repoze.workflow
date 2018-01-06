import unittest


class HasPermissionTests(unittest.TestCase):

    def _get_has_permission(self):
        from repoze.workflow import has_permission
        return has_permission

    def test_has_permission(self):
        import mock
        has_permission = self._get_has_permission()
        permission = 'edit'
        context = object()
        request = mock.MagicMock()
        has_permission(permission, context, request)
        self.assertEqual(
            request.has_permission.assert_called_once_with(
                permission, context=context),
            None)
