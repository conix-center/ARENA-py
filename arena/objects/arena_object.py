from ..base_object import *
from ..attributes import Animation, Data
from ..utils import *
import uuid


class Object(BaseObject):
    """
    Object class. Defines a generic object in the ARENA.
    """

    all_objects = {} # dict of all objects created so far

    def __init__(self, evt_handler=None, update_handler=None, **kwargs):
        # "object_id" is required in kwargs, defaulted to random uuid4
        object_id = kwargs.get("object_id", str(uuid.uuid4()))
        if "object_id" in kwargs: del kwargs["object_id"]

        # "persist" is required in kwargs, defaulted to false
        persist = kwargs.get("persist", False)
        if "persist" in kwargs: del kwargs["persist"]

        # special case for "parent" (can be an Object)
        if "parent" in kwargs and isinstance(kwargs["parent"], Object):
            kwargs["parent"] = kwargs["parent"].object_id

        # "ttl" is optional
        ttl = kwargs.get("ttl", None)
        if "ttl" in kwargs: del kwargs["ttl"]

        # remove timestamp, if exists
        if "timestamp" in kwargs: del kwargs["timestamp"]

        # remove "action", if exists
        if "action" in kwargs: del kwargs["action"]

        # print warning if object is being created with the same id as an existing object
        if Object.exists(object_id):
            print("[WARNING]", f"An object with object_id of {object_id} was already created. The previous object will be overwritten.")
            Object.remove(Object.get(object_id))

        # setup attributes in the "data" field
        data = kwargs.get("data", kwargs)
        data = Data(**data)
        super().__init__(
                object_id=object_id,
                type="object",
                persist=persist,
                data=data
            )
        if ttl:
            self.ttl = ttl

        self.evt_handler = evt_handler
        self.update_handler = update_handler
        self.animations = []

        # add current object to all_objects dict
        Object.add(self)

    def update_attributes(self, evt_handler=None, update_handler=None, **kwargs):
        if evt_handler:
            self.evt_handler = evt_handler

        if update_handler:
            self.update_handler = update_handler

        if "data" not in self:
            return

        # update "persist", and "ttl"
        self.persist = kwargs.get("persist", self.persist)
        if "ttl" in self:
            self.ttl = kwargs.get("ttl", self.ttl)

        data = self.data
        Data.update_data(data, kwargs)

        if self.update_handler:
            self.update_handler(self)

    def dispatch_animation(self, animation):
        if isinstance(animation, (tuple, list)):
            self.animations += list(animation)
        elif isinstance(animation, Animation):
            self.animations += [animation]
        return self.animations

    def remove_animation_at_index(self, idx):
        if 0 <= idx < len(self.animations):
            return self.animations.pop(idx)
        return -1

    def clear_animations(self):
        self.animations = []

    def json_preprocess(self, **kwargs):
        # kwargs are for additional param to add to json, like "action":"create"
        json_payload = { k:v for k,v in vars(self).items() if not callable(v) and k != "animations" }
        json_payload.update(kwargs)
        return json_payload

    def json_postprocess(self, json_payload, json_data): # to be done by subclasses, if needed
        pass

    def json(self, **kwargs):
        json_data = {}
        json_payload = self.json_preprocess(**kwargs)
        data = vars(json_payload["data"])

        for k,v in data.items():
            # color should be a hex string
            if "color" == k:
                json_data["color"] = v.hex

            # rotation should be in quaternions
            elif "rotation" == k:
                json_data["rotation"] = data["rotation"].quaternion

            # handle special case where "physics" should be "dynamic-body"
            elif "physics" == k or "dynamic_body" == k:
                json_data["dynamic-body"] = v

            # handle special case where "clickable" should be "click-listener"
            elif "clickable" == k or "click_listener" == k:
                json_data["click-listener"] = v

            # remove underscores from specific keys
            elif "goto_url" == k:
                json_data["goto-url"] = v

            elif "animation_mixer" == k:
                json_data["animation-mixer"] = v

            # for animation, replace "start" and "end" with "from" and "to"
            elif isinstance(k, str) and "animation" == k[:len("animation")]:
                animation = vars(v).copy()
                Utils.dict_key_replace(animation, "start", "from")
                Utils.dict_key_replace(animation, "end", "to")
                json_data[k] = animation
            else:
                json_data[k] = v

        json_payload["data"] = json_data
        self.json_postprocess(json_payload, json_data)
        return self.json_encode(json_payload)

    # methods for global objects dictionary
    @classmethod
    def get(cls, object_id):
        return Object.all_objects.get(object_id, None)

    @classmethod
    def add(cls, obj):
        object_id = obj.object_id
        Object.all_objects[object_id] = obj

    @classmethod
    def remove(cls, obj):
        object_id = obj.object_id
        del Object.all_objects[object_id]

    @classmethod
    def exists(cls, object_id):
        return object_id in Object.all_objects
