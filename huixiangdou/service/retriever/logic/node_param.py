from loguru import logger
import re
# SPOBase, SPOEntity, SPORelation, TypeInfo

import itertools
import json
import re
import pdb
from typing import List, Union
from abc import ABC
from ..base import LogicNode

class Identifier:
    def __init__(self, alias_name):
        self.alias_name = alias_name

    def __repr__(self):
        return self.alias_name

    def __str__(self):
        return self.alias_name

    def __eq__(self, other):
        if isinstance(other, Identifier):
            return self.alias_name == other.alias_name
        if isinstance(other, str):
            return self.alias_name == other
        return False

    def __hash__(self):
        return hash(self.alias_name)

class TypeInfo:
    def __init__(self, entity_type=None, entity_type_zh=None):
        self.entity_type = entity_type
        self.entity_type_zh = entity_type_zh

    def __repr__(self):
        return f"en:{self.entity_type} zh:{self.entity_type_zh}"

def parse_entity(raw_entity):
    if raw_entity is None:
        return []
    entity_parts = re.findall(r'(?:`(.+?)`|([^|]+))', raw_entity)
    return [part.replace('``', '|') if part else escaping_part for escaping_part, part in entity_parts]


class SPOBase:
    def __init__(self):
        self.alias_name: Identifier = None
        self.type_set: List[TypeInfo] = []
        self.is_attribute = False
        self.value_list = []

    def __repr__(self):
        return f"{self.alias_name}:{self.get_entity_first_type_or_en()}"

    def get_value_list_str(self):
        return [f"{self.alias_name}.{k}={v}" for k,v in self.value_list]

    def get_mention_name(self):
        return ""

    def get_type_with_gql_format(self):
        entity_types = self.get_entity_type_set()
        entity_zh_types = self.get_entity_type_zh_set()
        if len(entity_types) == 0 and len(entity_zh_types) == 0:
            return None
        if None in entity_types and None in entity_zh_types:
            raise RuntimeError(f"None type in entity type en {entity_types} zh {entity_zh_types}")
        if len(entity_types) > 0:
            return "|".join(entity_types)
        if len(entity_zh_types) > 0:
            return "|".join(entity_zh_types)

    def get_entity_first_type(self):
        type_list = list(self.get_entity_type_set())
        if len(type_list) == 0:
            return None
        return type_list[0]

    def get_entity_first_type_or_en(self):
        en = list(self.get_entity_type_set())
        zh = list(self.get_entity_type_zh_set())
        if len(zh) > 0:
            return zh[0]
        elif len(en) > 0:
            return en[0]
        else:
            return None

    def get_entity_type_or_zh_list(self):
        ret = []
        for entity_type_info in self.type_set:
            if entity_type_info.entity_type is not None:
                ret.append(entity_type_info.entity_type)
            elif entity_type_info.entity_type_zh is not None:
                ret.append(entity_type_info.entity_type_zh)
        return ret

    def get_entity_type_str(self):
        return ','.join(self.get_entity_type_or_zh_list())

    def get_entity_first_type_or_zh(self):
        en = list(self.get_entity_type_set())
        zh = list(self.get_entity_type_zh_set())
        if len(en) > 0:
            return en[0]
        elif len(zh) > 0:
            return zh[0]
        else:
            return None

    def get_entity_type_set(self):
        entity_types = []
        for entity_type_info in self.type_set:
            if entity_type_info.entity_type is not None:
                entity_types.append(entity_type_info.entity_type)
        return set(entity_types)

    def get_entity_type_zh_set(self):
        entity_types = []
        for entity_type_info in self.type_set:
            if entity_type_info.entity_type_zh is not None:
                entity_types.append(entity_type_info.entity_type_zh)
        return set(entity_types)


