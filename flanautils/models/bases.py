from __future__ import annotations  # todo0 remove in 3.11

import base64
import binascii
import copy
import datetime
import json
import pickle
import pprint
import typing
from dataclasses import dataclass, field
from enum import Enum
from typing import AbstractSet, Any, Iterable, Iterator, Sequence

import pymongo.collection
import pymongo.database
from bson import ObjectId

from flanautils import iterables


class BytesBase:
    """Base class for serialize objects to bytes with pickle."""

    def __bytes__(self):
        return pickle.dumps(self)

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> Any:
        return pickle.loads(bytes_)

    def to_bytes(self):
        return bytes(self)


class CopyBase:
    """Base class for copy and deepcopy objects."""

    def copy(self) -> CopyBase:
        return copy.copy(self)

    def deep_copy(self) -> CopyBase:
        return copy.deepcopy(self)


class DictBase:
    """Base class for serialize objects to dict."""

    def _dict_repr(self) -> Any:
        """
        Returns the dict representation of your object.

        It is the only method that you would want to redefine in most cases to represent data.
        """

        return vars(self).copy()

    @classmethod
    def from_dict(cls, data: dict, lazy=True) -> DictBase:
        """Classmethod that constructs an object given a dictionary."""

        def decode_dict(cls_, data_: dict) -> Any:
            new_data = copy.copy(data_)
            type_hints = typing.get_type_hints(cls_)
            for k, v in data_.items():
                try:
                    type_ = type_hints[k]
                except (KeyError, TypeError):
                    continue

                type_origin = typing.get_origin(type_)
                type_args = typing.get_args(type_)
                try:
                    value_type = type_args[-1]
                except (IndexError, TypeError):
                    value_type = type

                match v:
                    case dict() if issubclass(type_, DictBase) and lazy:
                        continue
                    case dict(dict_) if issubclass(type_, DictBase) and not lazy:
                        new_data[k] = decode_dict(type_, dict_)
                    case [*_] as list_ if not isinstance(list_, set) and type_origin and type_origin is not typing.Union and issubclass(type_origin, Iterable) and issubclass(value_type, DictBase) and not lazy:
                        new_data[k] = [decode_dict(value_type, dict_) for dict_ in list_]
                    case bytes(bytes_) if type_ is not bytes:
                        new_data[k] = pickle.loads(bytes_)

            return new_data if issubclass(cls_, dict) else cls_(**new_data)

        return decode_dict(cls, data)

    def to_dict(self, pickle_types: tuple | list = (), recursive=False) -> Any:
        """Returns the representation of the object as a dictionary."""

        def encode_obj(obj_) -> Any:
            # noinspection PyProtectedMember,PyUnresolvedReferences
            if isinstance(obj_, pickle_types) and not obj_._dict_repr.__qualname__.startswith(obj_.__class__.__name__):
                return pickle.dumps(obj_)
            elif recursive:
                return obj_.to_dict()
            else:
                return obj_

        if not isinstance(dict_repr := self._dict_repr(), dict):
            return dict_repr

        # noinspection DuplicatedCode
        self_vars = dict_repr.copy()
        for k, v in self_vars.items():
            match v:
                case DictBase() as obj:
                    self_vars[k] = encode_obj(obj)
                case obj if isinstance(obj, pickle_types):
                    self_vars[k] = pickle.dumps(obj)
                case [*_, obj] as objs if isinstance(obj, (DictBase, *pickle_types)):
                    self_vars[k] = [encode_obj(obj) for obj in objs]

        return self_vars


