def setup():
  from .data_viewer import MegaraDataViewer
  from glue.config import qt_client
  qt_client.add(MegaraDataViewer)
