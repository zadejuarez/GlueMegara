def setup():
  from .meg import MegaraDataViewer
  from .data import MegaraData
  from glue.config import qt_client
  qt_client.add(MegaraDataViewer)