class JSONBASE:
    """Base class for serialize objects to json."""

    def _json_repr(self) -> Any:
        """
        Returns the JSON representation of your object.

        It is the only method that you would want to redefine in most cases to represent data.
        """

        return vars(self)

    @classmethod
    def from_json(cls, text: str) -> Any:
        """Classmethod that constructs an object given a JSON string."""

        def decode_str(obj_: Any) -> Any:
            """Inner function to decode JSON strings to anything."""

            if not isinstance(obj_, str):
                return obj_
            try:
                bytes_ = base64.b64decode(obj_.encode(), validate=True)
                decoded_obj = pickle.loads(bytes_)
            except (binascii.Error, pickle.UnpicklingError, EOFError):
                return obj_
            return decoded_obj

        def decode_list(obj_: Any) -> Any:
            """Inner function to decode JSON lists to anything."""

            return [decode_str(e) for e in obj_]

        def decode_dict(cls_: Any, dict_: dict) -> Any:
            """Inner function to decode JSON dictionaries to anything."""

            kwargs = {}
            for k, v in dict_.items():
                k = decode_str(k)
                v = decode_str(v)
                if isinstance(v, dict):
                    try:
                        v = decode_dict(typing.get_type_hints(cls_)[k], v)
                    except KeyError:
                        pass
                kwargs[k] = v
            return cls_(**kwargs)

        if not isinstance(text, str):
            raise TypeError(f'must be str, not {type(text).__name__}')

        obj = json.loads(text)
        if isinstance(obj, str):
            return decode_str(obj)
        elif isinstance(obj, list):
            return decode_list(obj)
        elif isinstance(obj, dict):
            return decode_dict(cls, obj)
        else:
            return obj

    def to_json(self, pickle_types: tuple | list = (Enum,), indent: int = None) -> str:
        """Returns the representation of the object as a JSON string."""

        # noinspection PyProtectedMember,PyUnresolvedReferences
        def json_encoder(obj: Any) -> Any:
            if isinstance(obj, bytes):
                return base64.b64encode(obj).decode()

            match obj:
                case obj if isinstance(obj, AbstractSet):
                    return list(obj)
                case JSONBASE():
                    if isinstance(obj, pickle_types) and not obj._json_repr.__qualname__.startswith(obj.__class__.__name__):
                        return pickle.dumps(obj)
                    else:
                        return obj._json_repr()
                case (datetime.date() | datetime.datetime()) as date_time:
                    return str(date_time)
                case _:
                    try:
                        return json.dumps(obj, indent=indent)
                    except TypeError:
                        return repr(obj)

        return json.dumps(self, default=json_encoder, indent=indent)


class MeanBase:
    """Base class for calulate the mean of objects."""

    @classmethod
    def mean(cls, objects: Sequence, ratios: list[float] = None, attribute_names: Iterable[str] = ()) -> MeanBase:
        """
        Classmethod that builds a new object calculating the mean of the objects in the iterable for the attributes
        specified in attribute_names with the provided ratios.

        When calculating the mean, if an attribute is None, the ratio given for that object is distributed among the
        rest whose attributes with that name contain some value other than None.

        By default, ratios is 1 / n_objects for every object in objects.
        """

        if not objects:
            return cls()

        n_objects = len(objects)
        if not ratios:
            ratios = [1 / n_objects for _ in objects]
        elif len(ratios) != len(objects):
            raise ValueError('Wrong ratios length')

        # ----- updates the ratios depending on empty attributes -----
        attributes_ratios = {}
        attributes_ratios_length = {}
        for attribute_name in attribute_names:
            attributes_ratios[attribute_name] = ratios.copy()
            attributes_ratios_length[attribute_name] = len(attributes_ratios[attribute_name])
            for object_index, object_ in enumerate(objects):
                if not object_ or getattr(object_, attribute_name, None) is None:
                    attributes_ratios_length[attribute_name] -= 1
                    try:
                        ratio_part_to_add = attributes_ratios[attribute_name][object_index] / attributes_ratios_length[attribute_name]
                    except ZeroDivisionError:
                        ratio_part_to_add = 0
                    attributes_ratios[attribute_name][object_index] = 0
                    for ratio_index, _ in enumerate(attributes_ratios[attribute_name]):
                        if attributes_ratios[attribute_name][ratio_index]:
                            attributes_ratios[attribute_name][ratio_index] += ratio_part_to_add

        attribute_values = {}
        timezone: datetime.timezone | None = None
        for attribute_name, attribute_ratios in attributes_ratios.items():
            values = []
            for object_, ratio in zip(objects, attribute_ratios):
                if ratio:
                    attribute = getattr(object_, attribute_name)
                    if attribute_name in ('sunrise', 'sunset'):
                        timezone = attribute.tzinfo
                        attribute = attribute.timestamp()
                    values.append(attribute * ratio)

            if values:
                final_value = sum(values)
                if attribute_name in ('sunrise', 'sunset'):
                    final_value = datetime.datetime.fromtimestamp(final_value, timezone)
                attribute_values[attribute_name] = final_value

        # noinspection PyArgumentList
        return cls(**attribute_values)


