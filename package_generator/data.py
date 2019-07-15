# encoding: utf8


import random
import logging
import functools
import time
import util

ItemAttr = 'food flower medicine bright lovely'.split()
ItemNames = 'stick flower'.split()
IgnoreSentence = '__ignore_sentence__'

# 特殊的round
GoBack = '__go_back__'
GoToRoot = '__go_to_root__'
Leave = '__leave__'


def multi_cond(conds):
    @functools.wraps(conds[0])
    def __wrapper__():
        for cond in conds:
            if not cond():
                return
        return True
    return __wrapper__


def random_affection():
    """
    :return: [-1,1]
    """
    return (random.random() - 0.5) * 2


def lerp(begin, end, value):
    return begin + (end - begin) * value


def get_random_values(attr_list):
    result = {}
    for attr in attr_list:
        result[attr] = random_affection()
    return result


def rand(min, max):
    return min + random.random() * (max - min)


def clamp(value):
    return max(-1, min(1, value))


def get_attr_score(main_attr_list, another_attr_list, weight=None):
    """
    算法
        main中存在的属性,another不存在是默认为0
        main中不存在的属性,another中存在,直接忽略掉
    参数
        attr_list: string=>float[-1,1]
        weight: string=>float[0,1]
    """
    total_score = 0
    count = 0
    score_info = []
    for attr, score1 in main_attr_list.iteritems():
        score2 = another_attr_list.get(attr, 0)
        score = 1 - abs(score1 - score2) * 0.5
        if weight:
            score *= weight.get(attr)
        total_score += score
        count += 1
        score_info.append(dict(attr=attr, score=score))
    if count > 0:
        score_info.sort(key=lambda v: -v['score'])
        return dict(score=total_score / count, scores=score_info)
    return dict(score=0.5, scores=score_info)


class Item(object):
    def __init__(self):
        self.name = None
        self.attr2score = None  # string=>float[-1,1]
        self.generate()

    def set_name(self, name):
        self.name = name
        return self

    def generate(self):
        self.name = ItemNames[random.randint(0, len(ItemNames) - 1)]
        self.attr2score = get_random_values(ItemAttr)
        return self

    # person_affection: string=>float
    def get_affection(self, item_attr_affection):
        return get_attr_score(self.attr2score, item_attr_affection)['score']


class Threshold(object):
    def __init__(self, threshold, sentence, affection_delta=0.):
        self.threshold = threshold
        self.sentence = sentence
        self.affection_delta = affection_delta


class PersonMemory(object):
    def __init__(self):
        self.gift_count = dict()
        self.talking_count = 0
        self.relationship = {}  # person_id=>float
        self.couple_id = 0  # 老公/老婆


