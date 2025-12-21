#!/usr/bin/env python
"""
02_资源信息.py - 生成资源数据

包含：
- 文档数据 (Document)
- 活动数据 (Activity)
- 文章数据 (Category, Article)
"""

import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Django 环境设置
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from django.core.files import File
from django.utils import timezone
from apps.content.models import Document, Activity, Category, Article, ContentAttachment
from apps.users.models import User

# 媒体资源目录
MEDIA_DIR = Path(__file__).parent / "media"
FILE_DIR = MEDIA_DIR / "file"
IMAGE_DIR = MEDIA_DIR / "image"
VIDEO_DIR = MEDIA_DIR / "video"


def clear_data():
    """清除现有数据"""
    print("清除现有内容数据...")
    Article.objects.all().delete()
    Category.objects.all().delete()
    Activity.objects.all().delete()
    Document.objects.all().delete()
    ContentAttachment.objects.all().delete()
    print("内容数据清除完成")


def create_documents():
    """创建文档数据"""
    print("\n创建文档数据...")
    
    files = list(FILE_DIR.glob("*"))
    documents = []
    
    doc_names = [
        "人民调解法全文",
        "民法典婚姻家庭编解读",
        "矛盾纠纷调解工作指南",
        "基层治理工作手册",
        "调解员培训教材",
        "法律援助申请流程",
        "社区矛盾化解案例汇编",
        "农村土地纠纷处理指南",
        "劳动争议调解实务",
        "信访工作条例解读",
    ]
    
    for i, file_path in enumerate(files):
        name = doc_names[i] if i < len(doc_names) else f"文档资料{i+1}"
        
        with open(file_path, 'rb') as f:
            doc = Document.objects.create(
                name=name,
                file=File(f, name=file_path.name),
            )
            documents.append(doc)
            print(f"  创建文档: {doc.name}")
    
    return documents


def create_activities():
    """创建活动数据"""
    print("\n创建活动数据...")
    
    activities_data = [
        {"name": "2024年度人民调解员业务培训会", "content": "<p>为进一步提升人民调解员的业务素质和调解能力，加强调解员队伍建设，特举办本次培训活动。培训内容包括人民调解法律法规学习、矛盾纠纷调解技巧与方法、典型案例分析与研讨、实战演练与经验交流等。请各位调解员准时参加，携带学习笔记本，认真听讲做好记录。</p>"},
        {"name": "法治宣传进社区活动", "content": "<p>弘扬法治精神，共建和谐社区。活动内容包括法律知识咨询服务、法治宣传资料发放、典型案例展示、互动问答抽奖等。通过法治宣传活动，提高群众的法律意识，营造学法、用法、守法的良好氛围。</p>"},
        {"name": "矛盾纠纷排查化解专项行动", "content": "<p>深入开展矛盾纠纷排查化解工作，及时发现和化解各类矛盾纠纷，维护社会和谐稳定。重点排查领域包括邻里纠纷、家庭矛盾、土地权属争议、劳动争议、经济合同纠纷等。各网格调解员要深入辖区，主动排查，做到早发现、早介入、早化解。</p>"},
        {"name": "调解员技能竞赛", "content": "<p>以赛促学、以赛促练，检验调解员业务水平，激励调解员不断提升专业能力。竞赛内容包括法律知识笔试、模拟调解实操、案例分析答辩等。设一等奖1名、二等奖2名、三等奖3名，颁发荣誉证书和奖品。</p>"},
        {"name": "基层治理经验交流座谈会", "content": "<p>分享基层治理成功经验，探讨提升治理效能的方法路径。交流内容包括网格化管理经验分享、矛盾纠纷化解典型做法、群众工作方法创新、信息化手段应用等。参会人员为各网格负责人、优秀调解员代表。</p>"},
    ]
    
    files = list(FILE_DIR.glob("*"))
    activities = []
    now = timezone.now()
    
    for i, data in enumerate(activities_data):
        if i < 2:
            start_time = now - timedelta(days=30 + i * 15)
            reg_start = start_time - timedelta(days=14)
            reg_end = start_time - timedelta(days=1)
        elif i < 4:
            start_time = now + timedelta(days=7 + i * 5)
            reg_start = now - timedelta(days=7)
            reg_end = now + timedelta(days=3)
        else:
            start_time = now + timedelta(days=30 + i * 10)
            reg_start = now + timedelta(days=7)
            reg_end = start_time - timedelta(days=3)
        
        activity = Activity.objects.create(
            name=data["name"],
            start_time=start_time,
            registration_start=reg_start,
            registration_end=reg_end,
            content=data["content"],
        )
        
        if files:
            selected_files = random.sample(files, min(2, len(files)))
            for file_path in selected_files:
                with open(file_path, 'rb') as f:
                    attachment = ContentAttachment.objects.create(
                        file=File(f, name=file_path.name),
                    )
                    activity.files.add(attachment)
        
        if i < 4:
            mediators = list(User.objects.filter(role=User.Role.MEDIATOR))
            if mediators:
                participants = random.sample(mediators, min(random.randint(5, 15), len(mediators)))
                activity.participants.set(participants)
        
        activities.append(activity)
        print(f"  创建活动: {activity.name}")
    
    return activities


