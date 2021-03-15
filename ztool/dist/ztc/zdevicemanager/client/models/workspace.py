from .base import Model, Collection


class WorkspaceModel(Model):
    """Workspace class represent a Workspace"""

    def tags(self):
        """
        Get all available tags of the data published in the workspace.

        Args:
            workspace_id (str): workspace ID.

        Returns:
             (list of string): The response of the search.

        Raises:
            :py:class:`adm.errors.NotFound`
                If the container does not exist.
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        return self.client.api.tags(self.id)


class WorkspaceCollection(Collection):
    model = WorkspaceModel

    def list(self, all=False, before=None, filters=None, limit=-1):
        """
        List Workspaces
        """
        resp = self.client.api.containers(all=all, filters=filters, limit=limit)
        return [self.prepare_model(r) for r in resp]

    def get(self, workspace_id):
        """
        Get a workspace by ID.

        Args:
            workspace_id (str): Workspace ID.

        Returns:
            A :py:class:`Workspace` object.

        Raises:
            :py:class:`adm.errors.NotFound`
                If the container does not exist.
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.get_workspace(workspace_id)

        return self.prepare_model(resp)

    def create(self, name, description=""):
        """
        Create a workspace

        Args:
            name (str): name of the workspace.
            description (str): short description of the wokspace

        Returns:
            A :py:class:`Workspace` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.create_workspace(name, description)
        return self.prepare_model(resp)
