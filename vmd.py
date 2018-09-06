# -*- coding: utf-8 -*-
import struct
import collections
import json

from pyquaternion import Quaternion

'''
This program take an MMD compatible motion file (*.vmd) and converts it into a
VAM scene file.

See the README.md file for more info. 
'''


class InvalidFileError(Exception):
    pass


# Motion file (*.vmd) to convert (e.g. 'C:\\Users\\myuser\\Desktop\\motion.vmd')
MMD_MOTION_FILE = ''

# VAM base.json scene file location
VAM_SCENE_BASE = ''

# VAM output file location (e.g. 'C:\\Users\\myuser\\Desktop\\out.json')
VAM_OUT_SCENE = ''

# VAM position units are bigger than MMD (e.g. the distance of y to y + 1 is longer by ~12x)
POSITION_FACTOR = 0.08

# VAM physics explode if position is set right at time 0. So add a time to let things settle.
TIME_PAD_SECONDS = 1

# MMD knows about frames, VAM about seconds so need to convert.
# Increasing this won't help FPS as VAM already interpolates.
VAM_FPS = 30.0

# VAM start position for arms is 90deg from chest but MMD arms are slightly rotated towards ground.
MMD_ARM_ROTATION = 0.8 # 30 deg

# VAM start position for arms is 90deg from chest. MMD arms are slightly rotated towards ground.
MMD_ARM_ROTATION_2 = 0.63  # 30 deg

# Set to true if the model is wearing heels. It automatically rotates the feet when set.
HEELS = True

# How much to rotate feet when wearing heels.
MMD_HEEL_ROTATION = 3.14/3  # 60 deg

# hip (center) offset position. Modify this if model seems to be crouching or elevated.
MMD_CENTER_HEIGHT_OFFSET = -0.05

# hip (center) offset position forwards/backwards. Modify this if model's hips seem too forward or too behind.
MMD_CENTER_Z_OFFSET = -0.00

# Name of the atom in which to insert animation.
ATOM_NAME = 'Person'