class MongoBase(DictBase, BytesBase):
    """
    Base class for mapping objects to mongo documents and vice versa (Object Document Mapper).

    Dataclass compatible.
    """

    _id: ObjectId = None
    _database: pymongo.database.Database = None
    _unique_keys: str | Iterable[str] = ()
    _nullable_unique_keys: str | Iterable[str] = ()
    collection: pymongo.collection.Collection = None

    def __init__(self):
        """Automatically generate an ObjectId and store references to the database and collection."""

        match self._id:
            case str() if self._id:
                super().__setattr__('_id', ObjectId(self._id))
            case ObjectId() as object_id:
                super().__setattr__('_id', object_id)
            case _:
                super().__setattr__('_id', ObjectId())

        if self.collection is not None:
            super().__setattr__('collection', self.collection)
            super().__setattr__('_database', self.collection.database)
        if isinstance(self._unique_keys, str):
            super().__setattr__('_unique_keys', (self._unique_keys,))
        if isinstance(self._nullable_unique_keys, str):
            super().__setattr__('_nullable_unique_keys', (self._nullable_unique_keys,))

        self._create_unique_indices()

    def __post_init__(self):
        MongoBase.__init__(self)

    def __bytes__(self):
        return pickle.dumps(self.to_dict())

    def __eq__(self, other):
        if unique_attributes := self.unique_attributes:
            return isinstance(other, self.__class__) and unique_attributes == other.unique_attributes
        else:
            return isinstance(other, self.__class__) and self._id == other._id

    def __getattribute__(self, attribute_name):
        """
        Advice: Do not redefine this method.

        This very hacky method is called every time a class attribute is accessed. It is very difficult to implement
        since it is called recursively.

        So don't redefine this method if you don't really know how python treats objects internally.
        """

        value = super().__getattribute__(attribute_name)

        try:
            type_ = typing.get_type_hints(super().__getattribute__('__class__'))[attribute_name]
        except KeyError:
            return value

        match value:
            case ObjectId() as object_id if issubclass(type_, MongoBase):
                value = type_.find_one({'_id': object_id})
            case [*_, ObjectId()] as object_ids if type_arg := iterables.find(typing.get_args(type_), MongoBase):
                value = [result for object_id in object_ids if (result := type_arg.find_one({'_id': object_id}))]
            case _:
                return value

        super().__setattr__(attribute_name, value)
        return value

    def __hash__(self):
        if unique_attributes := self.unique_attributes:
            return hash(tuple(unique_attributes.values()))
        else:
            return hash(self._id)

    def _create_unique_indices(self):
        """Create the unique indices in the database based on _unique_keys and _nullable_unique_keys attributes."""

        if not self._unique_keys:
            return

        unique_keys = [(unique_key, pymongo.ASCENDING) for unique_key in self._unique_keys]
        type_filter = {'$type': ['number', 'string', 'object', 'array', 'binData', 'objectId', 'bool', 'date', 'regex',
                                 'javascript', 'regex', 'timestamp', 'minKey', 'maxKey']}
        partial_unique_filter = {nullable_unique_key: type_filter for nullable_unique_key in self._nullable_unique_keys}

        self.collection.create_index(unique_keys, partialFilterExpression=partial_unique_filter, unique=True)

    def _dict_repr(self) -> Any:
        return {k: v for k, v in vars(self).items() if k not in ('_database', '_unique_keys', '_nullable_unique_keys', 'collection')}

    def _json_repr(self) -> Any:
        self_vars = vars(self).copy()
        self_vars['_id'] = repr(self_vars['_id'])

        return {k: v for k, v in self_vars.items() if k not in ('_database', '_unique_keys', '_nullable_unique_keys', 'collection')}

    def _mongo_repr(self) -> Any:
        """Returns the object representation to save in mongo database."""

        return {k: v.value if isinstance(v, Enum) else v for k, v in self._dict_repr().items()}

    def delete(self, cascade=False):
        """
        Delete the object from the database.

        If cascade=True all objects whose classes inherit from _MongoBase are also deleted.
        """

        if cascade:
            for referenced_object in self.get_referenced_objects():
                referenced_object.delete(cascade)

        self.collection.delete_one({'_id': self._id})

    @classmethod
    def find(cls, query: dict = None, sort_keys: str | Iterable[str | tuple[str, int]] = (), lazy=False) -> Iterator | list:
        """Query the collection."""

        def find_generator() -> Iterator:
            for document in cursor:
                yield cls.from_dict(document)

        match sort_keys:
            case str():
                sort_keys = ((sort_keys, pymongo.ASCENDING),)
            case [[_, *_], *_]:
                pass
            case [*_]:
                sort_keys = [(sort_key, pymongo.ASCENDING) for sort_key in sort_keys]

        cursor: pymongo.cursor.Cursor = cls.collection.find(query)
        if sort_keys:
            cursor.sort(sort_keys)

        if lazy:
            return find_generator()
        else:
            return [cls.from_dict(document) for document in cursor]

    @classmethod
    def find_one(cls, query: dict = None, sort_keys: str | Iterable[str | tuple[str, int]] = ()) -> MongoBase | None:
        """Query the collection and return the first match."""

        return next(cls.find(query, sort_keys, lazy=True), None)

    def find_in_database_by_id(self, object_id: ObjectId) -> dict | None:
        """Find an object in all database collections by its ObjectId."""

        collections = (self._database[name] for name in self._database.list_collection_names())
        return next((document for collection in collections if (document := collection.find_one({'_id': object_id}))), None)

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> Any:
        return cls.from_dict(super().from_bytes(bytes_))

    def get_referenced_objects(self) -> list[MongoBase]:
        """Returns all referenced objects whose classes inherit from _MongoBase."""

        referenced_objects = []
        for k, v in vars(self).items():
            match v:
                case MongoBase() as obj:
                    referenced_objects.append(obj)
                case [*_, MongoBase()] as objs:
                    referenced_objects.extend(obj for obj in objs if isinstance(obj, MongoBase))

        return referenced_objects

    @property
    def object_id(self):
        return self._id

    def pull_from_database(self, query: dict = None, overwrite_fields: Iterable[str] = ()):
        """
        Updates the values of the current object with the values of the same object located in the database.

        By default, it updates the ObjectId and the attributes of the current object that contain None. You can force
        write from database with database_priority=True (by default database_priority=False).

        Ignore the attributes specified in exclude.
        """

        if not query:
            unique_attributes = self.unique_attributes

            if any(value is None for value in unique_attributes.values()):
                query = {'_id': self._id}
            else:
                query = {}
                for k, v in unique_attributes.items():
                    if isinstance(v, MongoBase):
                        v.pull_from_database(overwrite_fields=overwrite_fields)
                        v = v._id
                    query[k] = v

        if document := self.collection.find_one(query):
            for database_key, database_value in vars(self.from_dict(document)).items():
                self_value = getattr(self, database_key)
                if (
                        self_value is None
                        or
                        (isinstance(self_value, Iterable) and not self_value)
                        or
                        (database_key in overwrite_fields and database_value is not None)
                        or
                        database_key == '_id'
                ):
                    super().__setattr__(database_key, database_value)

    def resolve(self):
        """Resolve all the ObjectId references (ObjectId -> _MongoBase)."""

        for k in vars(self):
            getattr(self, k)

    def save(self, pickle_types: tuple | list = (AbstractSet,), pull_overwrite_fields: Iterable[str] = (), references=True):
        """
        Save (insert or update) the current object in the database.

        If references=True it saves the objects without redundancy (_MongoBase -> ObjectId).
        """

        if self.collection is None:
            return

        self.pull_from_database(overwrite_fields=pull_overwrite_fields)
        for referenced_object in self.get_referenced_objects():
            referenced_object.save(pickle_types, pull_overwrite_fields, references)

        data = self.to_mongo(pickle_types)

        if references:
            for k, v in data.items():
                match v:
                    case {'_id': ObjectId() as object_id}:
                        data[k] = object_id
                    case [*_, {'_id': ObjectId()}]:
                        data[k] = [obj_data['_id'] for obj_data in v]

        self.collection.find_one_and_update({'_id': self._id}, {'$set': data}, upsert=True)

    def to_mongo(self, pickle_types: tuple | list = (AbstractSet,)) -> Any:
        """Returns the representation of the object as a mongo compatible dictionary."""

        def encode_obj(obj_) -> Any:
            # noinspection PyProtectedMember,PyUnresolvedReferences
            if isinstance(obj_, pickle_types) and not obj_._mongo_repr.__qualname__.startswith(obj_.__class__.__name__):
                return pickle.dumps(obj_)
            else:
                return obj_.to_mongo()

        if not isinstance(mongo_repr := self._mongo_repr(), dict):
            return mongo_repr

        # noinspection DuplicatedCode
        self_vars = mongo_repr.copy()
        for k, v in self_vars.items():
            match v:
                case MongoBase() as obj:
                    self_vars[k] = encode_obj(obj)
                case obj if isinstance(obj, pickle_types):
                    self_vars[k] = pickle.dumps(obj)
                case [*_, obj] as objs if isinstance(obj, (MongoBase, *pickle_types)):
                    self_vars[k] = [encode_obj(obj) for obj in objs]

        return self_vars

    @property
    def unique_attributes(self):
        """
        Property that returns a dictionary with the name of the attributes that must be unique in the database and their
        values.
        """

        unique_attributes = {}
        for unique_key in self._unique_keys:
            attribute_value = getattr(self, unique_key, None)
            unique_attributes[unique_key] = attribute_value.value if isinstance(attribute_value, Enum) else attribute_value

        return unique_attributes


