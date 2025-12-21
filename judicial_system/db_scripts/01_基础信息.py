#!/usr/bin/env python
"""
01_基础信息.py - 生成基础数据

包含：
- 网格数据 (Grid)
- 地图配置 (MapConfig)
- 用户数据 (User)
- 培训记录 (TrainingRecord)
- 绩效数据 (PerformanceScore)
"""

import os
import sys
import random
import shutil
from datetime import date, timedelta
from pathlib import Path
from decimal import Decimal

# Django 环境设置
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from django.core.files import File
from apps.grids.models import Grid
from apps.common.models import MapConfig
from apps.users.models import User, TrainingRecord, PerformanceScore, UserAttachment
from apps.cases.models import Task

# 媒体资源目录
MEDIA_DIR = Path(__file__).parent / "media"
FILE_DIR = MEDIA_DIR / "file"


def clear_data():
    """清除现有数据"""
    print("清除现有数据...")
    # 先删除关联 User 的 Task 数据（reporter 是 PROTECT）
    Task.objects.all().delete()
    PerformanceScore.objects.all().delete()
    TrainingRecord.objects.all().delete()
    UserAttachment.objects.all().delete()
    User.objects.all().delete()
    Grid.objects.all().delete()
    MapConfig.objects.all().delete()
    print("数据清除完成")


def create_grids():
    """创建网格数据"""
    print("\n创建网格数据...")
    
    grids_data = [
        {
            "name": "烈士陵园巡逻网格",
            "boundary": [[107.8986007, 32.5369684], [107.8970772, 32.5362131], [107.8982037, 32.5349468], [107.9003227, 32.5357066]],
            "region": "城东区",
            "description": "负责烈士陵园及周边区域的治安巡逻与矛盾调解工作",
        },
        {
            "name": "体育馆治安管理网格",
            "boundary": [[107.895956, 32.538013], [107.8951246, 32.5377191], [107.896015, 32.5365704], [107.8970665, 32.537095]],
            "region": "城中区",
            "description": "负责体育馆及周边区域的治安管理与纪律维护工作",
        },
        {
            "name": "广场网格",
            "boundary": [[107.8903717, 32.5401883], [107.8895509, 32.5396592], [107.8904575, 32.5390848], [107.8911817, 32.539225], [107.8911495, 32.5401566]],
            "region": "城西区",
            "description": "负责广场及周边区域的公共秩序维护与群众矛盾调解工作",
        },
    ]
    
    grids = []
    for data in grids_data:
        # 计算中心点
        boundary = data["boundary"]
        center_lng = sum(p[0] for p in boundary) / len(boundary)
        center_lat = sum(p[1] for p in boundary) / len(boundary)
        
        grid = Grid.objects.create(
            name=data["name"],
            boundary=data["boundary"],
            region=data["region"],
            description=data["description"],
            center_lng=Decimal(str(round(center_lng, 7))),
            center_lat=Decimal(str(round(center_lat, 7))),
            is_active=True,
        )
        grids.append(grid)
        print(f"  创建网格: {grid.name}")
    
    return grids


def create_map_config():
    """创建地图配置"""
    print("\n创建地图配置...")
    
    config = MapConfig.objects.create(
        center_longitude=Decimal("107.8911325"),
        center_latitude=Decimal("32.5384616"),
        api_key="4H4BZ-OJACL-DKBPM-E7Y5H-5VSK5-KFFKK",
        zoom_level=14,
        is_active=True,
    )
    print(f"  创建地图配置: 中心点({config.center_longitude}, {config.center_latitude})")
    return config


def create_users(grids):
    """创建用户数据"""
    print("\n创建用户数据...")
    
    users = []
    
    # 1. 管理员用户
    admin_data = [
        {"username": "admin", "name": "系统管理员", "gender": "male"},
        {"username": "gqt", "name": "郭启童", "gender": "male"},
        {"username": "cc", "name": "程超", "gender": "male"},
    ]
    
    for data in admin_data:
        user = User.objects.create_user(
            username=data["username"],
            password="123456",
            name=data["name"],
            gender=data["gender"],
            role=User.Role.ADMIN,
            phone=f"138{random.randint(10000000, 99999999)}",
        )
        users.append(user)
        print(f"  创建管理员: {user.name} ({user.username})")
    
    # 2. 网格负责人
    grid_managers = []
    for i in range(1, 4):
        user = User.objects.create_user(
            username=f"grid_manager{i}",
            password="123456",
            name=f"网格负责人{i}",
            gender=random.choice(["male", "female"]),
            role=User.Role.GRID_MANAGER,
            phone=f"139{random.randint(10000000, 99999999)}",
            grid=grids[i-1],
        )
        # 设置网格的当前负责人
        grids[i-1].current_manager = user
        grids[i-1].save()
        
        grid_managers.append(user)
        users.append(user)
        print(f"  创建网格负责人: {user.name} ({user.username}) - {grids[i-1].name}")
    
    # 3. 调解员
    mediators = []
    first_names = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗", "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧"]
    last_names = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "秀兰", "霞", "平", "刚", "桂英", "英", "华", "慧", "建华", "建国", "建军", "建平"]
    
    for i in range(1, 31):
        name = random.choice(first_names) + random.choice(last_names)
        user = User.objects.create_user(
            username=f"user{i}",
            password="123456",
            name=name,
            gender=random.choice(["male", "female"]),
            role=User.Role.MEDIATOR,
            phone=f"137{random.randint(10000000, 99999999)}",
            grid=random.choice(grids),
        )
        mediators.append(user)
        users.append(user)
        print(f"  创建调解员: {user.name} ({user.username}) - {user.grid.name}")
    
    return users, grid_managers, mediators