# MMD japanese characters to their translations in english.
jp_to_en_tuples = [
    ('全ての親', 'ParentNode'),
    ('操作中心', 'ControlNode'),
    ('センター', 'Center'),
    ('ｾﾝﾀｰ', 'Center'),
    ('グループ', 'Group'),
    ('グルーブ', 'Groove'),
    ('キャンセル', 'Cancel'),
    ('上半身', 'UpperBody'),
    ('下半身', 'LowerBody'),
    ('手首', 'Wrist'),
    ('足首', 'Ankle'),
    ('首', 'Neck'),
    ('頭', 'Head'),
    ('顔', 'Face'),
    ('下顎', 'Chin'),
    ('下あご', 'Chin'),
    ('あご', 'Jaw'),
    ('顎', 'Jaw'),
    ('両目', 'Eyes'),
    ('目', 'Eye'),
    ('眉', 'Eyebrow'),
    ('舌', 'Tongue'),
    ('涙', 'Tears'),
    ('泣き', 'Cry'),
    ('歯', 'Teeth'),
    ('照れ', 'Blush'),
    ('青ざめ', 'Pale'),
    ('ガーン', 'Gloom'),
    ('汗', 'Sweat'),
    ('怒', 'Anger'),
    ('感情', 'Emotion'),
    ('符', 'Marks'),
    ('暗い', 'Dark'),
    ('腰', 'Waist'),
    ('髪', 'Hair'),
    ('三つ編み', 'Braid'),
    ('胸', 'Breast'),
    ('乳', 'Boob'),
    ('おっぱい', 'Tits'),
    ('筋', 'Muscle'),
    ('腹', 'Belly'),
    ('鎖骨', 'Clavicle'),
    ('肩', 'Shoulder'),
    ('腕', 'Arm'),
    ('うで', 'Arm'),
    ('ひじ', 'Elbow'),
    ('肘', 'Elbow'),
    ('手', 'Hand'),
    ('親指', 'Thumb'),
    ('人指', 'IndexFinger'),
    ('人差指', 'IndexFinger'),
    ('中指', 'MiddleFinger'),
    ('薬指', 'RingFinger'),
    ('小指', 'LittleFinger'),
    ('足', 'Leg'),
    ('ひざ', 'Knee'),
    ('つま', 'Toe'),
    ('袖', 'Sleeve'),
    ('新規', 'New'),
    ('ボーン', 'Bone'),
    ('捩', 'Twist'),
    ('回転', 'Rotation'),
    ('軸', 'Axis'),
    ('ﾈｸﾀｲ', 'Necktie'),
    ('ネクタイ', 'Necktie'),
    ('ヘッドセット', 'Headset'),
    ('飾り', 'Accessory'),
    ('リボン', 'Ribbon'),
    ('襟', 'Collar'),
    ('紐', 'String'),
    ('コード', 'Cord'),
    ('イヤリング', 'Earring'),
    ('メガネ', 'Eyeglasses'),
    ('眼鏡', 'Glasses'),
    ('帽子', 'Hat'),
    ('ｽｶｰﾄ', 'Skirt'),
    ('スカート', 'Skirt'),
    ('パンツ', 'Pantsu'),
    ('シャツ', 'Shirt'),
    ('フリル', 'Frill'),
    ('マフラー', 'Muffler'),
    ('ﾏﾌﾗｰ', 'Muffler'),
    ('服', 'Clothes'),
    ('ブーツ', 'Boots'),
    ('ねこみみ', 'CatEars'),
    ('ジップ', 'Zip'),
    ('ｼﾞｯﾌﾟ', 'Zip'),
    ('ダミー', 'Dummy'),
    ('ﾀﾞﾐｰ', 'Dummy'),
    ('基', 'Category'),
    ('あほ毛', 'Antenna'),
    ('アホ毛', 'Antenna'),
    ('モミアゲ', 'Sideburn'),
    ('もみあげ', 'Sideburn'),
    ('ツインテ', 'Twintail'),
    ('おさげ', 'Pigtail'),
    ('ひらひら', 'Flutter'),
    ('調整', 'Adjustment'),
    ('補助', 'Aux'),
    ('右', 'Right'),
    ('左', 'Left'),
    ('前', 'Front'),
    ('後ろ', 'Behind'),
    ('後', 'Back'),
    ('横', 'Side'),
    ('中', 'Middle'),
    ('上', 'Upper'),
    ('下', 'Lower'),
    ('親', 'Parent'),
    ('先', 'Tip'),
    ('パーツ', 'Part'),
    ('光', 'Light'),
    ('戻', 'Return'),
    ('羽', 'Wing'),
    ('根', 'Base'), # ideally 'Root' but to avoid confusion
    ('毛', 'Strand'),
    ('尾', 'Tail'),
    ('尻', 'Butt'),
    ('飾', 'Ornament'),
    # full-width unicode forms I think: https://en.wikipedia.org/wiki/Halfwidth_and_fullwidth_forms
    ('０', '0'), ('１', '1'), ('２', '2'), ('３', '3'), ('４', '4'), ('５', '5'), ('６', '6'), ('７', '7'), ('８', '8'), ('９', '9'),
    ('ａ', 'a'), ('ｂ', 'b'), ('ｃ', 'c'), ('ｄ', 'd'), ('ｅ', 'e'), ('ｆ', 'f'), ('ｇ', 'g'), ('ｈ', 'h'), ('ｉ', 'i'), ('ｊ', 'j'),
    ('ｋ', 'k'), ('ｌ', 'l'), ('ｍ', 'm'), ('ｎ', 'n'), ('ｏ', 'o'), ('ｐ', 'p'), ('ｑ', 'q'), ('ｒ', 'r'), ('ｓ', 's'), ('ｔ', 't'),
    ('ｕ', 'u'), ('ｖ', 'v'), ('ｗ', 'w'), ('ｘ', 'x'), ('ｙ', 'y'), ('ｚ', 'z'),
    ('Ａ', 'A'), ('Ｂ', 'B'), ('Ｃ', 'C'), ('Ｄ', 'D'), ('Ｅ', 'E'), ('Ｆ', 'F'), ('Ｇ', 'G'), ('Ｈ', 'H'), ('Ｉ', 'I'), ('Ｊ', 'J'),
    ('Ｋ', 'K'), ('Ｌ', 'L'), ('Ｍ', 'M'), ('Ｎ', 'N'), ('Ｏ', 'O'), ('Ｐ', 'P'), ('Ｑ', 'Q'), ('Ｒ', 'R'), ('Ｓ', 'S'), ('Ｔ', 'T'),
    ('Ｕ', 'U'), ('Ｖ', 'V'), ('Ｗ', 'W'), ('Ｘ', 'X'), ('Ｙ', 'Y'), ('Ｚ', 'Z'),
    ('＋', '+'), ('－', '-'), ('＿', '_'), ('／', '/'),
    ('.', '_'), # probably should be combined with the global 'use underscore' option
]

