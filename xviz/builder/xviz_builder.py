import logging
from easydict import EasyDict as edict

from xviz.message import XVIZData
from xviz.builder.validator import XVIZValidator
from xviz.builder.pose import XVIZPoseBuilder
from xviz.builder.primitive import XVIZPrimitiveBuilder
from xviz.builder.variable import XVIZVariableBuilder

from xviz.v2.core_pb2 import StreamSet
from google.protobuf.json_format import MessageToDict

PRIMARY_POSE_STREAM = '/vehicle_pose'

class XVIZBuilder:
    def __init__(self, metadata=None, disable_streams=None,
                 logger=logging.getLogger("xviz")):
        self._validator = XVIZValidator(logger)
        self.metadata = metadata or {}
        self.disable_streams = disable_streams or []
        self._stream_builder = None

        self._pose_builder = XVIZPoseBuilder(self.metadata, self._validator)
        self._variables_builder = XVIZVariableBuilder(self.metadata, self._validator)
        self._primitives_builder = XVIZPrimitiveBuilder(self.metadata, self._validator)
        # self._future_instance_builder = XVIZFutureInstanceBuilder(self.metadata, self._validator)
        # self._ui_primitives_builder = XVIZUIPrimitiveBuilder(self.metadata, self._validator)
        # self._time_series_builder = XVIZTimeSeriesBuilder(self.metadata, self._validator)

    def pose(self, stream_id=PRIMARY_POSE_STREAM):
        self._stream_builder = self._pose_builder.stream(stream_id)
        return self._stream_builder

    def variable(self, stream_id):
        self._stream_builder = self._variables_builder.stream(stream_id)
        return self._stream_builder

    def primitive(self, stream_id):
        self._stream_builder = self._primitives_builder.stream(stream_id)
        return self._stream_builder

    def future_instance(self, stream_id, timestamp):
        pass

    def ui_primitives(self, stream_id):
        pass

    def time_series(self, stream_id):
        pass

    def _reset(self):
        self._stream_builder = None

    def get_message(self):
        poses = self._pose_builder.get_data()
        if (not poses) or (PRIMARY_POSE_STREAM not in poses):
            self._validator.error('Every message requires a %s stream' % PRIMARY_POSE_STREAM)

        data = XVIZData(StreamSet(
            timestamp=poses[PRIMARY_POSE_STREAM].timestamp, # TODO: is timestamp required?
            poses=poses,
            primitives=self._primitives_builder.get_data(),
            # futures = self._future_instance_builder.get_data(),
            variables=self._variables_builder.get_data(),
            # time_series = self._time_series_builder.get_data(),
            # ui_primitives = self._ui_primitives_builder.get_data(),
        ))

        message = dict(
            update_type = 'SNAPSHOT',
            updates = [data.to_object()] # TODO: pass raw data
        )

        return message