def create_categories():
    """创建文章分类"""
    print("\n创建文章分类...")
    
    categories_data = [
        {"name": "政策法规", "sort_order": 1},
        {"name": "工作动态", "sort_order": 2},
        {"name": "典型案例", "sort_order": 3},
        {"name": "调解知识", "sort_order": 4},
    ]
    
    categories = []
    for data in categories_data:
        category = Category.objects.create(**data)
        categories.append(category)
        print(f"  创建分类: {category.name}")
    
    return categories


# 文章内容生成器
def get_article_content(category_name, index):
    """根据分类生成文章内容（500字以上）"""
    
    contents = {
        "政策法规": [
            """<h2>引言</h2><p>《中华人民共和国人民调解法》是规范人民调解工作的基本法律，于2010年8月28日通过，自2011年1月1日起施行。该法的出台，标志着我国人民调解工作进入了法治化、规范化的新阶段。</p><h2>第一章 总则</h2><p>本章规定了人民调解的定义、原则和地位。人民调解是指人民调解委员会通过说服、疏导等方法，促使当事人在平等协商基础上自愿达成调解协议，解决民间纠纷的活动。人民调解工作应当遵循自愿平等、合法合理、尊重当事人权利的原则。国家支持和保障人民调解工作的开展。</p><h2>第二章 人民调解委员会</h2><p>人民调解委员会是依法设立的调解民间纠纷的群众性组织。村民委员会、居民委员会设立人民调解委员会。企业事业单位根据需要设立人民调解委员会。人民调解委员会由委员三至九人组成，设主任一人，必要时可以设副主任若干人。人民调解委员会委员每届任期三年，可以连选连任。</p><h2>第三章 人民调解员</h2><p>人民调解员由人民调解委员会委员和人民调解委员会聘任的人员担任。人民调解员应当由公道正派、热心人民调解工作，并具有一定文化水平、政策水平和法律知识的成年公民担任。县级人民政府司法行政部门应当定期对人民调解员进行业务培训。</p>""",
            """<h2>概述</h2><p>《中华人民共和国民法典》婚姻家庭编是民法典的重要组成部分，共5章79条，对婚姻家庭关系的建立、维护和解除作出了全面规定。本文将对其中的重点条文进行解析。</p><h2>一、结婚制度</h2><p>民法典规定，结婚应当男女双方完全自愿，禁止任何一方对另一方加以强迫，禁止任何组织或者个人加以干涉。结婚年龄，男不得早于二十二周岁，女不得早于二十周岁。这些规定体现了婚姻自由原则和保护未成年人权益的立法精神。</p><h2>二、夫妻关系</h2><p>民法典规定夫妻在家庭中地位平等，夫妻双方都有参加生产、工作、学习和社会活动的自由，一方不得对另一方加以限制或者干涉。夫妻有相互扶养的义务，夫妻对共同财产有平等的处理权。这些规定保障了夫妻双方的合法权益。</p><h2>三、离婚制度</h2><p>民法典完善了离婚制度，增设了离婚冷静期制度。自婚姻登记机关收到离婚登记申请之日起三十日内，任何一方不愿意离婚的，可以向婚姻登记机关撤回离婚登记申请。这一制度旨在减少冲动离婚，维护家庭稳定。</p>""",
        ],
        "工作动态": [
            """<h2>会议召开</h2><p>2024年12月15日，市司法局召开全市人民调解工作总结会议。市司法局党组书记、局长出席会议并讲话，各区县司法局分管领导、调解科负责人，各乡镇司法所所长参加会议。</p><h2>工作回顾</h2><p>会议全面总结了2024年度全市人民调解工作取得的成绩。一年来，全市各级人民调解组织共受理各类矛盾纠纷12560件，调解成功12180件，调解成功率达97%。涉及金额3.2亿元，防止民转刑案件18起，防止群体性事件26起，有效维护了社会和谐稳定。</p><h2>经验交流</h2><p>会上，多个区县司法局和基层调解组织代表进行了经验交流。东城区介绍了枫桥经验本地化实践做法，西城区分享了行业性专业性调解组织建设经验，南城街道交流了调解加普法工作模式。</p><h2>工作部署</h2><p>会议对2025年工作进行了安排部署。要求各地要深入学习贯彻习近平法治思想，坚持和发展新时代枫桥经验，加强调解组织规范化建设，提高调解员队伍素质，推进调解信息化建设。</p>""",
            """<h2>活动概况</h2><p>12月4日是国家宪法日，为深入学习宣传贯彻习近平法治思想，大力弘扬宪法精神，我区在城北社区广场举办了法治宣传进社区主题活动。区司法局、区普法办、各街道司法所及律师志愿者等50余人参加活动，吸引了近500名社区居民前来咨询了解。</p><h2>活动内容</h2><p>活动现场设置了法律咨询台、法治宣传展板、有奖问答区等多个功能区域。法律咨询台前，律师和法律工作者热情解答群众关于婚姻家庭、劳动争议、邻里纠纷等方面的法律问题。</p><h2>资料发放</h2><p>活动期间，共发放宪法、民法典、人民调解法等法律法规宣传资料3000余份，发放普法宣传袋、普法扇子等普法用品500余份。这些宣传资料通俗易懂，贴近群众生活，受到了社区居民的欢迎。</p><h2>活动意义</h2><p>本次法治宣传进社区活动，是我区深入开展法治宣传教育、推进法治社区建设的重要举措。通过活动，进一步增强了群众的法治观念和法律意识。</p>""",
        ],
        "典型案例": [
            """<h2>案情简介</h2><p>2024年3月，王某与邻居李某因宅基地边界问题发生纠纷。王某认为李某新建房屋占用了其宅基地，要求李某拆除占用部分。李某则认为自己的房屋是在合法范围内建设，双方争执不下，甚至发生过肢体冲突。</p><h2>调解过程</h2><p>村人民调解委员会接到调解申请后，调解员立即进行了现场勘查，并调取了双方的宅基地使用证等相关资料。通过测量发现，李某新建房屋确实越界约30厘米。调解员分别与双方进行沟通，了解各自诉求和底线。</p><h2>调解方案</h2><p>调解员在充分了解情况后，提出了调解方案：李某将越界部分的围墙向内退让30厘米，并对王某因纠纷造成的损失给予适当补偿。调解员向双方详细解释了相关法律规定，分析了各自的利弊得失，最终双方接受了调解方案。</p><h2>案例启示</h2><p>邻里之间应当互谅互让，和睦相处。在宅基地使用过程中，应当严格按照批准的范围使用，不得擅自扩大或变更用途。发生纠纷后，应当通过合法途径解决，不得采取过激行为。</p>""",
            """<h2>案情简介</h2><p>2024年5月，张某与妻子刘某因家庭琐事经常发生争吵，矛盾逐渐升级。刘某提出离婚，但双方在财产分割和子女抚养问题上分歧较大，多次协商未果。刘某的娘家人也介入纠纷，使问题更加复杂。</p><h2>调解过程</h2><p>社区人民调解委员会介入后，调解员首先分别与张某、刘某进行了深入交谈，了解双方矛盾的根源和真实想法。调解员发现，双方其实感情基础较好，只是因为沟通不畅、生活压力大等原因产生了隔阂。</p><h2>调解策略</h2><p>调解员采取了冷却法和疏导法相结合的调解策略。一方面，建议双方分开冷静一段时间；另一方面，对双方进行心理疏导，帮助他们认识到婚姻中存在的问题和各自的不足。同时，调解员还做通了刘某娘家人的工作。</p><h2>调解结果</h2><p>经过多次调解，张某和刘某认识到了各自的问题，表示愿意给对方一个机会。双方达成协议，约定今后要加强沟通，互相体谅，共同努力维护家庭和睦。这起婚姻家庭纠纷得到了圆满解决。</p>""",
        ],
        "调解知识": [
            """<h2>引言</h2><p>调解技巧是调解员做好调解工作的重要保障。掌握科学的调解方法和技巧，能够提高调解效率，提升调解成功率。本文将介绍几种常用的调解技巧。</p><h2>一、倾听技巧</h2><p>倾听是调解的基础。调解员要认真、耐心地听取当事人的陈述，不要轻易打断。通过倾听，可以了解纠纷的来龙去脉，把握矛盾的焦点，为调解奠定基础。倾听时要注意观察当事人的表情、语气，捕捉其真实意图。</p><h2>二、沟通技巧</h2><p>良好的沟通是调解成功的关键。调解员要用平和的语气、通俗的语言与当事人交流，避免使用专业术语或官话。要善于运用提问技巧，引导当事人理性思考。同时要注意非语言沟通，保持眼神交流，给人以亲切感。</p><h2>三、说服技巧</h2><p>说服是调解的核心环节。调解员要善于运用法律法规、政策规定、道德规范、村规民约等进行说服教育。说服时要有针对性，抓住当事人的心理特点和利益关切，以理服人、以情感人、以法育人。</p><h2>四、协调技巧</h2><p>调解过程中，调解员要善于协调各方关系，寻找利益平衡点。对于双方分歧较大的问题，可以采取分解法，将大问题分解为若干小问题逐一解决。也可以采取换位思考法，引导当事人站在对方的角度考虑问题。</p>""",
            """<h2>概述</h2><p>调解文书是调解活动的重要载体，规范的调解文书是调解工作规范化的重要体现。本文将介绍调解文书的主要类型和制作要求。</p><h2>一、调解申请书</h2><p>调解申请书是当事人向人民调解委员会申请调解时提交的书面材料。主要内容包括：申请人的基本情况、被申请人的基本情况、申请调解的事项和理由、申请人签名和日期等。调解申请书应当表述清楚、内容完整。</p><h2>二、调解受理登记表</h2><p>调解受理登记表是人民调解委员会受理调解申请时填写的登记材料。主要内容包括：受理编号、受理日期、当事人信息、纠纷类型、纠纷简要情况、指派调解员等。登记表填写要规范、准确。</p><h2>三、调解协议书</h2><p>调解协议书是当事人达成调解协议后制作的法律文书。主要内容包括：当事人的基本情况、纠纷的主要事实和争议事项、双方达成协议的内容、履行方式和期限、当事人签名、调解员签名、人民调解委员会印章等。调解协议书是调解工作最重要的文书，制作要严谨规范。</p><h2>四、调解回访记录</h2><p>调解回访记录是调解协议履行后进行回访时填写的记录材料。主要内容包括：回访日期、回访对象、协议履行情况、当事人满意度、存在的问题等。做好回访记录，有助于跟踪调解效果。</p>""",
        ],
    }
    
    # 补充更多内容
    extra_contents = {
        "政策法规": """<h2>基层人民调解工作规范</h2><p>为进一步规范基层人民调解工作，提高调解质量和效率，根据人民调解法等法律法规，制定本工作规范。本规范适用于各级人民调解委员会及其人民调解员开展调解工作。</p><h2>调解受理</h2><p>人民调解委员会受理调解申请应当符合以下条件：属于民间纠纷；当事人自愿申请调解；符合人民调解委员会的受案范围。对不属于人民调解范围的纠纷，应当告知当事人通过其他合法途径解决。</p><h2>调解实施</h2><p>调解应当在专门的调解场所进行，保持场所整洁、安静、庄重。调解员应当耐心听取当事人陈述，引导当事人理性表达诉求。要善于运用法律法规、道德规范、村规民约等进行说服教育，促使当事人互谅互让，达成和解。</p><h2>档案管理</h2><p>人民调解委员会应当建立健全调解档案管理制度。调解档案应当包括：调解申请书、调解记录、调解协议书、回访记录等材料。档案应当分类归档，妥善保管，保管期限不少于三年。</p>""",
        "工作动态": """<h2>培训概况</h2><p>为提高人民调解员的业务素质和工作能力，11月25日至29日，区司法局在区委党校举办了2024年度人民调解员培训班。来自全区12个乡镇的86名调解员参加了培训。经过5天的集中学习，培训班圆满结业。</p><h2>培训内容</h2><p>本次培训邀请了市司法局领导、高校法学教授、资深律师等专家授课，内容涵盖人民调解法律法规、调解技巧与方法、典型案例分析、法律知识专题讲座等多个方面。培训注重理论与实践相结合。</p><h2>模拟演练</h2><p>在模拟调解演练环节，学员们分组进行了邻里纠纷、婚姻家庭纠纷、经济合同纠纷等案例的模拟调解。指导老师对每组的调解过程进行了点评，指出了存在的问题，提出了改进建议。</p><h2>学员感言</h2><p>参训学员纷纷表示，这次培训内容丰富、形式新颖、收获满满。通过培训，系统学习了法律知识和调解技巧，对今后更好地开展调解工作信心更足了。</p>""",
        "典型案例": """<h2>案情简介</h2><p>2024年7月，某建筑公司拖欠农民工工资引发群体性纠纷。该公司承建的某住宅小区项目因资金链断裂，拖欠30余名农民工工资共计56万余元。农民工多次讨薪未果，情绪激动，准备采取过激行为。</p><h2>调解介入</h2><p>街道人民调解委员会得知情况后，立即启动应急调解机制。调解员一方面安抚农民工情绪，引导其理性维权；另一方面联系建筑公司负责人，了解公司经营状况和支付能力。同时，调解员还协调了人社、住建等部门参与调解。</p><h2>调解方案</h2><p>经过多轮调解，最终达成分期支付方案：建筑公司先支付50%的欠薪，剩余50%在三个月内分两期支付完毕。同时，调解员协助农民工申请了法律援助，对调解协议进行了司法确认。</p><h2>案例启示</h2><p>对于涉及人数多、金额大的群体性纠纷，人民调解委员会要及时介入，充分发挥协调各方的优势。要善于整合各方资源，形成调解合力。对于调解协议，可以引导当事人申请司法确认，增强其法律效力。</p>""",
        "调解知识": """<h2>引言</h2><p>调解心理学是研究调解活动中当事人心理活动规律及其应用的学科。掌握调解心理学知识，有助于调解员更好地了解当事人心理，提高调解效果。</p><h2>一、当事人心理特点</h2><p>纠纷发生后，当事人往往处于应激状态，表现出焦虑、愤怒、委屈等情绪。有的当事人可能存在防御心理，对调解员缺乏信任；有的当事人可能存在从众心理，容易受他人影响；有的当事人可能存在面子心理，不愿在他人面前让步。</p><h2>二、心理疏导方法</h2><p>对于情绪激动的当事人，调解员要运用心理疏导方法，帮助其恢复理性。可以采用倾听法，让当事人充分表达；可以采用共情法，表示对当事人的理解；可以采用转移法，转移当事人的注意力。</p><h2>三、心理影响技术</h2><p>调解员可以运用一些心理影响技术，促进调解成功。如权威影响，借助法律法规的权威性；社会证明，举出类似纠纷的调解案例；互惠原则，引导当事人相互让步等。</p>""",
    }
    
    # 获取基础内容列表
    base_contents = contents.get(category_name, [])
    if index < len(base_contents):
        return base_contents[index]
    else:
        return extra_contents.get(category_name, base_contents[0] if base_contents else "")