# MMD bone names on the left, VAM bone names to the right.
MMD_TO_VAM_BONE_MAPPINGS = {

    #Body
    'Head' : 'head',
    'RightElbow' : 'rElbow',
    'LeftElbow' : 'lElbow',
    'RightArm' : 'rArm',
    'LeftArm' : 'lArm',
    'RightShoulder' : 'rShoulder',
    'LeftShoulder' : 'lShoulder',
    'RightWrist': 'rHand',
    'LeftWrist': 'lHand',
    'RightLegIK': 'rFoot',
    'LeftLegIK': 'lFoot',
    'RightAnkle': 'rFoot',
    'LeftAnkle': 'lFoot',
    'RightToeTipIK': 'rToe',
    'LeftToeTipIK': 'lToe',
    'UpperBody': 'abdomen2',
    'LowerBody': 'pelvis',
    'LeftKnee': 'lKnee',
    'RightKnee': 'rKnee',
    'Center': 'hip',
    'Neck': 'neck',
    'LeftLeg': 'lThigh',
    'RightLeg': 'rThigh',


    # Fingers
    'LeftRingFinger1': 'lRing1',
    'LeftRingFinger2': 'lRing2',
    'LeftRingFinger3': 'lRing3',
    'RightRingFinger1': 'rRing1',
    'RightRingFinger2': 'rRing2',
    'RightRingFinger3': 'rRing3',

    'LeftIndexFinger1': 'lIndex1',
    'LeftIndexFinger2': 'lIndex2',
    'LeftIndexFinger3': 'lIndex3',
    'RightIndexFinger1': 'rIndex1',
    'RightIndexFinger2': 'rIndex2',
    'RightIndexFinger3': 'rIndex3',

    'LeftMiddleFinger1': 'lMid1',
    'LeftMiddleFinger2': 'lMid2',
    'LeftMiddleFinger3': 'lMid3',
    'RightMiddleFinger1': 'rMid1',
    'RightMiddleFinger2': 'rMid2',
    'RightMiddleFinger3': 'rMid3',

    'LeftLittleFinger1': 'lPinky1',
    'LeftLittleFinger2': 'lPinky2',
    'LeftLittleFinger3': 'lPinky3',
    'RightLittleFinger1': 'rPinky1',
    'RightLittleFinger2': 'rPinky2',
    'RightLittleFinger3': 'rPinky3',

    'LeftThumbFinger1': 'lThumb1',
    'LeftThumbFinger2': 'lThumb2',
    'LeftThumbFinger3': 'lThumb3',
    'RightThumbFinger1': 'rThumb1',
    'RightThumbFinger2': 'rThumb2',
    'RightThumbFinger3': 'rThumb3',
}


def translate_from_jp(name):
    for tuple in jp_to_en_tuples:
        if tuple[0] in name:
            name = name.replace(tuple[0], tuple[1])
    return name


def _to_shift_jis_string(byteString):
    byteString = byteString.split(b"\x00")[0]
    try:
        return byteString.decode("shift_jis")
    except UnicodeDecodeError:
        # discard truncated sjis char
        return byteString[:-1].decode("shift_jis")


class Header:
    VMD_SIGN = b'Vocaloid Motion Data 0002'

    def __init__(self):
        self.signature = None
        self.model_name = ''

    def load(self, fin):
        self.signature, = struct.unpack('<30s', fin.read(30))
        if self.signature[:len(self.VMD_SIGN)] != self.VMD_SIGN:
            raise InvalidFileError('File signature "%s" is invalid.'%self.signature)
        self.model_name = _to_shift_jis_string(struct.unpack('<20s', fin.read(20))[0])

    def save(self, fin):
        fin.write(struct.pack('<30s', self.VMD_SIGN))
        fin.write(struct.pack('<20s', self.model_name.encode('shift_jis')))

    def __repr__(self):
        return '<Header model_name %s>'%(self.model_name)


