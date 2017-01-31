# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2016
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------

import pixiedust
from pixiedust.utils.userPreferences import *

myLogger = pixiedust.getLogger(__name__)

__all__ = ['PixiedustRenderer']

"""global dictionary used to register the renderers for each display id"""
_renderers = {}

"""
PixieDust renderer decorator. Recommended pattern is to decorate a base class with the rendererId (e.g. matplotlib)
and have all renderer subclasses provide the id
"""
class PixiedustRenderer(object):
    def __init__(self, id=None, rendererId=None):
        self.id = id
        self.rendererId = rendererId

    def __call__(self, cls, *args, **kwargs):
        if not hasattr(cls, "_id") or self.id is not None:
            cls._id = self.id
        if not hasattr(cls, "_rendererId") or self.rendererId is not None:
            cls._rendererId = self.rendererId

        if cls._id is not None and cls._rendererId is not None:
            if _renderers.get(cls._id) is None:
                _renderers[cls._id] = [cls]
            else:
                _renderers[cls._id].append(cls)
        return cls

    @staticmethod
    def getRenderer(options, entity):
        handlerId = options.get("handlerId")
        rendererId = options.get('rendererId', None )
        if rendererId is not None:
            setUserPreference(handlerId, rendererId)
        else:
            rendererId = getUserPreference( handlerId, 'matplotlib')
        renderers = _renderers.get(handlerId)
        if renderers is None or len(renderers)==0:
            myLogger.debug("Couldn't find a renderer for {0} in {1}".format(handlerId, _renderers))
            raise Exception("No renderer available for {0}".format(handlerId) )
        #Lookup the renderer, default to first one if not found
        for renderer in renderers:
            if renderer._rendererId == rendererId:
                myLogger.debug("Found renderer: {0} - {1}".format(renderer._rendererId, renderer._id))
                return renderer(options, entity)
        myLogger.debug("Defaulting to first renderer {0} - {1}".format(renderers[0]._rendererId, renderers[0]._id))
        return renderers[0](options, entity)

    @staticmethod
    def getRendererList(options, entity):
        handlerId = options.get("handlerId")
        if handlerId is None:
            return []
        return _renderers.get(handlerId)