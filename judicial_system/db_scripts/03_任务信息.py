#!/usr/bin/env python
"""
03_任务信息.py - 生成任务数据

包含：
- 附件数据 (Attachment)
- 任务数据 (Task)
"""

import os
import sys
import random
from datetime import timedelta
from pathlib import Path
from decimal import Decimal

# Django 环境设置
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from django.core.files import File
from django.utils import timezone
from apps.common.models import Attachment
from apps.cases.models import Task
from apps.users.models import User
from apps.grids.models import Grid

# 媒体资源目录
MEDIA_DIR = Path(__file__).parent / "media"
FILE_DIR = MEDIA_DIR / "file"
IMAGE_DIR = MEDIA_DIR / "image"

# 中心点坐标
CENTER_LNG = 107.8911325
CENTER_LAT = 32.5384616


def clear_data():
    """清除现有数据"""
    print("清除现有任务和附件数据...")
    Task.objects.all().delete()
    Attachment.objects.all().delete()
    print("数据清除完成")


def create_attachments():
    """创建附件数据"""
    print("\n创建附件数据...")
    attachments = {"image": [], "document": []}
    
    for img_path in IMAGE_DIR.glob("*"):
        with open(img_path, 'rb') as f:
            attachment = Attachment.objects.create(
                file=File(f, name=img_path.name),
                file_type=Attachment.FileType.IMAGE,
                file_size=img_path.stat().st_size,
                original_name=img_path.name,
            )
            attachments["image"].append(attachment)
            print(f"  创建图片附件: {attachment.original_name}")
    
    for file_path in FILE_DIR.glob("*"):
        with open(file_path, 'rb') as f:
            attachment = Attachment.objects.create(
                file=File(f, name=file_path.name),
                file_type=Attachment.FileType.DOCUMENT,
                file_size=file_path.stat().st_size,
                original_name=file_path.name,
            )
            attachments["document"].append(attachment)
            print(f"  创建文档附件: {attachment.original_name}")
    
    return attachments


def random_coords():
    """生成随机坐标（在中心点附近）"""
    lng = CENTER_LNG + random.uniform(-0.01, 0.01)
    lat = CENTER_LAT + random.uniform(-0.01, 0.01)
    return Decimal(str(round(lng, 7))), Decimal(str(round(lat, 7)))


# ========== 内容生成函数 ==========
# 导入同目录下的内容模块
sys.path.insert(0, str(Path(__file__).parent))
from db_scripts_content import (
    get_dispute_descriptions,
    get_legal_aid_descriptions,
    get_expected_plans,
    get_process_descriptions,
    get_result_details,
    get_addresses,
    get_participant_names,
)