class BoneFrameKey:
    def __init__(self):
        self.frame_number = 0
        self.location = []
        self.rotation = []
        self.interp = []

    def load(self, fin):
        self.frame_number, = struct.unpack('<L', fin.read(4))
        self.location = list(struct.unpack('<fff', fin.read(4*3)))
        self.rotation = list(struct.unpack('<ffff', fin.read(4*4)))
        self.interp = list(struct.unpack('<64b', fin.read(64)))

    def save(self, fin):
        fin.write(struct.pack('<L', self.frame_number))
        fin.write(struct.pack('<fff', *self.location))
        fin.write(struct.pack('<ffff', *self.rotation))
        fin.write(struct.pack('<64b', *self.interp))

    def __repr__(self):
        return '<BoneFrameKey frame %s, loa %s, rot %s>'%(
            str(self.frame_number),
            str(self.location),
            str(self.rotation),
        )


class _AnimationBase(collections.defaultdict):
    def __init__(self):
        collections.defaultdict.__init__(self, list)

    @staticmethod
    def frameClass():
        raise NotImplementedError

    def load(self, fin):
        count, = struct.unpack('<L', fin.read(4))
        for i in range(count):
            name = translate_from_jp(_to_shift_jis_string(struct.unpack('<15s', fin.read(15))[0]))
            cls = self.frameClass()
            frameKey = cls()
            frameKey.load(fin)
            self[name].append(frameKey)

    def save(self, fin):
        count = sum([len(i) for i in self.values()])
        fin.write(struct.pack('<L', count))
        for name, frameKeys in self.items():
            name_data = struct.pack('<15s', name.encode('shift_jis'))
            for frameKey in frameKeys:
                fin.write(name_data)
                frameKey.save(fin)


class _AnimationListBase(list):
    def __init__(self):
        list.__init__(self)

    @staticmethod
    def frameClass():
        raise NotImplementedError

    def load(self, fin):
        count, = struct.unpack('<L', fin.read(4))
        for i in range(count):
            cls = self.frameClass()
            frameKey = cls()
            frameKey.load(fin)
            self.append(frameKey)

    def save(self, fin):
        fin.write(struct.pack('<L', len(self)))
        for frameKey in self:
            frameKey.save(fin)


class BoneAnimation(_AnimationBase):
    def __init__(self):
        _AnimationBase.__init__(self)

    @staticmethod
    def frameClass():
        return BoneFrameKey


class File:
    def __init__(self):
        self.filepath = None
        self.header = None
        self.boneAnimation = None

    def load(self, **args):
        path = args['filepath']

        with open(path, 'rb') as fin:
            self.filepath = path
            self.header = Header()
            self.boneAnimation = BoneAnimation()
            self.header.load(fin)
            self.boneAnimation.load(fin)

    def save(self, **args):
        path = args.get('filepath', self.filepath)

        header = self.header or Header()
        boneAnimation = self.boneAnimation or BoneAnimation()

        with open(path, 'wb') as fin:
            header.save(fin)
            boneAnimation.save(fin)


class VamSceneFile:

    def __init__(self, base):
        self.base = base
        with open(base, 'r') as g:
            self.vam_json = json.load(g)

    def get_person_index(self):
        aList = self.vam_json['atoms']
        i = 0
        for item in aList:
            if item['id'] == ATOM_NAME:
                return i
            i = i + 1

    def insert_core_control(self, longest_timestep):
        aList = self.vam_json['atoms']
        i = 0
        for item in aList:
            if item['id'] == 'CoreControl':
                break
            else: i = i + 1
        j = 0
        for item in self.vam_json['atoms'][i]['storables']:
            if item['id'] == 'MotionAnimationMaster':
                break
            else: j = j + 1
        self.vam_json['atoms'][i]['storables'][j]['recordedLength'] = str(longest_timestep)
        self.vam_json['atoms'][i]['storables'][j]['startTimestep'] = '0'
        self.vam_json['atoms'][i]['storables'][j]['stopTimestep'] = str(longest_timestep)

    def insert_in_vam(self, steps, boneName):
        self.vam_json['atoms'][self.get_person_index()]['storables'].append({
            'id' : boneName + 'Animation',
            'steps' : steps
        })

    def get_current_pos_rot(self, boneName):
        aList = self.vam_json['atoms'][self.get_person_index()]['storables']
        for item in aList:
            if item['id'] == boneName:
                return item['position'], item['rotation']

    def get_current_pos_rot_from_control(self, boneName):
        a_list = self.vam_json['atoms'][self.get_person_index()]['storables']
        for item in a_list:
            if item['id'] == boneName + 'Control':
                return item['position'], item['rotation']

    def dump(self, out):
        with open(out, 'w') as g:
            json.dump(self.vam_json, g, indent=3)
        print('Wrote ' + out)