class SPORelation(SPOBase):
    def __init__(self, alias_name=None, rel_type=None, rel_type_zh=None):
        super().__init__()
        if rel_type is not None or rel_type_zh is not None:
            type_info = TypeInfo()
            type_info.entity_type = rel_type
            type_info.entity_type_zh = rel_type_zh
            self.type_set.append(type_info)
        self.alias_name: Identifier = None
        if alias_name is not None:
            self.alias_name = Identifier(alias_name)

        self.s: SPOBase = None
        self.o: SPOEntity = None

    def __str__(self):
        show = [f"{self.alias_name}:{self.get_entity_first_type_or_en()}"]
        show = show + self.get_value_list_str()
        return ",".join(show)

    @staticmethod
    def parse_logic_form(input_str):
        """
        Parses the logic form from the given input string and constructs a relation object.

        Parameters:
            input_str (str): The input string containing alias and entity types separated by ':'.

        Returns:
            SPORelation: A relation object with alias name and associated type set.
        """

        rel_type_set = []

        # Split the input string into alias and entity_type_set parts
        split_input = input_str.split(':', 1)
        alias = split_input[0]
        # If entity_type_set exists, process it further
        if len(split_input) > 1:
            entity_type_part = split_input[1]

            entity_types = parse_entity(entity_type_part)
            for entity_type in entity_types:
                entity_type_obj = TypeInfo()
                entity_type_obj.entity_type_zh = entity_type
                rel_type_set.append(entity_type_obj)

        rel = SPORelation()
        rel.alias_name = Identifier(alias)
        rel.type_set = rel_type_set
        return rel

class SPOEntity(SPOBase):
    def __init__(self, entity_id=None, entity_type=None, entity_type_zh=None, entity_name=None, alias_name=None,
                 is_attribute=False):
        super().__init__()
        self.is_attribute = is_attribute
        self.id_set = []
        self.entity_name = entity_name
        self.alias_name: Identifier = None
        if alias_name is not None:
            self.alias_name = Identifier(alias_name)
        if entity_id is not None:
            self.id_set.append(entity_id)
        if entity_type is not None or entity_type_zh is not None:
            type_info = TypeInfo()
            type_info.entity_type = entity_type
            type_info.entity_type_zh = entity_type_zh
            self.type_set.append(type_info)

    def __str__(self):
        show = [f"{self.alias_name}:{self.get_entity_first_type_or_en()}{'' if self.entity_name is None else '[' + self.entity_name + ']'} "]
        show = show + self.get_value_list_str()
        return ",".join(show)

    def get_mention_name(self):
        return self.entity_name
    def generate_id_key(self):
        if len(self.id_set) == 0:
            return None
        id_str_set = ['"' + id_str + '"' for id_str in self.id_set]
        return ",".join(id_str_set)

    def generate_start_infos(self, prefix=None):
        if len(self.id_set) == 0:
            return []
        if len(self.type_set) == 0:
            return []

        id_type_info = list(itertools.product(self.id_set, self.type_set))
        return [{
            "alias": self.alias_name.alias_name,
            "id": info[0],
            "type": info[1].entity_type if '.' in info[1].entity_type else (
                                                                               prefix + '.' if prefix is not None else '') +
                                                                           info[1].entity_type
        } for info in id_type_info]

    @staticmethod
    def parse_logic_form(input_str):
        # # 正则表达式解析输入字符串
        match = re.match(r"([^:]+):?([^\[]+)?(\[[^\[]*\])?(\[[^\[]*\])?", input_str)
        if not match:
            return None

        # 提取和解构匹配的组件
        alias = match.group(1)
        entity_type_raw = match.group(2)
        entity_name_raw = match.group(3)
        entity_id_raw = match.group(4)

        # 处理entity_type_set
        entity_type_set = parse_entity(entity_type_raw)

        # 解析entity_name和entity_id_set
        entity_name = entity_name_raw.strip('][') if entity_name_raw else None
        entity_name = entity_name.strip('`') if entity_name else None
        entity_id_set = parse_entity(entity_id_raw.strip('][')) if entity_id_raw else []

        spo_entity = SPOEntity()
        spo_entity.id_set = entity_id_set
        spo_entity.alias_name = Identifier(alias)
        spo_entity.entity_name = entity_name
        for entity_type in entity_type_set:
            entity_type_obj = TypeInfo()
            entity_type_obj.entity_type_zh = entity_type
            entity_type_obj.entity_type = entity_type
            spo_entity.type_set.append(entity_type_obj)
        return spo_entity