def create_tasks(attachments):
    """创建任务数据"""
    print("\n创建任务数据...")
    
    users = list(User.objects.all())
    mediators = list(User.objects.filter(role=User.Role.MEDIATOR))
    grid_managers = list(User.objects.filter(role=User.Role.GRID_MANAGER))
    grids = list(Grid.objects.all())
    
    if not users or not mediators or not grids:
        print("  错误：缺少必要的用户或网格数据，请先运行 01_基础信息.py")
        return []
    
    dispute_descriptions = get_dispute_descriptions()
    legal_aid_descriptions = get_legal_aid_descriptions()
    expected_plans = get_expected_plans()
    process_descriptions = get_process_descriptions()
    result_details = get_result_details()
    addresses = get_addresses()
    participant_names = get_participant_names()
    
    image_ids = [str(a.id) for a in attachments["image"]]
    doc_ids = [str(a.id) for a in attachments["document"]]
    
    tasks = []
    statuses = [Task.Status.REPORTED, Task.Status.ASSIGNED, Task.Status.PROCESSING, Task.Status.COMPLETED]
    now = timezone.now()
    
    for status_idx, status in enumerate(statuses):
        for i in range(10):
            task_num = status_idx * 10 + i + 1
            task_type = Task.Type.DISPUTE if task_num % 2 == 1 else Task.Type.LEGAL_AID
            
            description = dispute_descriptions[i % len(dispute_descriptions)] if task_type == Task.Type.DISPUTE else legal_aid_descriptions[i % len(legal_aid_descriptions)]
            report_lng, report_lat = random_coords()
            reporter = random.choice(mediators + grid_managers)
            grid = random.choice(grids)
            
            task_data = {
                "code": f"TASK-2024{task_num:04d}",
                "type": task_type,
                "status": status,
                "description": description,
                "amount": Decimal(str(random.randint(1000, 100000))) if random.random() > 0.3 else None,
                "grid": grid,
                "party_name": f"当事人{task_num}号",
                "party_phone": f"13{random.randint(100000000, 999999999)}",
                "party_address": random.choice(addresses),
                "reporter": reporter,
                "reported_at": now - timedelta(days=random.randint(1, 90)),
                "report_lng": report_lng,
                "report_lat": report_lat,
                "report_address": random.choice(addresses),
            }
            
            if image_ids:
                task_data["report_image_ids"] = ",".join(random.sample(image_ids, min(random.randint(1, 3), len(image_ids))))
            if doc_ids and random.random() > 0.5:
                task_data["report_file_ids"] = ",".join(random.sample(doc_ids, min(random.randint(1, 2), len(doc_ids))))
            
            if status in [Task.Status.ASSIGNED, Task.Status.PROCESSING, Task.Status.COMPLETED]:
                task_data["assigner"] = random.choice(grid_managers)
                task_data["assigned_mediator"] = random.choice(mediators)
                task_data["assigned_at"] = task_data["reported_at"] + timedelta(hours=random.randint(1, 48))
            
            if status in [Task.Status.PROCESSING, Task.Status.COMPLETED]:
                task_data["process_submitted_at"] = task_data["assigned_at"] + timedelta(hours=random.randint(1, 24))
                task_data["participants"] = random.choice(participant_names)
                task_data["handle_method"] = random.choice([Task.HandleMethod.ONSITE, Task.HandleMethod.ONLINE])
                task_data["expected_plan"] = expected_plans[i % len(expected_plans)]
            
            if status == Task.Status.COMPLETED:
                complete_lng, complete_lat = random_coords()
                task_data["result"] = random.choice([Task.Result.SUCCESS, Task.Result.FAILURE, Task.Result.PARTIAL])
                task_data["result_detail"] = result_details[i % len(result_details)]
                task_data["process_description"] = process_descriptions[i % len(process_descriptions)]
                task_data["completed_at"] = task_data["process_submitted_at"] + timedelta(days=random.randint(1, 14))
                task_data["complete_lng"] = complete_lng
                task_data["complete_lat"] = complete_lat
                task_data["complete_address"] = random.choice(addresses)
                if image_ids:
                    task_data["complete_image_ids"] = ",".join(random.sample(image_ids, min(random.randint(1, 3), len(image_ids))))
                if doc_ids and random.random() > 0.5:
                    task_data["complete_file_ids"] = ",".join(random.sample(doc_ids, min(random.randint(1, 2), len(doc_ids))))
            
            task = Task.objects.create(**task_data)
            tasks.append(task)
            print(f"  创建任务: {task.code} [{task.get_status_display()}] - {task.get_type_display()}")
    
    return tasks


def main():
    """主函数"""
    print("=" * 60)
    print("开始生成任务数据...")
    print("=" * 60)
    
    clear_data()
    attachments = create_attachments()
    create_tasks(attachments)
    
    print("\n" + "=" * 60)
    print("任务数据生成完成!")
    print("=" * 60)
    print(f"\n统计:")
    print(f"  - 附件: {Attachment.objects.count()} 条")
    print(f"  - 任务: {Task.objects.count()} 条")
    for s in [Task.Status.REPORTED, Task.Status.ASSIGNED, Task.Status.PROCESSING, Task.Status.COMPLETED]:
        print(f"    - {Task.Status(s).label}: {Task.objects.filter(status=s).count()} 条")


if __name__ == "__main__":
    main()