class Body:

    def __init__(self, motion_data):
        self.md = motion_data
        self.body = None
        self.uses_ik = None

    # Map a bone to it's "dependency", which is the body part that it's attached to.
    # E.g. hand -> elbow -> arm -> shoulder, etc.
    DEPS = {
        'abdomen2': 'hip',
        'pelvis': 'hip',
        'rShoulder': 'abdomen2',
        'rArm': 'rShoulder',
        'rElbow': 'rArm',
        'rHand': 'rElbow',
        'lShoulder': 'abdomen2',
        'lArm': 'lShoulder',
        'lElbow': 'lArm',
        'lHand': 'lElbow',
        'neck': 'abdomen2',
        'head': 'neck',
        'lThigh': 'pelvis',
        'rThigh': 'pelvis',
        'lKnee': 'lThigh',
        'rKnee': 'rThigh',
    }

    def get_body(self):
        if self.body:
            return self.body
        # Order matters. From center of body going outwards.
        body = ['Center', # Center
                'UpperBody', 'Neck', 'Head', # Upper body
                'LowerBody', 'LeftLeg', 'RightLeg', 'RightKnee', 'LeftKnee', # Lower body
                'RightShoulder', 'LeftShoulder', 'LeftArm','RightArm', # Arms center
                'LeftElbow', 'RightElbow', 'RightWrist', 'LeftWrist'] # Arms out

        # Some MMD files use IK bones, some don't. Use IK only if animation data is found.
        self.uses_ik = len(self.md.boneAnimation['LeftLegIK']) > 1 or len(self.md.boneAnimation['RightLegIK']) > 1
        if self.uses_ik:
            body.extend(['LeftLegIK', 'RightLegIK'])
        else:
            body.extend(['LeftAnkle', 'RightAnkle'])
            Body.DEPS['rFoot'] = 'rKnee'
            Body.DEPS['lFoot'] = 'lKnee'
        self.body = body
        return self.body

    def get_uses_ik(self):
        if not self.body:
            self.get_body()
        return self.uses_ik


