"""
Settings package.

结构说明:
- base.py: 基础配置 (所有环境共享)
- development.py: 开发环境配置 (继承 base)
- production.py: 生产环境配置 (继承 base, 从环境变量读取敏感信息)

使用方式:
- 开发环境: DJANGO_SETTINGS_MODULE=config.settings.development
- 生产环境: DJANGO_SETTINGS_MODULE=config.settings.production
"""

