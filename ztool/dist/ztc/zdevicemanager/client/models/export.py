from .gate import GateModel
from .base import Collection


class ExportModel(GateModel):

    @property
    def Url(self):
        return self.attrs.get("dump_url")


class ExportsCollection(Collection):
    model = ExportModel

    def create(self, name, type, configurations, notifications):
        # TODO
        pass

    def get(self, id):
        # TODO
        pass