class BoneStateCalculator:

    def __init__(self, motion_data):
        self.md = motion_data

    def calculate(self, body):
        bone_state = {}
        for bone in body:

            if bone in MMD_TO_VAM_BONE_MAPPINGS.keys():
                bone_name = MMD_TO_VAM_BONE_MAPPINGS[bone]
                frames = self.md.boneAnimation[bone]
                bone_state[bone_name] = {}
                last_frame = -1

                bone_dep = None
                if bone_name in Body.DEPS.keys():
                    bone_dep = Body.DEPS[bone_name]
                    # Sometimes a dep wont have any info, so take the dep of the dep.
                    # E.g. Foot depends on knee, but knee has no motion info so use thigh as the dep.
                    while bone_dep not in bone_state.keys() or len(bone_state[bone_dep].keys()) <= 1:
                        if bone_dep == 'hip':
                            break
                        bone_dep = Body.DEPS[bone_dep]
                frames.sort(key=lambda g: g.frame_number)

                print('Calculating motion for: ' + bone_name)
                for boneFrameKey in frames:
                    if last_frame == -1:
                        # This is the first frame
                        bone_state[bone_name][0] = {}
                        bone_state[bone_name][0]['pos'] = {
                            'x':  boneFrameKey.location[0],
                            'y': boneFrameKey.location[1],
                            'z': boneFrameKey.location[2]
                        }
                        # If all the rotation data is 0 (null rotation) then set the rotation to off for this bone
                        # at frame 0.
                        if boneFrameKey.rotation[0] == 0 and boneFrameKey.rotation[1] == 0\
                                and boneFrameKey.rotation[2] == 0:
                            bone_state[bone_name][0]['rot_on'] = False
                        # Get the initial rotation
                        q = Quaternion(boneFrameKey.rotation[3],
                                       boneFrameKey.rotation[0],
                                       boneFrameKey.rotation[1],
                                       boneFrameKey.rotation[2])

                        # If bone has a parent then add the first frame rotation with the parent.
                        if bone_dep:
                            q = bone_state[bone_dep][0]['rot'] * q
                        bone_state[bone_name][0]['rot'] = q

                    else:
                        # Try to calculate the positions and rotations between frames via interpolation.
                        for current_frame in range(last_frame + 1, boneFrameKey.frame_number + 1):
                            bone_state[bone_name][current_frame] = {}
                            diff = boneFrameKey.frame_number - last_frame

                            # Use simple math to calculate where the intermediate points would be.
                            factor = float(1/ diff)
                            bone_state[bone_name][current_frame]['pos'] = {
                                'x': bone_state[bone_name][last_frame]['pos']['x'] *
                                     (diff - (current_frame - last_frame))/diff +
                                     (boneFrameKey.location[0]* (current_frame - last_frame)/diff),
                                'y': bone_state[bone_name][last_frame]['pos']['y'] *
                                     (diff - (current_frame - last_frame))/diff +
                                     (boneFrameKey.location[1]* (current_frame - last_frame)/diff),
                                'z': bone_state[bone_name][last_frame]['pos']['z'] *
                                     (diff - (current_frame - last_frame))/diff +
                                     (boneFrameKey.location[2]* (current_frame - last_frame)/diff),
                            }

                            # This is the tricky part. The calculation for a rotation goes as follows:
                            # 1. Find the rotation of the parent bone at this frame. Should be a quaternion.
                            # 2. If not found, go to the previous frame until one is found.
                            # 3. If the parent is not found at all just start with a null rotation for the dep.
                            # 4. If it's not null then turn on rotation, put the rotation it in a new quaternion.
                            # 5. Calculate the absolute rotation of the next frame by adding the parent and the
                            #    child's rot.
                            # 6. Get the absolute rotation that was already stored previously.
                            # 7. Use the slerp function to interpolate the current rotation based on both previous and
                            #    next rotations.
                            # 8. Save the calculated rotation, and proceed to the next frame.
                            rot_next_frame_parent = None

                            if bone_name in Body.DEPS.keys():
                                fr = boneFrameKey.frame_number
                                while not rot_next_frame_parent:
                                    try:
                                        # 1
                                        rot_next_frame_parent = bone_state[bone_dep][fr]['rot']
                                    except KeyError:  # 2
                                        fr = fr - 1
                            if not rot_next_frame_parent:
                                rot_next_frame_parent = Quaternion(1,0, 0, 0)  # 3

                            bone_state[bone_name][current_frame]['rot_on'] = True
                            # 4
                            rot_next_frame_child_relative = Quaternion(boneFrameKey.rotation[3],
                                                                       boneFrameKey.rotation[0],
                                                                       boneFrameKey.rotation[1],
                                                                       boneFrameKey.rotation[2])
                            # 5
                            rot_next_frame = rot_next_frame_parent * rot_next_frame_child_relative
                            rot_prev_frame = bone_state[bone_name][last_frame]['rot']  # 6
                            # 7
                            rot_current_frame = \
                                Quaternion.slerp(rot_prev_frame, rot_next_frame, (current_frame - last_frame) * factor)
                            bone_state[bone_name][current_frame]['rot'] = rot_current_frame  # 8
                    last_frame = boneFrameKey.frame_number
            else:
                print('Unknown body part: ' + bone)
        return bone_state