@dataclass(eq=False)
class DCMongoBase(MongoBase):
    """Base class to be inherited by an unfrozen dataclass."""

    _id: ObjectId = field(kw_only=True, default_factory=ObjectId)


@dataclass(eq=False, frozen=True)
class FrozenDCMongoBase(MongoBase):
    """Base class to be inherited by a frozen dataclass."""

    _id: ObjectId = field(kw_only=True, default_factory=ObjectId)


class REPRBase(DictBase):
    """Base class for a nicer objects representation."""

    def __repr__(self):
        # values = vars(self).values()
        # return f"{self.__class__.__name__}({', '.join(repr(v) for v in values)})"
        return str(self)

    def __str__(self):
        formatted = pprint.pformat(self.to_dict())
        return f'{self.__class__.__name__} {formatted[0]}\n {formatted[1:-1]}\n{formatted[-1]}'  # todo1 someday improve the internal objects appearance


class FlanaBase(REPRBase, JSONBASE, CopyBase, BytesBase):
    """Useful mixin."""


# noinspection PyPropertyDefinition
class FlanaEnum(JSONBASE, DictBase, CopyBase, BytesBase, Enum):
    """Useful mixin for enums."""

    def _dict_repr(self) -> Any:
        return self

    def _json_repr(self) -> Any:
        return bytes(self)

    @classmethod
    @property
    def items(cls) -> list[tuple[str, int]]:
        # noinspection PyTypeChecker
        return [item for item in zip(cls.keys, cls.values)]

    @classmethod
    @property
    def keys(cls) -> list[str]:
        return [element.name for element in cls]

    @classmethod
    @property
    def values(cls) -> list[int]:
        return [element.value for element in cls]