class Person(object):
    # personality: 性格,1表示奔放,-1表示自闭
    # appearance: 1表示外貌协会,-1表示厌恶好看的人
    # wealthy: 1表示喜欢富有的人,-1表示厌恶金钱
    characters = 'appearance wealthy personality'.split()
    PersonID = 1
    storage_fields = 'id action_affection item_affection item_attr_affection character_affection character_weight'

    def __init__(self):
        self.id = Person.PersonID
        Person.PersonID += 1  # 自增

        # hobby[-1,1]
        # :: talking eating dancing
        self.action_affection = {}

        # gift affection[-1,1]
        # :: red_flower
        self.item_affection = {}
        # gift attr affection[-1,1]
        # :: food flower tool
        self.item_attr_affection = {}
        # type -> value[-1,1]
        # :: appearance justice humor wealthy goodness

        self.character_affection = {}
        # type -> value[0,1]
        # :: appearance ...
        self.character_weight = {}

        self.mem = PersonMemory()

    # [-1,1] 获取对某个物品的整体印象分
    def get_item_affection(self, item):
        score1 = self.item_affection.get(item.name)
        score2 = item.get_affection(self.item_attr_affection)
        if score1 is None:
            return score2
        score1_weight = 0.7
        return score1_weight * score1 + (1 - score1_weight) * score2

    def get_gift_affection(self, giver, item):
        affection = self.get_item_affection(item)
        affection += lerp(-0.5, 0.5, self.get_person_impression(giver))
        return affection

    # [-1,1] 获得对某个人的属性印象分
    def get_person_impression(self, another, only_score=True):
        info = get_attr_score(self.character_affection, another.character_affection, self.character_weight)
        if only_score:
            return info['score']
        return info

    # [-1,1] 获得和某个人的关系分
    def get_relation(self, another):
        self.init_relation(another)
        return self.mem.relationship[another.id]

    # 随机生成一个人物
    def generate(self):
        # 随机生成人物属性
        for character in Person.characters:
            self.character_affection[character] = random_affection()
            self.character_weight[character] = random.random()

        # 强制修正人物属性
        #: 95%的人都爱钱
        if random.random() < 0.6:
            self.character_weight['wealthy'] = rand(0.3, 1)
            self.character_affection['wealthy'] = rand(0.8, 1)
        #: 喜欢好看的人
        self.character_weight['wealthy'] = rand(0.2, 1)
        if random.random() < 0.8:
            self.character_affection['wealthy'] = rand(0.2, 1)
        #: 性格是很重要的
        self.character_weight['personality'] = 1

        # 物品的喜好
        self.item_attr_affection = get_random_values(ItemAttr)
        self.item_affection = get_random_values(ItemNames)

        return self

    def init_relation(self, another):
        if another.id not in self.mem.relationship:
            init_impression = self.get_person_impression(another)
            self.mem.relationship[another.id] = min(init_impression, 0.1)

    def get_items_affection(self):
        """
        :return: 返回数组(item_name,affection) 最喜欢的排在最前面
        """
        result = []
        for item, affection in self.item_affection.iteritems():
            result.append((item, affection))
        result.sort(key=lambda v: -v[1])
        return result

    def take_item(self, giver, item):
        """
        :param giver:
        :param item:
        :return: False表示拒绝收下礼物, 后面接要说的话
        """
        affection = self.get_gift_affection(giver, item)
        thresholds = [
            Threshold(0.9, 'oh i love you, as well as this fantastic gift!', affection_delta=0.2),
            Threshold(0.5, 'thanks a lot! i love it so much!', affection_delta=0.1),
            Threshold(0., 'its so nice of you', affection_delta=.05),
            Threshold(-.5, 'im afraid i cannot accept it', affection_delta=-.1),
            Threshold(-1., 'oh no, i hat this so much', affection_delta=-.5),
        ]
        for info in thresholds:
            if affection >= info.threshold:
                # 影响关系
                self.init_relation(giver)
                self.mem.relationship[giver.id] += info.affection_delta
                self.mem.relationship[giver.id] = clamp(self.mem.relationship[giver.id])
                return info.affection_delta > 0, info.sentence

        return False, 'i dont known what to say'

    def has_item(self, item):
        return random.random() > 0.5

    def get_gift(self):
        if random.random() > 0.5:
            return Item().generate()
        return None

    def increase_relation(self, person, delta):
        self.init_relation(person)
        self.mem.relationship[person.id] += delta

    def is_cp(self, person):
        return self.mem.couple_id == person.id

    def make_cp(self, person):
        self.mem.couple_id = person.id

    def has_cp(self):
        return self.mem.couple_id != 0


