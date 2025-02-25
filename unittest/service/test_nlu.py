from huixiangdou.service.nlu import is_float_regex, clean_str, split_string_by_multi_markers, pack_user_assistant_to_messages, _handle_single_entity_extraction, _handle_single_relationship_extraction
from huixiangdou.service.nlu import _handle_entity_relation_summary, _merge_nodes_then_upsert, _merge_edges_then_upsert
from huixiangdou.service.nlu import parse_chunk_to_knowledge
from huixiangdou.primitive import MemoryGraph, Chunk, Faiss, encode_string, LLM
import unittest
import json
import pytoml
import asyncio
from loguru import logger

# def test_is_float_regex():
#     assert is_float_regex("123") == True
#     assert is_float_regex("-123.45") == True
#     assert is_float_regex("+67.8") == True
#     assert is_float_regex("abc") == False
#     assert is_float_regex("123.") == False
#     assert is_float_regex(".456") == True
#     assert is_float_regex("-.456") == True
#     assert is_float_regex("+.456") == True
#     assert is_float_regex("") == False
#     assert is_float_regex("123a") == False
#     assert is_float_regex(".a") == False

# def test_clean_str():
#     assert clean_str("  Hello World  ") == "Hello World"
#     assert clean_str("<b>Hello</b>") == "Hello"  # Assuming html.unescape works as expected
#     assert clean_str("Hello\x07World") == "HelloWorld"  # Control character bell (\x07) should be removed
#     assert clean_str("Hello\u200BWorld") == "HelloWorld"  # Zero width space should be removed
#     assert clean_str(123) == "123"  # Non-string input should be returned as is

# def test_split_string_by_multi_markers():
#     assert split_string_by_multi_markers("Hello,World;Test", [",", ";"]) == ["Hello", "World", "Test"]
#     assert split_string_by_multi_markers("No markers here", []) == ["No markers here"]
#     assert split_string_by_multi_markers("Single marker: test", [":"]) == ["Single marker", "test"]

# def test_pack_user_assistant_to_messages():
#     messages = pack_user_assistant_to_messages("User: Hello", "Assistant: Hi")
#     assert len(messages) == 2
#     assert messages[0]["role"] == "user" and messages[0]["content"] == "User: Hello"
#     assert messages[1]["role"] == "assistant" and messages[1]["content"] == "Assistant: Hi"


def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def load_secret():
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        return json_obj