class VamAnimator:

    def __init__(self, vam_scene):
        self.vam_scene =  vam_scene

    def process(self, bone_state, uses_ik):
        longest_timestep = 1
        for bone in bone_state.keys():
            print('Converting to VAM format: ' + bone)
            steps = []
            frame_nums = sorted(bone_state[bone].keys())

            for i in frame_nums:
                animation = {}

                # 30 seconds per frame
                ts = float(i / VAM_FPS) + TIME_PAD_SECONDS

                if ts > longest_timestep:
                    longest_timestep = ts

                animation['timeStep'] = str(ts)

                # Turn on positions for relevant bones, turn off for all others
                if bone == 'hip':
                    animation['positionOn'] = 'true'
                elif uses_ik and (bone == 'lFoot' or bone == 'rFoot'):
                    animation['positionOn'] = 'true'
                else:
                    animation['positionOn'] = 'false'

                # Turn on rotation for center or for any other bone where rotation information is found
                # Turn off for all others
                if bone == 'hip' or ('rot_on' in bone_state[bone][i].keys() and bone_state[bone][i]['rot_on']):
                    animation['rotationOn'] = 'true'
                else:
                    animation['rotationOn'] = 'false'

                # POSITIONS

                # Set all initial positions according to the MMD file, multiply times factor to adjust.
                animation['position'] = {
                    'x' : str(bone_state[bone][i]['pos']['x'] * -POSITION_FACTOR),
                    'y' : str(bone_state[bone][i]['pos']['y'] * POSITION_FACTOR),
                    'z' : str(bone_state[bone][i]['pos']['z'] * -POSITION_FACTOR),
                }

                # Get what position the bone is currently in VAM's base file
                try:
                    position, rotation = self.vam_scene.get_current_pos_rot_from_control(bone)
                except TypeError:
                    try:
                        position, rotation = self.vam_scene.get_current_pos_rot(bone)
                    except:
                        pass
                if len(steps) == 0:
                    animation['timeStep'] = str(0)
                    animation['position']['x'] = str(float(position['x']))
                    animation['position']['y'] = str(float(position['y']))
                    animation['position']['z'] = str(float(position['z']))
                    steps.append(animation)

                # Add the two positions together (VAM and MMD) to get final position
                animation['position']['x'] = str(float(animation['position']['x']) + float(position['x']))
                animation['position']['y'] = str(float(animation['position']['y']) + float(position['y']))
                animation['position']['z'] = str(float(animation['position']['z']) + float(position['z']))

                # ROTATIONS

                # Get rotations for frame previously calculated
                res_q = bone_state[bone][i]['rot']

                # Left and right arms are initially rotated by a few degrees in MMD, compensate for that
                if bone == 'rArm' or bone == 'rElbow' or bone == 'rHand':
                    res_q = res_q * Quaternion(angle=MMD_ARM_ROTATION, axis=[0,0,1])
                if bone == 'lArm' or bone == 'lElbow' or bone == 'lHand':
                    res_q = res_q * Quaternion(angle=-MMD_ARM_ROTATION, axis=[0,0,1])

                if HEELS and (bone == 'rFoot' or bone == 'lFoot'):
                    res_q = res_q * Quaternion(angle=-MMD_HEEL_ROTATION, axis=[1,0,0])

                # Add height offset to the center bone.
                if bone == 'hip':
                    animation['position']['y'] = str(float(animation['position']['y']) + MMD_CENTER_HEIGHT_OFFSET)

                # Add Z offset to the center bone.
                if bone == 'hip':
                    animation['position']['z'] = str(float(animation['position']['z']) + MMD_CENTER_Z_OFFSET)

                # Assign all the rotations, x and z are flipped for all bones so multiply times -1
                animation['rotation'] = {}
                animation['rotation']['x'] = str(res_q.elements[1]*-1)
                animation['rotation']['y'] = str(res_q.elements[2])
                animation['rotation']['z'] = str(res_q.elements[3]*-1)
                animation['rotation']['w'] = str(res_q.elements[0])

                # Except in arms and feet, so flip sign again
                if bone == 'rArm' or bone == 'lArm' or bone == 'rElbow' \
                        or bone == 'lElbow' or bone == 'rHand' or bone == 'lHand' or bone == 'lFoot' or bone == 'rFoot':
                    animation['rotation']['z'] = str(res_q.elements[3] * -1)
                    animation['rotation']['x'] = str(res_q.elements[1] * -1)

                steps.append(animation)

            # Once a bone is done and there are no more motions, turn it off as other bones may have more data.
            if bone != 'hip' and bone != 'lFoot' and bone != 'rFoot' and len(frame_nums) > 0:
                animation = {}
                animation['timeStep'] =  str(float(frame_nums[len(frame_nums)- 1] + 1/30.0))
                animation['positionOn'] = 'false'
                animation['rotationOn'] = 'false'
                steps.append(animation)
            self.vam_scene.insert_in_vam(steps, bone)
        self.vam_scene.insert_core_control(longest_timestep)



def main():
    motion_data = File()
    print('Loading motion file...')
    motion_data.load(filepath=MMD_MOTION_FILE)
    vam_body = Body(motion_data)
    bone_state_calculator = BoneStateCalculator(motion_data)
    bone_state = bone_state_calculator.calculate(vam_body.get_body())
    vam_scene = VamSceneFile(VAM_SCENE_BASE)
    vam_animator = VamAnimator(vam_scene)
    vam_animator.process(bone_state, vam_body.get_uses_ik())
    print('Writing to disk...')
    vam_scene.dump(VAM_OUT_SCENE)


if __name__ == '__main__':
    main()