# 对话中的一个句子
class Sentence(object):
    def __init__(self, sentence, next_round=None, cond=None, callback=None, is_system=False):
        """
        :param cond: 是否显示这句话的条件
        :param sentence: 显示的话,或者fn
        :param callback: 点击后的回调事件
        :return:
        """
        # validation
        if not isinstance(sentence, basestring) and not callable(sentence):
            print sentence
            raise RuntimeError("invalid sentence")
        if next_round is not None and not isinstance(next_round, Round):
            if isinstance(next_round, basestring) and next_round.startswith('__'):
                pass
            else:
                raise RuntimeError("invalid next_round")
        if cond is not None and not callable(cond):
            raise RuntimeError("invalid condition")
        if callback is not None and not callable(callback):
            raise RuntimeError("invalid callback")

        self.sentence = sentence
        self.cond = cond
        self.callback = callback
        self.next_round = next_round
        self.is_system = is_system
        self.sentence_str = None

    # return False 表示需要忽略这句话
    def update_sentence_str(self):
        self.sentence_str = self.sentence
        if callable(self.sentence_str):
            self.sentence_str = self.sentence_str()
            return self.sentence_str != IgnoreSentence
        return True

    def condition_met(self):
        if self.cond:
            return self.cond()
        return True

    def on_select(self):
        if self.callback:
            self.callback()


def Sentences(sentences, cond=None, callback=None):
    result = []
    for sentence in sentences:
        # 支持直接添加string
        if isinstance(sentence, basestring):
            result.append(Sentence(sentence, cond=cond, callback=callback))
            continue

        if not isinstance(sentence, Sentence):
            print(sentence)
            raise RuntimeError("invalid sentence")
        result.append(sentence)

        # override一些公共属性
        if cond and not sentence.cond:
            sentence.cond = cond
        if callback and not sentence.callback:
            sentence.callback = callback
    return result


class GiftStatus(object):
    unknown = 0
    accepted = 1
    denied = 2
    not_found = 3


class AttitudeType(object):
    neutral = 0
    positive = 1
    negative = 2


class ConversationContext(object):
    def __init__(self):
        self.hero = None  # 主角
        self.speaker = None  # 主角正在跟谁说话
        self.item = None  # 当前正在操作的item. 例如送礼,讨论
        self.gift_status = GiftStatus.unknown  # 对礼物的态度
        self.current_round = None  # 当前的说话轮次
        self.attitude = AttitudeType.neutral  # AttitudeType speaker的反应是不是积极的
        self.back_root_count = 0  # 回到root对话的次数


# 一问一答的方式
class Round(object):
    def __init__(self, tips, sentences=None, allow_exit=True, is_special=False):
        """
        :param tips: Sentence,表示speaker说的话
        :param sentences: SentenceList 主角可以选择的话
        :return:
        """
        # validation
        if sentences is None:
            sentences = list()
        if not isinstance(sentences, list):
            raise RuntimeError("sentences must be of list type")

        # 将分组的sentence展开
        expanded_sentence = list()
        for sentence in sentences:
            if isinstance(sentence, list):
                expanded_sentence.extend(sentence)
            else:
                expanded_sentence.append(sentence)
        sentences = expanded_sentence

        for sentence in sentences:
            if not isinstance(sentence, Sentence):
                print sentence
                raise RuntimeError("invalid sentence type")

        self.is_special = is_special
        self.ctx = None  # 一次对话的上下文
        # speaker说的话,数组,多句话
        self.tips = tips if isinstance(tips, list) else [tips]
        self.tip_index = 0
        self.sentences = sentences  # 主角说话的选项
        self._effective_sentences = list()  # 允许展示的sentence列表
        self.allow_exit = allow_exit
        self.show_index = 0  # 当前是第几次进行展示.每个Round算作一次.
        self.initialized = False  # 复用时不要重复初始化
    
    def any_effective_sentences(self):
        return self._effective_sentences is not None and len(self._effective_sentences) > 0

    def any_sentences(self):
        return self.sentences is not None and len(self.sentences) > 0

    def show(self):
        """
        :return: dict(done=bool, tip=str, sentences=str_list)
            tip=None 则说明说完了
            done=True 表示最后一句话了
            done=False 表示还没说完呢
        """
        self._effective_sentences = None
        result = dict(done=False, tip='unset!', sentences=[])
        if self.tip_index == 0:
            self.show_index += 1

        # 找到第一句话
        while True:
            tip = self.tips[self.tip_index]
            self.tip_index += 1
            if isinstance(tip, basestring):
                result['tip'] = tip
            else:
                # 动态生成句子
                # return True 继续下一句
                # return False 立刻结束Round
                # return str 显示这个句子
                # return other 异常
                fn_tip = tip(self)
                if fn_tip is None:
                    raise Exception("fn_tip cannot be None")
                if fn_tip is False:
                    result['tip'] = '...'

                    self.tip_index = 0
                    result['done'] = True
                    return result
                if fn_tip is True:
                    continue

                if isinstance(fn_tip, basestring):
                    result['tip'] = fn_tip
            if result['tip'] or self.tip_index >= len(self.tips):
                break

        if self.tip_index < len(self.tips):
            return result

        self._effective_sentences = list()
        system_sentence_count = 0
        for sentence in self.sentences:
            if sentence.condition_met() and sentence.update_sentence_str():
                self._effective_sentences.append(sentence)
                result['sentences'].append(sentence.sentence_str)
                if sentence.is_system:
                    system_sentence_count += 1
        if self.any_effective_sentences() and system_sentence_count == len(self._effective_sentences):
            print 'Error! ' * 10

        self.tip_index = 0
        result['done'] = True
        return result

    @staticmethod
    def default_display(result):
        if not result['tip']:
            return False
        print '=' * 10, 'speaker', '=' * 10
        print result['tip']
        print '-' * 10
        for idx in range(len(result['sentences'])):
            print '[%d] %s' % (idx + 1, result['sentences'][idx])
        return True

    def choose(self, index):
        if not self._effective_sentences:
            return
        s = self._effective_sentences[index]
        s.on_select()
        return s.next_round