# get_spg(s, p, o)
class GetSPONode(LogicNode):
    def __init__(self, operator, args):
        super().__init__(operator, args)
        self.s: SPOBase = args.get('s', None)
        self.p: SPOBase = args.get('p', None)
        self.o: SPOBase = args.get('o', None)
        self.sub_query = args.get("sub_query", None)
        self.root_query = args.get("root_query", None)

    def to_dsl(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def to_std(self, args):
        for key, value in args.items():
            self.args[key] = value
        self.s = args.get('s', self.s)
        self.p = args.get('p', self.p)
        self.o = args.get('o', self.o)
        self.sub_query = args.get('sub_query', self.sub_query)
        self.root_query = args.get('root_query', self.root_query)

    @staticmethod
    def parse_node(input_str):
        # remove loop, use flat mode
        equality_list = re.findall(r'([\w.]+=[^=]+)(,|，|$)', input_str)
        if len(equality_list) < 3:
            raise RuntimeError(f"{__file__} parse {input_str} error not found s,p,o")
        spo_params = [e[0] for e in equality_list[:3]]
        s = None
        p = None
        o = None
        for spo_param in spo_params:
            key, param = spo_param.split('=')
            if key == "s":
                s = SPOEntity.parse_logic_form(param)
            elif key == "o":
                o = SPOEntity.parse_logic_form(param)
            elif key == "p":
                p = SPORelation.parse_logic_form(param)
        if s is None:
            raise RuntimeError(f"parse {str(spo_params)} error not found s")
        if p is None:
            raise RuntimeError(f"parse {str(spo_params)} error not found p")
        if o is None:
            raise RuntimeError(f"parse {str(spo_params)} error not found o")
        return GetSPONode("get_spo", {
            "s": s,
            "p": p,
            "o": o
        })

def binary_expr_parse(input_str):
    pattern = re.compile(r'(\w+)=((?:(?!\w+=).)*)')
    matches = pattern.finditer(input_str)
    left_expr = None
    right_expr = None
    op = None
    for match in matches:
        key = match.group(1).strip()
        value = match.group(2).strip().rstrip(',')
        value = value.rstrip('，')
        if key == "left_expr":
            if "," in value:
                left_expr_list = list(set([Identifier(v) for v in value.split(",")]))
            elif "，" in value:
                left_expr_list = list(set([Identifier(v) for v in value.split("，")]))
            else:
                left_expr_list = [Identifier(value)]
            if len(left_expr_list) == 1:
                left_expr = left_expr_list[0]
            else:
                left_expr = left_expr_list
        elif key == "right_expr":
            if value != '':
                right_expr = value
        elif key == "op":
            op = value
    if left_expr is None:
        raise RuntimeError(f"parse {input_str} error not found left_expr")

    if op is None:
        raise RuntimeError(f"parse {input_str} error not found op")
    return {
        "left_expr": left_expr,
        "right_expr": right_expr,
        "op": op
    }


# filter(left_expr=alias, right_expr=other_alias or const_data, op=equal|lt|gt|le|ge|in|contains|and|or|not)
class FilterNode(LogicNode):
    def __init__(self, operator, args):
        super().__init__(operator, args)
        self.left_expr = args.get('left_expr', None)
        self.right_expr = args.get('right_expr', None)
        self.op = args.get('op', None)
        self.OP = 'equal|lt|gt|le|ge|in|contains|and|or|not'.split('|')

    def to_dsl(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def to_std(self, args):
        for key, value in args.items():
            self.args[key] = value
        self.left_expr = args.get('left_expr', self.left_expr)
        self.right_expr = args.get('right_expr', self.right_expr)
        self.op = args.get('op', self.op)

    @staticmethod
    def parse_node(args_str:str):
        args = binary_expr_parse(args_str)
        return FilterNode("filter", args)


# count(alias)->count_alias
class CountNode(LogicNode):
    def __init__(self, operator, args):
        super(CountNode, self).__init__(operator, args)
        self.alias_name = args.get("alias_name", None)
        self.set = args.get("set", None)

    def to_dsl(self):
        raise NotImplementedError("Subclasses should implement this method.")

    @staticmethod
    def parse_node(input_str, output_name):
        args = {'alias_name': output_name, 'set': input_str}
        return CountNode("count", args)

# sum(alias)->sum_alias
class SumNode(LogicNode):
    def __init__(self, operator, args):
        super(SumNode, self).__init__(operator, args)
        self.alias_name = args.get("alias_name", None)
        self.set = args.get("set", None)
        
    def to_dsl(self):
        raise NotImplementedError("Subclasses should implement this method.")

    @staticmethod
    def parse_node(input_str):
        # count_alias=count(alias)
        match = re.match(r'(\w+)[\(\（](.*)[\)\）](->)?(.*)?', input_str)
        if not match:
            pdb.set_trace()
            raise RuntimeError(f"{__file__} parse logic form error {input_str}")
        # print('match:',match.groups())
        if len(match.groups()) == 4:
            operator, params, _, alias_name = match.groups()
        else:
            operator, params = match.groups()
            alias_name = 'sum1'
        params = params.replace('，', ',').split(',')
        args = {'alias_name': alias_name, 'set': params}
        return SumNode("sum", args)


# compare(param=[alias], op=equal or not_equal or bigger or small)
class CompareNode(LogicNode):
    def __init__(self, operator, args):
        super().__init__(operator, args)
        self.alias_name = args.get("alias_name", None)
        self.set = args.get("set", None)
        self.op = args.get("op", None)

    def to_dsl(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def __str__(self):
        return f"compare：{self.set} {self.op} "

    def get_set(self):
        if isinstance(self.set, list):
            return set(self.set)
        return {self.set}

    @staticmethod
    def parse_node(input_str):
        equality_list = re.findall(r'([\w.]+=[^=]+)(,|，|$)', input_str)
        if len(equality_list) < 2:
            raise RuntimeError(f"{__file__} parse {input_str} error not found set,orderby,direction,limit")
        params = [e[0] for e in equality_list[:2]]
        params_dict = {}
        for param in params:
            key, value = param.split('=')
            if key == 'set':
                value = value.strip().replace('，', ',').replace(' ', '').strip('[').strip(']').split(',')
            params_dict[key] = value
        return CompareNode("compare", params_dict)


# class DeduceNode(LogicNode):
#     def __init__(self, operator, args):
#         super().__init__(operator, args)
#         self.deduce_ops = args.get("deduce_ops", [])

#     def __str__(self):
#         return f"deduce(op={','.join(self.deduce_ops)})"

#     @staticmethod
#     def parse_node(input_str):
#         ops = input_str.replace("op=", "")
#         input_ops = ops.split(",")
#         return DeduceNode("deduce", {
#             "deduce_ops": input_ops
#         })


# get(alias_name)
class GetNode(LogicNode):
    def __init__(self, operator, args):
        super(GetNode, self).__init__(operator, args)
        self.alias_name = args.get("alias_name")
        self.alias_name_set: list = args.get("alias_name_set")
        self.s = args.get("s", None)
        self.s_alias_map: dict = args.get("s_alias_map", None)

    def to_dsl(self):
        raise NotImplementedError("Subclasses should implement this method.")

    @staticmethod
    def parse_node(args_str):
        input_args = args_str.split(",")
        return GetNode("get", {
            "alias_name": Identifier(input_args[0]),
            "alias_name_set": [Identifier(e) for e in input_args]
        })

# search_s()
class SearchNode(LogicNode):
    def __init__(self, operator, args):
        super().__init__(operator, args)
        self.s = SPOEntity(None, None, args['type'], None, args['alias'], False)
        self.s.value_list = args['conditions']

    @staticmethod
    def parse_node(input_str):
        pattern = re.compile(r'[,\s]*s=(\w+):([^,\s]+),(.*)')
        matches = pattern.match(input_str)
        args = dict()
        args["alias"] = matches.group(1)
        args["type"] = matches.group(2)
        if len(matches.groups()) > 2:
            search_condition = dict()
            s_condition = matches.group(3)

            condition_pattern = re.compile(r'(?:[,\s]*(\w+)\.(\w+)=([^,，]+))')
            condition_list = condition_pattern.findall(s_condition)
            for condition in condition_list:
                s_property = condition[1]
                s_value = condition[2]
                s_value = SearchNode.check_value_is_reference(s_value)
                search_condition[s_property] = s_value
            args['conditions'] = search_condition

        return SearchNode('search_s', args)

    @staticmethod
    def check_value_is_reference(value_str):
        if '.' in value_str:
            return value_str.split('.')
        return value_str