def create_training_records(users, mediators):
    """创建培训记录"""
    print("\n创建培训记录...")
    
    training_names = [
        "人民调解法律法规培训",
        "矛盾纠纷调解技巧培训",
        "社区治理能力提升培训",
        "群众工作方法培训",
        "法律知识专题培训",
        "调解员职业道德培训",
        "心理疏导技能培训",
        "基层治理实务培训",
        "民事纠纷处理培训",
        "农村土地纠纷调解培训",
        "劳动争议调解培训",
        "家庭矛盾调解技巧培训",
        "邻里纠纷处理培训",
        "信访问题处置培训",
        "应急事件处理培训",
    ]
    
    training_contents = [
        "学习《人民调解法》《民法典》等法律法规，掌握调解工作的法律依据和程序要求。",
        "掌握矛盾纠纷的识别、分析和化解技巧，提高调解成功率。",
        "提升社区治理能力，学习如何有效组织群众参与社区建设。",
        "学习群众工作的基本方法和技巧，提高与群众沟通的能力。",
        "系统学习民法、刑法、行政法等基本法律知识。",
        "培养调解员的职业道德和责任意识，树立正确的价值观。",
        "学习心理疏导的基本方法，帮助当事人缓解情绪。",
        "学习基层治理的理论和实践，提高处理实际问题的能力。",
        "系统学习民事纠纷的类型、特点及处理方法。",
        "针对农村土地承包、流转等纠纷的专业调解培训。",
        "学习劳动法相关知识，掌握劳动争议调解技巧。",
        "学习家庭矛盾的心理疏导和调解方法。",
        "掌握邻里纠纷的常见类型和处理技巧。",
        "学习信访问题的接待和处置方法。",
        "学习突发事件的应急处理和协调方法。",
    ]
    
    # 获取可用的文件资源
    files = list(FILE_DIR.glob("*"))
    
    records = []
    target_users = mediators[:15] + users[:5]  # 选取部分用户
    
    for i in range(20):
        user = random.choice(target_users)
        training_idx = i % len(training_names)
        
        # 随机生成培训时间（过去一年内）
        training_date = date.today() - timedelta(days=random.randint(1, 365))
        
        record = TrainingRecord.objects.create(
            user=user,
            name=training_names[training_idx],
            content=training_contents[training_idx],
            training_time=training_date,
        )
        
        # 添加培训附件（随机选择1-2个文件）
        if files:
            selected_files = random.sample(files, min(random.randint(1, 2), len(files)))
            for file_path in selected_files:
                with open(file_path, 'rb') as f:
                    attachment = UserAttachment.objects.create(
                        user=user,
                        file=File(f, name=file_path.name),
                    )
                    record.files.add(attachment)
        
        records.append(record)
        print(f"  创建培训记录: {record.name} - {user.name}")
    
    return records


def create_performance_scores(mediators, grid_managers):
    """创建绩效数据"""
    print("\n创建绩效数据...")
    
    comments = [
        "工作认真负责，调解成功率高，群众满意度好。",
        "态度积极，善于沟通，能有效化解矛盾纠纷。",
        "专业能力强，处理问题及时准确，值得表扬。",
        "工作努力，但还需加强法律知识学习。",
        "调解技巧有所提升，继续努力。",
        "本月表现优秀，多次成功调解复杂纠纷。",
        "工作稳定，能按时完成各项任务。",
        "与群众沟通良好，获得多方好评。",
        "需要进一步提高调解效率。",
        "本月工作量较大，完成情况良好。",
    ]
    
    scores = []
    # 生成过去几个月的绩效数据
    periods = []
    today = date.today()
    for i in range(6):
        period_date = today - timedelta(days=30 * i)
        periods.append(f"{period_date.year}-{period_date.month:02d}")
    
    # 为每个调解员生成绩效记录
    used_combinations = set()
    count = 0
    
    while count < 20:
        mediator = random.choice(mediators)
        period = random.choice(periods)
        
        # 避免重复（同一调解员同一周期只能有一条记录）
        key = (mediator.id, period)
        if key in used_combinations:
            continue
        used_combinations.add(key)
        
        scorer = random.choice(grid_managers)
        
        score = PerformanceScore.objects.create(
            mediator=mediator,
            scorer=scorer,
            score=random.randint(60, 100),
            period=period,
            comment=random.choice(comments),
        )
        scores.append(score)
        count += 1
        print(f"  创建绩效记录: {mediator.name} - {period} - {score.score}分")
    
    return scores


def main():
    """主函数"""
    print("=" * 60)
    print("开始生成基础数据...")
    print("=" * 60)
    
    # 清除数据
    clear_data()
    
    # 创建数据
    grids = create_grids()
    create_map_config()
    users, grid_managers, mediators = create_users(grids)
    create_training_records(users, mediators)
    create_performance_scores(mediators, grid_managers)
    
    print("\n" + "=" * 60)
    print("基础数据生成完成!")
    print("=" * 60)
    print(f"\n统计:")
    print(f"  - 网格: {Grid.objects.count()} 条")
    print(f"  - 地图配置: {MapConfig.objects.count()} 条")
    print(f"  - 用户: {User.objects.count()} 条")
    print(f"  - 培训记录: {TrainingRecord.objects.count()} 条")
    print(f"  - 绩效记录: {PerformanceScore.objects.count()} 条")


if __name__ == "__main__":
    main()