# random sentence generator
def rand_sg(sentences):
    def __wrapper__(round):
        return sentences[random.randint(0, len(sentences) - 1)]
    return __wrapper__


# 控制一次完整的对话
class Conversation(object):
    def __init__(self):
        story = [
            self._story_first_sentence,
            'once upon a time',
            'i am still a little girl',
            'i have a harmonious family',
            'my father loved me, my mother loved me too',
        ]
        thanks = Round(rand_sg([
            'oh thank you',
            'it is so nice of you',
            'i really appreciate that',
            'thanks',
            'thanks a lot',
            'its so kind of you',
        ]))
        story_round = Round(story, [
            Sentence('its really a lovely story', callback=self._increase_relation, next_round=thanks),
            Sentence('em... ok'),
            Sentence('actually i cannot really understand your story', callback=self._decrease_relation, next_round=Round('all right')),
        ])
        cp_round = Round(self._sentence_cp_response, [
            Sentence('wow its fantastic!', cond=self._cond_positive_attitude, callback=self._increase_relation),
            Sentences([
                Sentence('ok i can understand. i wont give up by the way', callback=self._increase_relation),
                Sentence('ok its fine', callback=self._decrease_relation),
            ], cond=self._cond_neutral_attitude),
            Sentences([
                'ok, its fine...',
                'no way...',
                'but why?',
            ], cond=self._cond_negative_attitude, callback=self._decrease_relation),
        ])
        gift_round = Round(self._sentence_accept_gift, [
            Sentence('thats great!', cond=self._cond_gift_accepted),
            Sentence('ok, it fine...', cond=self._cond_gift_not_accepted),
            Sentence('ok i can understand. i wont give you this again', cond=self._cond_gift_not_accepted),
            Sentence('oh, its my fault. sorry', cond=self._cond_gift_not_found),
        ])
        self.root_round = Round(self._init_sentence, [
            Sentence('please tell me about your story', story_round),
            Sentence(self._sentence_cp_request, cp_round),
            Sentence(self._sentence_send_gift, gift_round),
            Sentence('what item do you like?', Round(self._tip_tell_item_like, [
                Sentence('i love that too!', Round('oh really? haha..', [
                    Sentence(':)'),
                    Sentence("i'm just kidding...", callback=self._decrease_relation),
                ]), callback=self._increase_relation, cond=self._cond_hero_like_item),
                Sentence('oh no, i hate that, really really a lot', cond=self._cond_hero_not_like_item),
                Sentence('em.. okay', cond=self._cond_hero_not_like_item),
                Sentence('ok! i will send you that', gift_round, cond=self._cond_item),
                Sentence('ok, but i dont want to send you that', Round(
                    'what?', [
                            Sentence('hehe, you thought i like you?', callback=self._decrease_relation),
                            Sentence('ha, i am just kidding'),
                            Sentence('just kidding. do you like it?', gift_round,
                                     callback=self._increase_relation, cond=self._cond_item),
                        ],
                ), cond=self._cond_item, callback=self._decrease_relation),
            ])),
            Sentence('how is your impression abount me?', Round(self._tip_tell_person_initial_impression, [
                Sentence('ok, 3q', cond=self._cond_positive_attitude),
                Sentence('i am feeling the same way', cond=self._cond_positive_attitude),
                Sentence('anyway, i like you', cond=self._cond_negative_attitude, callback=self._decrease_relation),
                Sentence('i can understand that', cond=self._cond_negative_attitude),
                Sentence('all right, its fine', cond=self._cond_negative_attitude),
                Sentence('but why?', cond=self._cond_negative_attitude, callback=self._decrease_relation,
                         next_round=Round(
                                 'it is just my feeling', [
                                     Sentence('ok...'),
                                 ]
                         )),
                Sentence('ok, got that', cond=self._cond_neutral_attitude),
                Sentence('ok, but it is still a little upsetting', cond=self._cond_neutral_attitude),
            ])),
            Sentence('how do you think about our relation?', Round(self._tip_tell_person_relation, [
                Sentence('ok, 3q', cond=self._cond_positive_attitude),
                Sentence('i think so too', cond=self._cond_positive_attitude),
                Sentence('anyway, i love you', cond=self._cond_negative_attitude, callback=self._decrease_relation),
                Sentence('i can understand that', cond=self._cond_negative_attitude),
                Sentence('all right, its fine', cond=self._cond_negative_attitude),
                Sentence('but why?', cond=self._cond_negative_attitude, callback=self._decrease_relation,
                         next_round=Round(
                                 'just my feeling', [
                                     Sentence('ok...'),
                                 ]
                         )),
                Sentence('ok, got that', cond=self._cond_neutral_attitude),
                Sentence('ok, but i wont give you up', cond=self._cond_neutral_attitude),
            ]))
        ])

        self.have_to_go_sentence = Sentence('i have to go now', Round('ok, see you', [
            Sentence('see you', Leave)
        ], allow_exit=False), is_system=True)
        self.leave_sentence = Sentence('leave directly', Leave, is_system=True)
        self._init_rounds(self.root_round)

        self.ctx = None

    # 一行3个
    _init_sentences = [
        'hi~', 'so, anything else?', 'ha ha...',
        'you are really a talker', "i'm a little tired", 'em...',
        'ok go on...', 'yeah...', 'all right',
        'i dont want to talk any more', "dont really want to talk any more", "i am so tired of you now",
        'oh i hate you now', 'please stop now', 'talk talk talk..',
        'you never stop talking!', 'its a little awkward now', "i have nothing to say now"
    ]

    def _init_sentence(self, round):
        index = round.show_index - 1
        if index >= len(self._init_sentences):
            index = len(self._init_sentences) - 1

        # 一开始说话,增加心情
        if index == 0:
            relation = self.ctx.speaker.get_relation(self.ctx.hero)
            self._increase_relation(relation * 0.1)

        # 说话太多影响关系
        max_index = 9
        if index >= max_index:
            percent = float(2 * max_index - index) / max_index
            percent = clamp(percent)
            self._decrease_relation(-percent * 0.2)

        return self._init_sentences[index]

    def _story_first_sentence(self, round):
        sentences = [
            'ok, i will tell your once more',
            ]
        '''
            'emm.. whats wrong about your memory?',
            'ok, remember for this time, ok?',
            'all right, its the last time',
        ]
        '''
        if round.show_index <= 1:
            return True
        index = round.show_index - 2
        if index >= len(sentences):
            return False
        return sentences[index]

    # 对round tree进行初始化
    def _init_rounds(self, root_round):
        if root_round.initialized:
            return
        root_round.initialized = True

        if root_round.any_sentences() and root_round.allow_exit:
            root_round.sentences.append(self.have_to_go_sentence)
            root_round.sentences.append(self.leave_sentence)
        for sentence in root_round.sentences:
            if sentence.next_round and not isinstance(sentence.next_round, basestring):
                self._init_rounds(sentence.next_round)

    def _increase_relation(self, delta=0.03):
        self.ctx.speaker.increase_relation(self.ctx.hero, delta)

    def _decrease_relation(self, delta=-0.05):
        self.ctx.speaker.increase_relation(self.ctx.hero, delta)

    def _make_cp(self):
        self.ctx.speaker.make_cp(self.ctx.hero)

    def _cond_cp(self):
        return self.ctx.speaker.is_cp(self.ctx.hero)

    def _cond_item(self):
        return self.ctx.item is not None

    def _cond_gift_accepted(self):
        return self.ctx.gift_status == GiftStatus.accepted

    def _cond_gift_not_accepted(self):
        return self.ctx.gift_status == GiftStatus.denied

    def _cond_gift_not_found(self):
        return self.ctx.gift_status == GiftStatus.not_found

    def _cond_hero_like_item(self):
        if not self.ctx.item:
            return
        affection = self.ctx.hero.get_item_affection(self.ctx.item)
        return affection > 0

    def _cond_hero_not_like_item(self):
        if not self.ctx.item:
            return
        affection = self.ctx.hero.get_item_affection(self.ctx.item)
        return affection <= 0

    def _cond_positive_attitude(self):
        return self.ctx.attitude == AttitudeType.positive

    def _cond_negative_attitude(self):
        return self.ctx.attitude == AttitudeType.negative

    def _cond_neutral_attitude(self):
        return self.ctx.attitude == AttitudeType.neutral

    def _sentence_send_gift(self):
        self.ctx.item = None
        gift = self.ctx.hero.get_gift()
        if gift:
            self.ctx.item = gift
            return 'i want to send you: %s' % gift.name
        return IgnoreSentence

    # 主角送礼物时,的反应
    def _sentence_accept_gift(self, round):
        if not self.ctx.item:
            self.ctx.gift_status = GiftStatus.not_found
            return 'i dont know what do you want to send to me'
        if self.ctx.hero.has_item(self.ctx.item):
            self.ctx.gift_status = GiftStatus.not_found
            return 'you do not have this item: %s' % self.ctx.item.name

        accepted, sentence = self.ctx.speaker.take_item(self.ctx.hero, self.ctx.item)
        if accepted:
            self.ctx.gift_status = GiftStatus.accepted
        else:
            self.ctx.gift_status = GiftStatus.denied
        return sentence

    # 主角送求x时说的话
    def _sentence_cp_request(self):
        if self.ctx.speaker.is_cp(self.ctx.hero):
            return IgnoreSentence
        else:
            affection = self.ctx.speaker.get_relation(self.ctx.hero)
            if affection < -0.5:
                return 'i dont like you, but if you want to, i can be your cp'
            if self.ctx.speaker.has_cp():
                return 'i want to be your new cp'
            else:
                return 'i want to be your cp'

    # 主角送求x时的反应
    def _sentence_cp_response(self, round):
        affection = self.ctx.speaker.get_relation(self.ctx.hero)

        gift = self.ctx.hero.get_gift()
        if gift:
            gift_affection = self.ctx.speaker.get_gift_affection(self.ctx.hero, gift)
            if gift_affection > 0.3:
                affection += gift_affection * 0.5

        if affection > 0.8:
            self.ctx.attitude = AttitudeType.positive
            return 'yes, i do'
        if affection > 0.4:
            self.ctx.attitude = AttitudeType.neutral
            return 'no, but i will think about that'
        if affection > 0.0:
            self.ctx.attitude = AttitudeType.neutral
            return 'em.. maybe no'
        if affection > -0.5:
            self.ctx.attitude = AttitudeType.negative
            return 'em.. no, i dont think its a good idea'
        self.ctx.attitude = AttitudeType.negative
        return 'no! dont think about that, its impossible'

    # 回答主角,喜欢什么物品
    def _tip_tell_item_like(self, round):
        self.ctx.item = None
        items = self.ctx.speaker.get_items_affection()
        loved_items = [item[0] for item in items if item[1] > 0]
        if loved_items:
            loved_item = random.choice(loved_items)
            self.ctx.item = Item().set_name(loved_item)
            return 'i love:' + loved_item
        return 'sorry, but i dont like anything'

    # 回答主角,喜不喜欢
    def _tip_tell_person_initial_impression(self, round):
        impression = self.ctx.speaker.get_person_impression(self.ctx.hero)
        relation = self.ctx.speaker.get_relation(self.ctx.hero)
        impression = max(impression, relation)
        if impression > 0.1:
            self.ctx.attitude = AttitudeType.positive
            return 'its good'
        elif impression < -0.1:
            self.ctx.attitude = AttitudeType.negative
            return 'actually not good'
        else:
            self.ctx.attitude = AttitudeType.neutral
            return 'just so so'

    # 回答主角,喜不喜欢
    def _tip_tell_person_relation(self, round):
        relation = self.ctx.speaker.get_relation(self.ctx.hero)
        if relation > 0.1:
            self.ctx.attitude = AttitudeType.positive
            return 'we are good friends'
        elif relation < -0.1:
            self.ctx.attitude = AttitudeType.negative
            return 'i dont want to make friends with you yet'
        else:
            self.ctx.attitude = AttitudeType.neutral
            return 'we are not friend yet'

    def _fallback(self):
        c = self.root_round
        self.ctx.current_round = c

    def show(self, hero, speaker):
        ctx = ConversationContext()  # 每次对话的上下文
        self.ctx = ctx
        ctx.hero = hero
        ctx.speaker = speaker
        ctx.current_round = self.root_round
        round_stack = list()
        while True:
            result = ctx.current_round.show()
            if not result['tip']:
                self._fallback()
                continue
            Round.default_display(result)
            if not result['done']:
                time.sleep(0.1)
                continue

            # 没有任何可选回答的round,直接跳到下一次对话
            if not ctx.current_round.any_effective_sentences():
                time.sleep(0.1)
                self._fallback()
                continue

            # 选择一个合适的对话
            for i in range(3):
                try:
                    index = raw_input('choose index: ')
                    next_round = ctx.current_round.choose(int(index) - 1)
                    break
                except Exception, e:
                    logging.error("exception %s", e)
                    continue

            # fallback操作
            if not next_round:
                self._fallback()
                time.sleep(0.1)
                continue

            # 处理特殊的next round
            if next_round == Leave:
                break
            elif next_round == GoToRoot:
                self.ctx.back_root_count += 1
                round_stack = list()
                ctx.current_round = self.root_round
            elif next_round == GoBack:
                if round_stack:
                    ctx.current_round = round_stack[-1]
                    round_stack.pop()
                else:
                    self._fallback()
            else:
                # 进入正常的next round
                round_stack.append(ctx.current_round)
                ctx.current_round = next_round