def create_articles(categories):
    """创建文章数据"""
    print("\n创建文章数据...")
    
    # 获取媒体资源
    images = list(IMAGE_DIR.glob("*"))
    files = list(FILE_DIR.glob("*"))
    videos = list(VIDEO_DIR.glob("*"))
    
    # 获取发布者
    admins = list(User.objects.filter(role=User.Role.ADMIN))
    
    # 文章标题
    titles = {
        "政策法规": [
            "《中华人民共和国人民调解法》全文解读",
            "《民法典》婚姻家庭编重点条文解析",
            "基层人民调解工作规范解读",
            "劳动争议调解仲裁法要点梳理",
            "土地管理法修订要点及调解实务指南",
            "信访工作条例实施细则解读",
            "社区矫正法律制度简介",
            "物业管理条例与业主权益保护",
            "消费者权益保护法重点解析",
            "未成年人保护法修订亮点解读",
        ],
        "工作动态": [
            "市司法局召开2024年度人民调解工作总结会议",
            "我区开展矛盾纠纷排查化解专项行动",
            "法治宣传进社区活动圆满举办",
            "调解员业务培训班顺利结业",
            "全区调解工作推进会召开",
            "人民调解工作经验交流会成功举办",
            "优秀调解员表彰大会隆重举行",
            "调解工作信息化建设取得新进展",
            "行业性专业性调解组织建设推进会召开",
            "新任调解员岗前培训圆满完成",
        ],
        "典型案例": [
            "邻里宅基地纠纷调解案例",
            "婚姻家庭矛盾调解案例",
            "农民工工资纠纷群体调解案例",
            "物业管理纠纷调解案例",
            "消费者权益纠纷调解案例",
            "农村土地承包纠纷调解案例",
            "医疗纠纷调解案例",
            "交通事故赔偿纠纷调解案例",
            "劳动合同纠纷调解案例",
            "继承纠纷调解案例",
        ],
        "调解知识": [
            "人民调解员必备的调解技巧",
            "调解文书的制作规范与要求",
            "调解心理学知识及应用",
            "如何做好调解前的准备工作",
            "调解中的沟通艺术",
            "特殊群体纠纷调解注意事项",
            "调解协议的效力与执行",
            "调解与诉讼的衔接机制",
            "网格化调解工作方法",
            "调解员职业道德规范",
        ],
    }
    
    articles = []
    now = timezone.now()
    
    for category in categories:
        category_titles = titles.get(category.name, [])
        for i, title in enumerate(category_titles):
            # 随机发布时间
            published_at = now - timedelta(days=random.randint(1, 180))
            
            article = Article.objects.create(
                title=title,
                category=category,
                content=get_article_content(category.name, i),
                status=Article.Status.PUBLISHED,
                sort_order=i,
                publisher=random.choice(admins) if admins else None,
                published_at=published_at,
            )
            
            # 添加封面图片
            if images:
                img_path = random.choice(images)
                with open(img_path, 'rb') as f:
                    article.cover_image.save(img_path.name, File(f), save=True)
            
            # 部分文章添加视频
            if videos and random.random() > 0.7:
                video_path = random.choice(videos)
                with open(video_path, 'rb') as f:
                    article.video.save(video_path.name, File(f), save=True)
            
            # 添加附件
            if files and random.random() > 0.5:
                selected_files = random.sample(files, min(random.randint(1, 2), len(files)))
                for file_path in selected_files:
                    with open(file_path, 'rb') as f:
                        attachment = ContentAttachment.objects.create(
                            file=File(f, name=file_path.name),
                        )
                        article.files.add(attachment)
            
            articles.append(article)
            print(f"  创建文章: [{category.name}] {article.title}")
    
    return articles


def main():
    """主函数"""
    print("=" * 60)
    print("开始生成资源数据...")
    print("=" * 60)
    
    # 清除数据
    clear_data()
    
    # 创建数据
    create_documents()
    create_activities()
    categories = create_categories()
    create_articles(categories)
    
    print("\n" + "=" * 60)
    print("资源数据生成完成!")
    print("=" * 60)
    print(f"\n统计:")
    print(f"  - 文档: {Document.objects.count()} 条")
    print(f"  - 活动: {Activity.objects.count()} 条")
    print(f"  - 分类: {Category.objects.count()} 条")
    print(f"  - 文章: {Article.objects.count()} 条")


if __name__ == "__main__":
    main()