class NLU:

    def setUp(self):
        secrets = load_secret()
        config_proto = 'config.ini'
        with open(config_proto, encoding='utf8') as f:
            config = pytoml.load(f)
            config['llm']['kimi']['api_key'] = secrets['kimi']
            config['llm']['step']['api_key'] = secrets['step']
        config_path = '/tmp/config.ini'
        with open(config_path, 'w', encoding='utf8') as f:
            pytoml.dump(config, f)
            f.flush()
        self.llm = LLM(config_path)
        self.memory_graph = MemoryGraph()
        self.nodes_data = [{
            "entity_name": "百草园",
            "entity_type": "地点",
            "description": "我家的后面有一个很大的园，相传叫作百草园",
            "source_id": "12"
        }, {
            "entity_name": "百草园",
            "entity_type": "菜园",
            "description":
            "现在是早已并1屋子一起卖给朱文公的子孙2了，连那最末次的相见也已经隔了七八年，其中似乎确凿3只有一些野草；但那时却是我的乐园。",
            "source_id": "14"
        }]

        self.edges_data = [{
            "src_id": "12",
            "tgt_id": "13",
            "weight": 1,
            "description": "做不了瀍水的事情",
            "keywords": "掌柜，评价",
            "source_id": "22"
        }, {
            "src_id": "12",
            "tgt_id": "13",
            "weight": 2,
            "description": "掌柜评价我样貌太傻",
            "keywords": "评价",
            "source_id": "23"
        }]

        self.edge_data = {"input": "value"}
        self.entityDB = Faiss()
        self.relationDB = Faiss()
        self.content = """我家的后面有一个很大的园，相传叫作百草园。现在是早已并1屋子一起卖给朱文公的子孙2了，连那最末次的相见也已经隔了七八年，其中似乎确凿3只有一些野草；但那时却是我的乐园。
不必说碧绿的菜畦4，光滑的石井栏，高大的皂荚树5，紫红的桑椹6；也不必说鸣蝉在树叶里长吟7，肥胖的黄蜂伏在菜花上，轻捷8的叫天子9（云雀）忽然从草间直窜向云霄10里去了。单是周围的短短的泥墙根一带，就有无限趣味。油蛉11在这里低唱，蟋蟀们在这里弹琴。翻开断砖来，有时会遇见蜈蚣；还有斑蝥12，倘若13用手指按住它的脊梁，便会啪的一声，从后窍14喷出一阵烟雾。何首乌15藤和木莲16藤缠络17着，木莲有莲房18一般的果实，何首乌有臃肿19的根。有人说，何首乌根是有像人形的，吃了便可以成仙，我于是常常拔它起来，牵连不断地拔起来，也曾因此弄坏了泥墙，却从来没有见过有一块根像人样。如果不怕刺，还可以摘到覆盆子20，像小珊瑚珠21攒22成的小球，又酸又甜，色味都比桑椹要好得远。
长的草里是不去的，因为相传这园里有一条很大的赤练蛇。长妈妈23曾经讲给我一个故事听：先前，有一个读书人住在古庙里用功，晚间，在院子里纳凉24的时候，突然听到有人在叫他。答应着，四面看时，却见一个美女的脸露在墙头上，向他一笑，隐去了。他很高兴；但竟给那走来和他夜谈的老和尚识破了机关25。说他脸上有些妖气，一定遇见“美女蛇”了；这是人首蛇身的怪物，能唤人名，倘一答应，夜间便要来吃这人的肉的。他自然吓得要死，而那老和尚却道26无妨，给他一个小盒子，说只要放在枕边，便可高枕而卧27。他虽然照样办，却总是睡不着，——当然睡不着的。到半夜，果然来了，沙沙沙！门外像是风雨声。他正抖作一团时，却听得豁的一声，一道金光从枕边飞出，外面便什么声音也没有了，那金光也就飞回来，敛28在盒子里。后来呢？后来，老和尚说，这是飞蜈蚣，它能吸蛇的脑髓，美女蛇就被它治死了。
结末的教训是：所以倘有陌生的声音叫你的名字，你万万不可答应他。
这故事很使我觉得做人之险，夏夜乘凉，往往有些担心，不敢去看墙上，而且极想得到一盒老和尚那样的飞蜈蚣。走到百草园的草丛旁边时，也常常这样想。但直到现在，总还没有得到，但也没有遇见过赤练蛇和美女蛇。叫我名字的陌生声音自然是常有的，然而都不是美女蛇。
冬天的百草园比较的无味；雪一下，可就两样了。拍雪人（将自己的全形印在雪上）和塑雪罗汉29需要人们鉴赏30，这是荒园，人迹罕至31，所以不相宜，只好来捕鸟。薄薄的雪，是不行的；总须积雪盖了地面一两天，鸟雀们久已无处觅食32的时候才好。扫开一块雪，露出地面，用一支短棒支起一面大的竹筛来，下面撒些秕谷33，棒上系一条长绳，人远远地牵着，看鸟雀下来啄食，走到竹筛底下的时候，将绳子一拉，便罩住了。但所得的是麻雀居多，也有白颊的“张飞鸟34”，性子很躁，养不过夜的。
这是闰土的父亲所传授的方法，我却不大能用。明明见它们进去了，拉了绳，跑去一看，却什么都没有，费了半天力，捉住的不过三四只。闰土的父亲是小半天便能捕获几十只，装在叉袋35里叫着撞着的。我曾经问他得失的缘由，他只静静地笑道：你太性急，来不及等它走到中间去。
我不知道为什么家里的人要将我送进书塾36里去了，而且还是全城中称为最严厉的书塾。也许是因为拔何首乌毁了泥墙罢，也许是因为将砖头抛到间壁的梁家去了罢，也许是因为站在石井栏上跳了下来罢……都无从37知道。总而言之：我将不能常到百草园了。Ade38，我的蟋蟀们！Ade，我的覆盆子们和木莲们！......
出门向东，不上半里，走过一道石桥，便是我先生的家了。从一扇黑油的竹门进去，第三间是书房。中间挂着一块匾道：三味书屋；匾下面是一幅画，画着一只很肥大的梅花鹿伏在古树下。没有孔子牌位，我们便对着那匾和鹿行礼。第一次算是拜孔子，第二次算是拜先生39。
第二次行礼时，先生便和蔼地在一旁答礼。他是一个高而瘦的老人，须发都花白了，还戴着大眼镜。我对他很恭敬，因为我早听到，他是本城中极方正40，质朴，博学的人。
不知从哪里听来的，东方朔41也很渊博42，他认识一种虫，名曰“怪哉43”，冤气所化，用酒一浇，就消释44了。我很想详细地知道这故事，但阿长是不知道的，因为她毕竟不渊博。现在得到机会了，可以问先生。
“先生，‘怪哉’这虫，是怎么一回事？”我上了生书，将要退下来的时候45，赶忙问。
“不知道！”他似乎很不高兴，脸上还有怒色了。
我才知道做学生是不应该问这些事的，只要读书，因为他是渊博的宿儒46，决不至于不知道，所谓不知道者，乃是不愿意说。年纪比我大的人，往往如此，我遇见过好几回了。
我就只读书，正午习字，晚上对课47。先生最初这几天对我很严厉，后来却好起来了，不过给我读的书渐渐加多，对课也渐渐地加上字去，从三言48到五言，终于到七言了。
三味书屋后面也有一个园，虽然小，但在那里也可以爬上花坛去折腊梅花，在地上或桂花树上寻蝉蜕49。最好的工作是捉了苍蝇喂蚂蚁，静悄悄地没有声音。然而同窗50们到园里的太多，太久，可就不行了，先生在书房里便大叫起来：
“人都到那里去了！”
便一个一个陆续走回去；一同回去，也不行的。他有一条戒尺51，但是不常用，也有罚跪的规则，但也不常用，普通总不过瞪几眼，大声道：
“读书！”
大家放开喉咙读一阵书，真是人声鼎沸52。有念“仁远乎哉我欲仁斯仁至矣53”的，有念“笑人齿缺曰狗窦大开”的（语出《幼学琼林·身体》），有念“上九潜龙勿用”的（语出《易经》，原为初九潜龙勿用），有念“厥土下上上错厥贡苞茅橘柚”的……(语出《尚书》中的《禹贡》)先生自己也念书。后来，我们的声音便低下去，静下去了，只有他还大声朗读着：
“铁如意，指挥倜傥54，一座皆惊呢~~；金叵罗，颠倒淋漓噫，千杯未醉嗬~~……”（语出《李克用置酒三垂冈赋》是清末诗人刘翰所作的一首诗词）
我疑心这是极好的文章，因为读到这里，他总是微笑起来，而且将头仰起，摇着，向后面拗55过去，拗过去。
读书入神的时候，于我们是很相宜的。有几个便用纸糊的盔甲56套在指甲上做戏。我是画画儿，用一种叫作“荆川纸57”的，蒙在小说的绣像58上一个个描下来， 像习字时候的影写59一样。读的书多起来，画的画也多起来；书没有读成，画的成绩却不少了，最成片段的是《荡寇志》60和《西游记》的绣像，都有一大本。后来，为要钱用，卖给了一个有钱的同窗了。他的父亲是开锡箔61店的；听说现在自己已经做了店主，而且快要升到绅士62的地位了。这东西早已没有了吧。
"""
        c = Chunk(content_or_path=self.content)
        self.chunks = [c]

    async def test_handle_single_entity_extraction(self):
        # Test with valid entity record
        entity = await _handle_single_entity_extraction(
            ['"entity"', "EntityName", "EntityType", "EntitySummary"],
            "chunk_key")
        assert entity["entity_name"] == "ENTITYNAME"
        assert entity["entity_type"] == "ENTITYTYPE"
        assert entity["description"] == "EntitySummary"
        # Test with invalid entity record
        entity = await _handle_single_entity_extraction(
            ['"invalid"', "EntityName"], "chunk_key")
        assert entity is None

    async def test_handle_single_relationship_extraction(self):
        # Test with valid relationship record
        relation = await _handle_single_relationship_extraction([
            '"relationship"', "Source", "Target", "EdgeSummary",
            "EdgeKeywords", "1.0"
        ], "chunk_key")
        assert relation["src_id"] == "SOURCE"
        assert relation["tgt_id"] == "TARGET"
        assert relation["weight"] == 1.0
        # Test with invalid relationship record
        relation = await _handle_single_relationship_extraction(
            ['"invalid"', "Source", "Target"], "chunk_key")
        assert relation is None

    async def test_handle_entity_relation_summary(self):
        summary = await _handle_entity_relation_summary(
            "EntityName", self.content, self.llm)
        assert len(summary) > 0

    async def test_merge_nodes_then_upsert(self):
        # Assuming knowledge_graph_inst is a mock instance
        node_data = await _merge_nodes_then_upsert(
            self.nodes_data[0]['entity_name'], self.nodes_data,
            self.memory_graph, self.llm)
        assert node_data["entity_type"] == "地点"

    async def test_merge_edges_then_upsert(self):
        # Assuming knowledge_graph_inst is a mock instance
        edge_data = await _merge_edges_then_upsert(
            self.edges_data[0]["src_id"], self.edges_data[0]["tgt_id"],
            self.edges_data, self.memory_graph, self.llm)
        assert self.edges_data[0]["description"] in edge_data["description"]
        assert self.edges_data[-1]["description"] in edge_data["description"]

    async def test_parse_chunk_to_knowledge(self):
        # Assuming chunks, llm, graph, entityDB, and relationDB are mock instances
        await parse_chunk_to_knowledge(self.chunks, self.llm,
                                       self.memory_graph, self.entityDB,
                                       self.relationDB)

    async def test_truncate_list_by_token_size(self):
        list_data = [{"content": "hello world"}]
        key = lambda x: x["content"]
        assert truncate_list_by_token_size(list_data, key, 5) == []
        assert truncate_list_by_token_size(list_data, key, 11) == list_data

    async def asyncTearDown(self):
        # 清理测试环境
        self.memory_graph.drop()


def test_async_funcs():
    inst = NLU()
    inst.setUp()
    loop = always_get_an_event_loop()
    loop.run_until_complete(inst.test_handle_single_entity_extraction())
    loop.run_until_complete(inst.test_handle_single_relationship_extraction())
    loop.run_until_complete(inst.test_handle_entity_relation_summary())
    loop.run_until_complete(inst.test_merge_nodes_then_upsert())
    loop.run_until_complete(inst.test_merge_edges_then_upsert())
    loop.run_until_complete(inst.test_parse_chunk_to_knowledge())
